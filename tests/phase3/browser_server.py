"""Disposable, explicitly synthetic browser fixture, never a production data fallback."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from app.enterprise import imports
from app.employees import data
from app.services.database_service import Database
from tests.phase3.test_imports import small_sales
from tests.phase3.test_employee_data import small_employees
from app.enterprise.launch import main

if __name__=='__main__':
    with TemporaryDirectory(prefix='phase3-browser-') as directory:
        root=Path(directory);db=Database('sqlite:///'+(root/'db').as_posix())
        source=root/'sales.xlsx';source.write_bytes(b'explicit sales fixture')
        with patch.object(imports,'sheets',return_value=small_sales()):imports.import_sales(db,source)
        source.write_bytes(b'explicit employee fixture')
        with patch.object(data,'sheets',return_value=small_employees()):data.import_employees(db,source)
        db.close();sys.argv+=['--database',str(root/'db')];main()
