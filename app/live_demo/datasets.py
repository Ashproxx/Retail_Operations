"""Current demo inventory and attendance for the existing dataset cards."""
from collections import Counter
import json
from app.api.schemas import Role
from app.security.policy import AccessDenied
from app.live_demo.config import TZ
from app.live_demo.store import connect, now_utc


def dataset(path,ctx,kind,offset,limit):
    now=now_utc();stamp=now.isoformat()
    if kind=='products':
        from app.live_demo.routes import clauses
        where,args=clauses(ctx)
        with connect(path) as db:
            records=[dict(r) for r in db.execute("""
                SELECT e.store_id,e.sku_id,
                COALESCE(json_extract(p.payload,'$.normalized_category'),json_extract(p.payload,'$.category'),'Unknown') category,
                CASE WHEN SUM(CASE WHEN e.kind='opening' THEN 1 ELSE 0 END)>0
                     THEN SUM(e.stock_delta) ELSE NULL END available_units
                FROM demo_events e JOIN retail_products p ON p.sku_id=e.sku_id
                WHERE """+where+' AND e.occurred_at<=? GROUP BY e.store_id,e.sku_id ORDER BY e.store_id,e.sku_id',[*args,stamp])]
        counts=Counter()
        for row in records:
            if row['available_units'] is not None: counts[row['category']]+=row['available_units']
        known=sum(r['available_units'] is not None for r in records)
        return dict(live=True,title='Available inventory',total=len(records),rows=records[offset:offset+limit],
                    metrics={'Known available units':sum(counts.values()) if known else None,
                             'Known store/product balances':known,'Unknown balances':len(records)-known},groups=dict(counts),
                    note='SIMULATED DEMO DATA. Signed stock movements as of '+stamp+'. Unknown opening balances are excluded from the pie, not counted as zero.',
                    chart_title='Available units by category',source='Simulated inventory ledger')
    if ctx.role not in {Role.ADMIN,Role.HR_ADMIN,Role.HR_USER}: raise AccessDenied('Live attendance requires HR access')
    where='1=1';args=[]
    if ctx.role==Role.HR_USER:
        if not ctx.store_ids: raise AccessDenied('No HR stores')
        where='e.store_id IN ('+','.join('?' for _ in ctx.store_ids)+')';args=list(ctx.store_ids)
    with connect(path) as db:
        rows=[]
        for employee in db.execute('SELECT e.employee_id,e.store_id,e.payload FROM employees e WHERE '+where+' ORDER BY e.employee_id',args):
            shifts=db.execute('SELECT * FROM demo_shifts WHERE employee_id=? AND business_date=?',(employee['employee_id'],str(now.astimezone(TZ).date()))).fetchall()
            status='Unknown'
            for shift in shifts:
                seen={r[0] for r in db.execute('SELECT status FROM demo_attendance WHERE shift_id=? AND occurred_at<=?',(shift['id'],stamp))}
                if 'clock_in' in seen and 'clock_out' not in seen and shift['start_at']<=stamp<shift['end_at']:
                    status='On duty';break
                if 'absent' in seen: status='Absent'
                elif 'clock_out' in seen: status='Finished'
                elif stamp<shift['start_at']: status='Scheduled'
            rows.append({'employee_id':employee['employee_id'],'store_id':employee['store_id'],
                         'full_name':json.loads(employee['payload']).get('full_name'),'current_status':status})
    counts=dict(Counter(r['current_status'] for r in rows))
    return dict(live=True,title='Current staff',total=len(rows),rows=rows[offset:offset+limit],
                metrics={'Employees':len(rows),'On duty':counts.get('On duty',0),'Unknown attendance':counts.get('Unknown',0)},
                groups=counts,note='SIMULATED DEMO DATA. Attendance as of '+stamp+'. Employment status is not attendance; no recorded shift or attendance means unknown.',
                chart_title='Current recorded attendance',source='Simulated shifts and attendance')
