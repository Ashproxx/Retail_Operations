"""Single-writer local audit hash chain; keep anchors outside the log."""
import hashlib,json,os
from pathlib import Path
from threading import Lock
from app.api.schemas import AuditEvent
from app.security.integrity import canonical,IntegrityFailure

ZERO='0'*64

def verify_chain(rows:list[dict],anchor:dict|None=None)->dict:
    previous=ZERO
    for i,row in enumerate(rows,1):
        if not isinstance(row,dict):raise IntegrityFailure('Invalid audit row')
        if set(row)!={'sequence','previous_hash','event','hash'}:raise IntegrityFailure('Invalid audit row')
        if row['sequence']!=i or row['previous_hash']!=previous:raise IntegrityFailure('Broken audit linkage')
        event=AuditEvent.model_validate(row['event'])
        if event.timestamp.tzinfo is None:raise IntegrityFailure('Naive audit timestamp')
        payload={k:v for k,v in row.items() if k!='hash'}
        digest=hashlib.sha256(canonical(payload)).hexdigest()
        if digest!=row['hash']:raise IntegrityFailure('Audit digest mismatch')
        previous=digest
    observed={'count':len(rows),'head':previous}
    if anchor is not None and observed!=anchor:raise IntegrityFailure('Audit anchor mismatch')
    return observed

class AuditChain:
    def __init__(self,path:Path,trusted_anchor:dict|None=None):
        self.path=path;self._lock=Lock();self._anchor=trusted_anchor.copy() if trusted_anchor else None
    def read(self)->list[dict]:
        if not self.path.exists():
            verify_chain([],self._anchor)
            return []
        try:rows=[json.loads(line) for line in self.path.read_text(encoding='utf-8').splitlines()]
        except (ValueError,UnicodeError):raise IntegrityFailure('Unreadable audit log') from None
        verify_chain(rows,self._anchor)
        return rows
    def append(self,event:AuditEvent)->dict:
        if event.timestamp.tzinfo is None:raise IntegrityFailure('Naive audit timestamp')
        with self._lock:
            rows=self.read();anchor=verify_chain(rows)
            body={'sequence':len(rows)+1,'previous_hash':anchor['head'],'event':event.model_dump(mode='json')}
            row={**body,'hash':hashlib.sha256(canonical(body)).hexdigest()}
            fd=os.open(self.path,os.O_WRONLY|os.O_CREAT|os.O_APPEND|getattr(os,'O_NOFOLLOW',0),0o600)
            with os.fdopen(fd,'a',encoding='utf-8') as stream:
                stream.write(json.dumps(row,sort_keys=True)+'\n');stream.flush();os.fsync(stream.fileno())
            self._anchor={'count':row['sequence'],'head':row['hash']}
            return self._anchor.copy()
