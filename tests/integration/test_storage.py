import csv
from datetime import datetime
import pytest
from openpyxl import Workbook
from app.services.database_service import Database
from app.integration.repository import Repository
from app.integration.loader import TabularLoader
from app.security.policy import AccessDenied
from app.core.exceptions import DataValidationError
from app.api.schemas import RequestContext

MAPPING={'store':'store_id','sku':'sku_id','date':'observed_on','stock':'closing_stock','reorder':'reorder_point','lead':'lead_days'}

@pytest.fixture
def repository(tmp_path):
    db=Database('sqlite+pysqlite:///'+str(tmp_path/'import.db'))
    repo=Repository(db)
    yield repo
    db.close()

def make_csv(path,rows):
    with path.open('w',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(MAPPING);writer.writerows(rows)

def admin():return RequestContext(session_id='s',principal_id='a',role='ADMIN')

def test_atomic_mapping_import_persistence_and_idempotency(repository,tmp_path):
    path=tmp_path/'observed.csv'
    make_csv(path,[['S1','SKU1','2026-09-22',3,5,2]])
    report=TabularLoader(repository,'inventory',fixture=True).load(path,MAPPING)
    assert report.rows_loaded==1
    persisted=Repository(repository.database).records('inventory',admin())
    assert persisted[0]['fixture'] and persisted[0]['source']=='observed.csv'
    with pytest.raises(DataValidationError):TabularLoader(repository,'inventory').load(path,MAPPING)
    assert len(repository.records('inventory',admin()))==1

@pytest.mark.parametrize('badrow',[
    ['S1','SKU2','bad-date',3,5,2],['S1','SKU2','2026-09-22',-3,5,2],
    ['','SKU2','2026-09-22',3,5,2],['S1','SKU2','2026-09-22','=2+2',5,2]])
def test_invalid_batch_rolls_back(repository,tmp_path,badrow):
    path=tmp_path/'bad.csv'
    make_csv(path,[['S1','SKU1','2026-09-22',3,5,2],badrow])
    with pytest.raises(DataValidationError):TabularLoader(repository,'inventory').load(path,MAPPING)
    assert repository.records('inventory',admin())==[]


def test_duplicate_headers_and_duplicate_rows(repository,tmp_path):
    path=tmp_path/'duplicate.csv';path.write_text('store,store\nS1,S1\n')
    with pytest.raises(DataValidationError):TabularLoader(repository,'inventory').load(path,MAPPING)
    row=['S1','SKU1','2026-09-22',3,5,2]
    make_csv(path,[row,row])
    with pytest.raises(DataValidationError):TabularLoader(repository,'inventory').load(path,MAPPING)
    assert repository.records('inventory',admin())==[]


def test_xlsx_typed_dates_and_formula_rejection(repository,tmp_path):
    path=tmp_path/'data.xlsx'
    workbook=Workbook();sheet=workbook.active
    sheet.append(list(MAPPING));sheet.append(['S1','SKU1',datetime(2026,9,22),3,5,2]);workbook.save(path)
    assert TabularLoader(repository,'inventory').load(path,MAPPING).rows_loaded==1
    sheet['B2']='SKU2';sheet['D2']='=3+3';workbook.save(path)
    with pytest.raises(DataValidationError):TabularLoader(repository,'inventory').load(path,MAPPING)


def test_authorization_precedes_any_database_session(repository,monkeypatch):
    def forbidden():raise AssertionError('Database must not be opened')
    monkeypatch.setattr(repository.database,'session',forbidden)
    with pytest.raises(AccessDenied):repository.records('inventory',RequestContext(session_id='s',principal_id='p',role='ANALYST',store_ids=['S1']),'S1')
