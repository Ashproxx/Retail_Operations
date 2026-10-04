"""Reconcile the imported local database against both supplied source workbooks."""
import argparse
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from sqlalchemy import select,func
from app.api.schemas import RequestContext
from app.enterprise.imports import sheets,SALES_COLUMNS,COMPETITOR_COLUMNS,STORE_COLUMNS,paise
from app.enterprise.data import Sale,CompetitorSale
from app.employees.data import Employee,Staffing,COLUMNS,STAFFING_COLUMNS
from app.enterprise.retail import RetailService
from app.employees.service import EmployeeService
from app.enterprise.contracts import WorkspaceTurn
from app.integration.repository import Repository
from app.services.database_service import Database
from app.security.audit import AuditChain


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sales',type=Path,required=True);p.add_argument('--employees',type=Path,required=True)
    p.add_argument('--database',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    sales=sheets(args.sales,{'Sales_Transactions':SALES_COLUMNS,'Competitor_Sales':COMPETITOR_COLUMNS,'Store_Master':STORE_COLUMNS})
    employees=sheets(args.employees,{'Employee_Master':COLUMNS,'Store_Staffing':STAFFING_COLUMNS})
    db=Database('sqlite:///'+args.database.resolve().as_posix())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    rt=SimpleNamespace(repository=Repository(db),audit=AuditChain(args.output.parent/'source-validation-audit.jsonl'))
    retail=RetailService(rt);hr=EmployeeService(rt)
    ctx=RequestContext(principal_id='source-validation',role='ADMIN',session_id='source-validation')
    def ask(service,message='',**kw):return service.run(WorkspaceTurn(session_id=ctx.session_id,message=message,**kw),ctx)
    try:
        facts=sales['Sales_Transactions'];people=employees['Employee_Master']
        source_net=sum(paise(r['net_amount_inr']) for r in facts)
        expected=defaultdict(int)
        for row in facts:expected[(row['store_id'],row['category'])]+=paise(row['net_amount_inr'])
        with db.session() as session:
            assert session.scalar(select(func.count()).select_from(Sale))==len(facts)
            assert session.scalar(select(func.count()).select_from(CompetitorSale))==len(sales['Competitor_Sales'])
            assert session.scalar(select(func.sum(Sale.net_paise)))==source_net
            assert session.scalar(select(func.count(func.distinct(Sale.order_id))))==len({r['order_id'] for r in facts})
            actual={(s,c):n for s,c,n in session.execute(select(Sale.store_id,Sale.category,func.sum(Sale.net_paise)).group_by(Sale.store_id,Sale.category))}
            # Source taxonomy is canonical apart from singular/plural aliases, normalized by importer.
            from app.conversation.taxonomy import classify
            normalized=defaultdict(int)
            for (store,category),amount in expected.items():normalized[(store,classify(category)['normalized_category'] or category)]+=amount
            assert actual==normalized
            assert session.scalar(select(func.count()).select_from(Employee))==len(people)
            assert session.scalar(select(func.count()).select_from(Staffing))==len(employees['Store_Staffing'])
        result=ask(retail,'Show sales across all stores for available data')
        assert Decimal(result['metrics']['Net sales (INR)'])*100==source_net
        assert sum(Decimal(r['net_revenue_inr']) for r in result['table'])*100==source_net
        assert ask(retail,'Show sales on 2030-01-01')['status']=='no_data'
        assert ask(retail,action='latest')['status']=='success'
        assert ask(retail,'Show inventory')['status']=='unavailable'
        forecast=ask(retail,'Forecast next 7 days');assert forecast['status']=='success' and len(forecast['table'])==7
        competitors=ask(retail,'Compare competitors');assert competitors['status']=='success'
        delivery=ask(retail,'Which store has highest delivery delays?');assert delivery['status']=='success'
        missing=next(r for r in people if r['performance_rating'] is None)
        assert ask(hr,'Tell me about '+missing['full_name'])['status']=='success'
        assert 'No performance rating' in ask(hr,'What is her performance rating?')['summary']
        city=people[0]['city'];result=ask(hr,'Who works in '+city+'?')
        assert result['metrics']['Employees']==sum(r['city']==city for r in people)
        payroll=hr.overview(ctx)['metrics']['Recorded monthly gross payroll (INR)']
        assert Decimal(str(payroll))==sum(Decimal(str(r['monthly_gross_salary_inr'])) for r in people if r['monthly_gross_salary_inr'] is not None)
        report={'passed':True,'source':'Actual supplied synthetic workbooks, not generated acceptance fixtures','sales_lines':len(facts),'orders':len({r['order_id'] for r in facts}),'competitor_rows':len(sales['Competitor_Sales']),'employees':len(people),'staffing_rows':len(employees['Store_Staffing']),'net_revenue_inr':str(Decimal(source_net)/100),'store_category_totals_reconciled':len(actual),'checks':['row counts','source net amounts','all store/category totals','all-source chat total','future-date fallback','inventory unavailable','chronological forecast','weekly competitor estimates','distinct-order delivery','missing employee rating','city employee filtering','authorized source payroll']}
        args.output.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
    finally:db.close()


if __name__=='__main__':main()
