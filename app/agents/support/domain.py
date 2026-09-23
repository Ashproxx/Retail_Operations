import re,hashlib
from datetime import date
from typing import Protocol
from pydantic import Field,model_validator
from app.api.schemas import Contract

class Policy(Contract):
    store_id:str=Field(min_length=1)
    document_id:str=Field(min_length=1)
    version:str=Field(min_length=1)
    valid_from:date
    valid_until:date|None=None
    approved:bool=False
    text:str=Field(min_length=1,max_length=30000)
    expected_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
    source:str=Field(min_length=1)
    fixture:bool=False
    @model_validator(mode='after')
    def dates(self):
        if self.valid_until and self.valid_until<self.valid_from:raise ValueError('Invalid policy validity')
        return self

class Query(Contract):
    store_id:str
    question:str=Field(min_length=1,max_length=4000)
    as_of:date
    min_coverage:float=Field(default=.6,gt=0,le=1)

class EvidenceRetriever(Protocol):
    def retrieve(self,question:str,trusted_store_id:str)->list[Policy]: ...

STOP={'what','is','the','a','an','i','am','please','about','my','to','for','and','policy','how','can','do','are','of','you'}
def terms(text:str)->set[str]:return set(re.findall(r'[a-z0-9]+',text.lower()))-STOP

def triage(question:str)->dict:
    text=question.lower()
    negative=bool(re.search(r'\bnot (?:happy|satisfied)\b',text))
    without_negated=re.sub(r'\bnot (?:angry|upset|frustrated)\b','',text)
    negative=negative or bool(re.search(r'\b(?:angry|furious|upset|frustrated|terrible)\b',without_negated))
    categories=[]
    for category,pattern in [('returns',r'\b(?:refund|return|defect\w*|wrong item)\b'),('orders',r'\b(?:order|delivery|shipping|shipment)\b'),('pricing',r'\b(?:price|discount|charged|billing)\b'),('inventory',r'\b(?:stock|inventory|availability)\b')]:
        if re.search(pattern,text):categories.append(category)
    return {'sentiment':'negative' if negative else 'positive' if re.search(r'\b(?:happy|satisfied|excellent|thanks)\b',text) else 'neutral','categories':categories or ['general'],
            'priority':'human_review' if negative else 'normal',
            'classifier':'lexical-triage-v1','warnings':['Heuristic sentiment/category labels, not calibrated predictions.']}


def evaluate(rows:list[Policy],query:Query)->dict:
    assessment=triage(query.question);wanted=terms(query.question);sources=[];rejected=0
    ids=[(r.document_id,r.version) for r in rows if r.store_id==query.store_id]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate policy version')
    for r in rows:
        if r.store_id!=query.store_id or not r.approved or r.valid_from>query.as_of or (r.valid_until and r.valid_until<query.as_of):continue
        if hashlib.sha256(r.text.encode()).hexdigest()!=r.expected_sha256:rejected+=1;continue
        coverage=len(wanted&terms(r.text))/len(wanted) if wanted else 0
        if coverage>=query.min_coverage:
            sources.append({'document_id':r.document_id,'version':r.version,'source':r.source,'text':r.text,
                            'query_coverage':coverage,'fixture':r.fixture,'content_hash':r.expected_sha256})
    sources.sort(key=lambda s:(-s['query_coverage'],s['document_id'],s['version']));sources=sources[:3]
    # Differing relevant policy statements are not reconciled by a lexical baseline.
    conflict=len({s['text'] for s in sources})>1
    sufficient=bool(sources) and not conflict
    handoffs={'returns':'returns-refunds','orders':'order-fulfillment','pricing':'pricing-promotions','inventory':'inventory'}
    return {'status':('escalated' if assessment['priority']=='human_review' else 'success') if sufficient else 'insufficient_evidence','triage':assessment,
            'handoffs':[handoffs[c] for c in assessment['categories'] if c in handoffs] if not sufficient or assessment['priority']=='human_review' else [],
            'answer':'Source excerpt: '+sources[0]['text'] if sufficient else 'The knowledge base does not contain enough unambiguous evidence.',
            'sources':sources,'requires_human':not sufficient or assessment['priority']=='human_review',
            'reason':'conflicting_evidence' if conflict else 'grounded_excerpt' if sufficient else 'insufficient_evidence',
            'integrity_rejections':rejected,'retrieval':'local lexical evidence adapter; Chroma integration deferred'}
