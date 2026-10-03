import pytest
from sqlalchemy import select,func
from app.employees import data
from app.services.database_service import Database


def small_employees():
    row={k:None for k in data.COLUMNS}
    row.update(employee_id='E1',full_name='Test Person',store_id='S1',city='Test City',department='Sales',designation='Associate',employment_type='Permanent',employment_status='Active',hire_date='2025-01-01',attendance_pct_last_90d=95,monthly_gross_salary_inr=20000)
    store=dict(store_id='S1',city='Test City',headcount=1,active_headcount=1,monthly_payroll_inr=20000,avg_gross_salary_inr=20000,store_area_sqft=1000,avg_tenure_years=1,staff_per_1000_sqft=1)
    return {'Employee_Master':[row],'Store_Staffing':[store]}


def test_nullable_rating_atomicity_and_name_key(tmp_path,monkeypatch):
    db=Database('sqlite:///'+str(tmp_path/'db'));path=tmp_path/'employees.xlsx';path.write_bytes(b'fixture')
    rows=small_employees();monkeypatch.setattr(data,'sheets',lambda *a:rows)
    result=data.import_employees(db,path)
    assert result['missing']['Employee_Master']['performance_rating']==1
    assert data.import_employees(db,path)['already_imported']
    path.write_bytes(b'changed');rows['Employee_Master'][0]['performance_rating']=6
    with pytest.raises(ValueError):data.import_employees(db,path)
    with db.session() as s:assert s.scalar(select(func.count()).select_from(data.Employee))==1
    assert data.name_key('  José D’Souza ')==data.name_key("Jose D'Souza")
    db.close()
