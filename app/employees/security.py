"""Server-side HR field and store authorization, including aggregate-only analysts."""
from app.api.schemas import Role, AuditEvent
from app.security.policy import AccessDenied

GLOBAL={Role.ADMIN,Role.HR_ADMIN}
FULL=GLOBAL|{Role.HR_USER}
ROLES=FULL|{Role.STORE_MANAGER,Role.ANALYST}
SENSITIVE={'date_of_birth','age','gender','education','languages','monthly_gross_salary_inr','avg_monthly_incentive_inr','pf_applicable','esic_applicable'}
MANAGER_FIELDS={'full_name','store_location','city','zone','department','designation','grade','employment_type','confirmation_status','hire_date','tenure_years','reports_to_name','shift','weekly_off','weekly_hours','performance_rating','attendance_pct_last_90d','employment_status','last_working_date'}


def scope(query,model,ctx,*,detail=False):
    if ctx.role not in ROLES or detail and ctx.role==Role.ANALYST:raise AccessDenied('HR access is not permitted')
    if ctx.role not in GLOBAL:
        if not ctx.store_ids:raise AccessDenied('No authorized HR stores')
        query=query.where(model.store_id.in_(ctx.store_ids))
    return query


def profile(row,ctx):
    if ctx.role not in FULL|{Role.STORE_MANAGER} or ctx.role not in GLOBAL and row['store_id'] not in ctx.store_ids:raise AccessDenied('Employee is outside authorized scope')
    fields=MANAGER_FIELDS|SENSITIVE if ctx.role in FULL else MANAGER_FIELDS
    return {k:row.get(k) for k in sorted(fields)}


def audit(runtime,ctx,tool,status,subjects=(),fields=()):
    runtime.audit.append(AuditEvent(request_id=ctx.request_id,session_id=ctx.session_id,user_role=ctx.role,
        actor_id=ctx.principal_id,subject_ids=list(subjects),fields_accessed=sorted(set(fields)),
        agents_called=['employee-360'],tools_called=[tool],confidence=0,latency_ms=0,final_status=status))
