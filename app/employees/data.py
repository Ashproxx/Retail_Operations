import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from sqlalchemy import JSON, String, ForeignKey, insert
from sqlalchemy.orm import Mapped, mapped_column
from app.models.database import Base
from app.services.database_service import Database
from app.enterprise.data import ImportBatch
from app.enterprise.imports import sheets, report_for, save_stores, identifier, day, number, integer

COLUMNS='employee_id full_name gender date_of_birth age education languages store_id store_location city zone department designation grade employment_type confirmation_status hire_date tenure_years reports_to_id reports_to_name shift weekly_off weekly_hours monthly_gross_salary_inr avg_monthly_incentive_inr pf_applicable esic_applicable performance_rating attendance_pct_last_90d employment_status last_working_date'.split()
STAFFING_COLUMNS='store_id city store_location zone store_format delivery_tier store_area_sqft demand_index headcount active_headcount n_store_manager n_assistant_store_manager n_sales_associate n_cashier n_stock_executive n_visual_merchandiser n_alteration_tailor n_delivery_executive n_online_order_executive n_security_guard n_housekeeping_staff permanent contract part_time female_staff_pct avg_tenure_years avg_gross_salary_inr monthly_payroll_inr staff_per_1000_sqft'.split()


def name_key(value):
    text=''.join(c for c in unicodedata.normalize('NFKD',str(value or '')).casefold() if not unicodedata.combining(c))
    return ' '.join(re.findall(r'\w+',text))


class Employee(Base):
    __tablename__='employees'
    employee_id: Mapped[str]=mapped_column(String(128),primary_key=True)
    store_id: Mapped[str]=mapped_column(ForeignKey('stores.id'),index=True)
    search_name: Mapped[str]=mapped_column(String(256),index=True)
    payload: Mapped[dict]=mapped_column(JSON)


class Staffing(Base):
    __tablename__='store_staffing'
    store_id: Mapped[str]=mapped_column(ForeignKey('stores.id'),primary_key=True)
    payload: Mapped[dict]=mapped_column(JSON)


def import_employees(database,path):
    Base.metadata.create_all(database.engine)
    digest='employees:'+hashlib.sha256(Path(path).read_bytes()).hexdigest()
    with database.session() as s:
        previous=s.get(ImportBatch,digest)
        if previous:return {**previous.report,'already_imported':True}
    data=sheets(path,{'Employee_Master':COLUMNS,'Store_Staffing':STAFFING_COLUMNS})
    report=report_for(path,'employees',data,{'Employee_Master':150,'Store_Staffing':20})
    staffing=data['Store_Staffing'];stores={identifier(r['store_id']) for r in staffing}
    if len(stores)!=len(staffing):raise ValueError('Duplicate staffing store')
    ids={identifier(r['employee_id']) for r in data['Employee_Master']}
    if len(ids)!=len(data['Employee_Master']):raise ValueError('Duplicate employee ID')
    employees=[]
    for raw in data['Employee_Master']:
        r=dict(raw)
        if r['store_id'] not in stores:raise ValueError('Employee store is unknown')
        if not isinstance(r['full_name'],str) or not 1<=len(r['full_name'])<=256 or not name_key(r['full_name']):raise ValueError('Employee name is required')
        for k in ['department','designation','employment_type','employment_status']:
            if not isinstance(r[k],str) or not r[k].strip():raise ValueError('Employment field is missing')
        for k in ['date_of_birth','hire_date','last_working_date']:
            if r[k] is not None:r[k]=day(r[k])
        for k in ['age','weekly_hours','monthly_gross_salary_inr','avg_monthly_incentive_inr','tenure_years']:
            if r[k] is not None:r[k]=float(number(r[k],minimum=0))
        if r['performance_rating'] is not None:r['performance_rating']=float(number(r['performance_rating'],minimum=1,maximum=5))
        if r['attendance_pct_last_90d'] is not None:r['attendance_pct_last_90d']=float(number(r['attendance_pct_last_90d'],minimum=0,maximum=100))
        if r['reports_to_id'] is not None and r['reports_to_id'] not in ids:raise ValueError('Unknown reporting manager ID')
        if r['last_working_date'] and r['hire_date'] and r['last_working_date']<r['hire_date']:raise ValueError('Last working date precedes hire')
        employees.append(dict(employee_id=r['employee_id'],store_id=r['store_id'],search_name=name_key(r['full_name']),payload=r))
    for r in staffing:
        actual=[e['payload'] for e in employees if e['store_id']==r['store_id']]
        if integer(r['headcount'])!=len(actual):raise ValueError('Staffing headcount disagrees with employee records')
        if integer(r['active_headcount'])!=sum(e['employment_status']=='Active' for e in actual):raise ValueError('Active headcount mismatch')
        for k in ['monthly_payroll_inr','avg_gross_salary_inr','store_area_sqft','avg_tenure_years','staff_per_1000_sqft']:r[k]=float(number(r[k],minimum=0))
    with database.session() as session:
        save_stores(session,staffing)
        session.flush()
        session.execute(insert(Employee),employees)
        session.execute(insert(Staffing),[dict(store_id=r['store_id'],payload=r) for r in staffing])
        session.add(ImportBatch(id=digest,domain='employees',report=report))
    return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--file',type=Path,required=True);p.add_argument('--database',required=True);args=p.parse_args()
    db=Database(args.database)
    try:print(json.dumps(import_employees(db,args.file),indent=2))
    finally:db.close()


if __name__=='__main__':main()
