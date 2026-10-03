"""Name-based, descriptive HR information with separate scoped conversational memory."""
from collections import Counter
from difflib import SequenceMatcher
import re
from statistics import mean
from sqlalchemy import select
from app.api.schemas import Role
from app.security.policy import AccessDenied
from app.employees.data import Employee,Staffing,name_key
from app.employees.security import scope,profile,audit,FULL

DIMENSIONS=['city','department','designation','employment_type','employment_status','shift']
SECTIONS={'Profile':['full_name','age','gender','education','languages','date_of_birth'],
    'Employment':['department','designation','grade','employment_type','confirmation_status','hire_date','tenure_years','employment_status','last_working_date'],
    'Organization':['store_location','city','zone','reports_to_name'],
    'Work schedule':['shift','weekly_off','weekly_hours'],
    'Compensation':['monthly_gross_salary_inr','avg_monthly_incentive_inr'],
    'Benefits':['pf_applicable','esic_applicable'],
    'Attendance and performance':['attendance_pct_last_90d','performance_rating']}


def candidates(text,rows):
    query=name_key(text);padded=' '+query+' '
    exact=[r for r in rows if ' '+name_key(r['full_name'])+' ' in padded]
    if exact:return exact,False
    tokens=set(query.split())
    names={token for r in rows for token in name_key(r['full_name']).split()}
    wanted=tokens&names
    if wanted:
        found=[r for r in rows if wanted<=set(name_key(r['full_name']).split())]
        if found:return found,False
    cleaned=re.sub(r'\b(tell|me|about|show|employee|profile|please|find|search|for)\b',' ',query)
    cleaned=' '.join(cleaned.split())
    if len(cleaned)<3:return [],False
    scored=[(SequenceMatcher(None,cleaned,name_key(r['full_name'])).ratio(),r) for r in rows]
    best=max((score for score,_ in scored),default=0)
    return ([r for score,r in sorted(scored,key=lambda pair:-pair[0]) if score>=max(.74,best-.04)][:8],True)


def choice(row):
    return {'label':row['full_name'],'value':row['employee_id'],'description':' · '.join(str(row.get(k) or 'Not recorded') for k in ['designation','city','department'])}


class EmployeeService:
    def __init__(self,runtime):self.runtime=runtime;self.db=runtime.repository.database

    def rows(self,ctx,detail=False):
        with self.db.session() as s:return [r.payload for r in s.scalars(scope(select(Employee).order_by(Employee.search_name),Employee,ctx,detail=detail))]

    def options(self,ctx):
        rows=self.rows(ctx)
        return {'source':'POC Navi Mumbai Employee Dataset','synthetic':True,'can_view_profiles':ctx.role!=Role.ANALYST,
            'can_view_compensation':ctx.role in FULL,'dimensions':{k:sorted({r[k] for r in rows if r.get(k)}) for k in DIMENSIONS}}

    def search(self,text,ctx):
        found=[];status='denied'
        try:
            rows=self.rows(ctx,detail=True);found,fuzzy=candidates(text,rows)
            status='success'
            return {'choices':[choice(r) for r in found[:50]],'fuzzy':fuzzy,'synthetic':True}
        finally:audit(self.runtime,ctx,'employee.search',status,[r['employee_id'] for r in found[:50]],['full_name','designation','city','department'] if found else [])

    def overview(self,ctx,selected=None):
        selected=selected or {};rows=self.rows(ctx)
        rows=[r for r in rows if all(r.get(k)==v for k,v in selected.items() if k in DIMENSIONS)]
        stats={'Employees':len(rows),'Active employees':sum(r.get('employment_status')=='Active' for r in rows)}
        for field,label in [('attendance_pct_last_90d','Average attendance (%)'),('tenure_years','Average recorded tenure (years)')]:
            values=[r[field] for r in rows if r.get(field) is not None]
            stats[label]=round(mean(values),2) if values else None
        if ctx.role in FULL:
            salary=[r['monthly_gross_salary_inr'] for r in rows if r.get('monthly_gross_salary_inr') is not None]
            stats['Recorded monthly gross payroll (INR)']=sum(salary) if salary else None
            stats['Average gross salary (INR)']=round(mean(salary),2) if salary else None
        counts={k:dict(Counter(r.get(k) or 'Not recorded' for r in rows)) for k in ['department','employment_type','city','employment_status']}
        if ctx.role==Role.ANALYST and len(rows)<5:
            stats={'Privacy':'Fewer than five matching employees; detailed statistics are suppressed.'};counts={}
        with self.db.session() as s:staffing=[r.payload for r in s.scalars(scope(select(Staffing),Staffing,ctx))]
        stores={r['store_id'] for r in rows};staffing=[r for r in staffing if r['store_id'] in stores]
        public=[]
        for r in staffing:
            fields=['city','headcount','active_headcount','permanent','contract','part_time','avg_tenure_years','staff_per_1000_sqft']
            if ctx.role in FULL:fields+=['avg_gross_salary_inr','monthly_payroll_inr']
            public.append({k:r.get(k) for k in fields})
        return {'metrics':stats,'groups':counts,'staffing':public,'filters':selected,'synthetic':True,
            'findings':['Descriptive source-snapshot statistics. Store staffing covers the whole store; employee filters affect employee statistics only. No individual sales attribution or employment decision is made.']}

    def run(self,turn,ctx):
        response=None;subjects=[];fields=[]
        try:
            response,subjects,fields=self._run(turn,ctx)
            return {**response,'request_id':str(ctx.request_id),'source':'POC Navi Mumbai Employee Dataset','synthetic':True,'operational_write_performed':False}
        finally:audit(self.runtime,ctx,'employee.conversation',(response or {}).get('status','denied_or_error'),subjects,fields)

    def _run(self,turn,ctx):
        all_rows=self.rows(ctx);text=name_key(turn.message)
        owner=ctx.model_copy(update={'session_id':'phase3:employees:'+ctx.session_id})
        state=self.runtime.repository.memory(owner) or {}
        if turn.action=='reset':state={}
        def done(result,subjects=(),fields=()):
            self.runtime.repository.remember(owner,state)
            return result,list(subjects),list(fields)
        if re.search(r'\b(fire|fired|firing|dismiss|terminate|demote|promote|hire|hiring|discipline|punish)\b|who deserves|cut (?:pay|salary)',text):
            return done({'status':'human_review','summary':'Employee 360 provides recorded HR information. It does not recommend or execute hiring, firing, promotion, discipline or compensation decisions. An authorized human must handle those decisions.'})
        if re.search(r'\b(sales|revenue|inventory|competitor|delivery orders)\b',text):
            if re.search(r'\b(her|his|their|employee)\b',text):return done({'status':'unavailable','summary':'Sales transactions do not identify individual employees. Store-level sales cannot be attributed to a person.'})
            return done({'status':'route','summary':'That question belongs to Retail Operations. Open that workspace to continue.','workspace':'/retail'})
        if re.search(r'\b(policy|policies|handbook|rules)\b',text):return done({'status':'unavailable','summary':'HR policy documents have not been supplied. No leave, benefits or employment policy is inferred from employee records. The existing signed RAG service is retained for authorized documents.'})
        selected={}
        for dim in DIMENSIONS:
            values={r[dim] for r in all_rows if r.get(dim)}
            matches=[v for v in values if ' '+name_key(v)+' ' in ' '+text+' ' or dim=='shift' and name_key(v).split()[0] in text.split()]
            if matches:selected[dim]=max(matches,key=len)
        if turn.action=='overview' or not turn.message and turn.action in [None,'reset']:
            result=self.overview(ctx,selected)
            return done({'status':'success','summary':'Staffing overview for your authorized stores.',**result},fields=result['metrics'])
        private=re.search(r'\b(salary|payroll|compensation|incentive|birth|dob|benefits|pf|esic)\b',text)
        if private and ctx.role not in FULL:return done({'status':'denied','summary':'Your role cannot access individual compensation, birth details or benefits.'})
        if ctx.role==Role.ANALYST:
            if selected or re.search(r'\b(headcount|staffing|how many|average|statistics|mix)\b',text):
                result=self.overview(ctx,selected);return done({'status':'success','summary':'Anonymized staffing statistics for your authorized scope.',**result},fields=result['metrics'])
            return done({'status':'denied','summary':'Analysts can access aggregate HR statistics, not individual employee profiles or names.'})
        found,fuzzy=candidates(turn.message,all_rows)
        if turn.action=='select':
            found=[r for r in all_rows if r['employee_id']==turn.value];fuzzy=False
            if not found:raise AccessDenied('Employee is unavailable in authorized scope')
        if len(found)>1 or fuzzy and found:
            state.pop('employee_id',None)
            return done({'status':'needs_clarification','summary':'I found several matching records. Which employee do you mean?' if len(found)>1 else 'Did you mean this employee?',
                'choices':[choice(r) for r in found[:50]]},[r['employee_id'] for r in found[:50]],['full_name','designation','city','department'])
        if found:state['employee_id']=found[0]['employee_id']
        directory=not found and (bool(selected) or re.search(r'\b(employees|staffing|headcount|who works|how many|staff mix|highest payroll)\b',text))
        if directory:
            state.pop('employee_id',None)
            result=self.overview(ctx,selected)
            rows=[r for r in all_rows if all(r.get(k)==v for k,v in selected.items())]
            if 'highest payroll' in text and ctx.role in FULL:result['staffing'].sort(key=lambda r:-(r.get('monthly_payroll_inr') or 0))
            return done({'status':'success','summary':f'{len(rows)} employees match your authorized filters.',**result,'choices':[choice(r) for r in rows[:50]],'more_results':len(rows)>50},[r['employee_id'] for r in rows[:50]],list(result['metrics'])+['full_name','designation','city','department'])
        if not found and re.search(r'\b(tell me about|show me|find|search)\b',text) and not re.search(r'\b(her|his|their|this employee)\b',text):
            state.pop('employee_id',None)
        row=next((r for r in all_rows if r['employee_id']==state.get('employee_id')),None)
        if not row:
            state.pop('employee_id',None)
            return done({'status':'needs_clarification','summary':'Which employee? Enter a full or partial name; no employee ID is needed.'})
        public=profile(row,ctx)
        sections={title:{k:public[k] for k in keys if k in public} for title,keys in SECTIONS.items()}
        sections={k:v for k,v in sections.items() if v}
        summary=f"{public['full_name']} · {public['designation']} · {public['city']}. Recorded status: {public['employment_status']}."
        if 'attendance' in text:summary+=f" Recorded 90-day attendance: {public['attendance_pct_last_90d']}%." if public['attendance_pct_last_90d'] is not None else ' No attendance percentage is recorded.'
        if 'performance' in text or 'rating' in text:summary+=f" Recorded performance rating: {public['performance_rating']}." if public['performance_rating'] is not None else ' No performance rating is currently recorded for this employee.'
        if 'salary' in text and ctx.role in FULL:summary+=f" Recorded monthly gross salary: INR {public['monthly_gross_salary_inr']:,}." if public['monthly_gross_salary_inr'] is not None else ' No salary is recorded.'
        store_rows=[r for r in all_rows if r['store_id']==row['store_id']]
        attendance=[r['attendance_pct_last_90d'] for r in store_rows if r.get('attendance_pct_last_90d') is not None]
        return done({'status':'success','summary':summary,'profile':sections,'metrics':{'Store headcount':len(store_rows),'Store mean attendance (%)':round(mean(attendance),2) if attendance else None},
            'findings':['Fields describe the supplied HR snapshot, not live employment status. Blank values are not inferred. Statistics do not establish individual sales contribution or suitability for employment decisions.'],
            'actions':[{'label':'Staffing overview','action':'overview'}]},[row['employee_id']],public.keys())
