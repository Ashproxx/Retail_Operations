from collections.abc import Callable
from app.api.schemas import RequestContext
from app.security.policy import authorize,AccessDenied
from app.security.integrity import SealedDocument,verify,IntegrityFailure

DOMAIN_ACTION={'inventory':'inventory.read','demand':'forecast.read','analytics':'analytics.read',
               'pricing':'pricing.recommend','orders':'orders.read','supply':'supply.read',
               'support':'support.read','returns':'returns.read'}


def retrieve_verified(context:RequestContext,store_id:str,domain:str,question:str,
                      provider:Callable,key:bytes)->list[SealedDocument]:
    if domain not in DOMAIN_ACTION:raise AccessDenied('Unknown retrieval domain')
    authorize(context,DOMAIN_ACTION[domain],store_id)
    if not question.strip() or len(question)>4000:raise ValueError('Invalid retrieval question')
    # Providers are trusted configured adapters; user input cannot choose callables.
    records=provider(store_id=store_id,domain=domain,question=question)
    result=[]
    for item in records:
        sealed=SealedDocument.model_validate(item)
        if sealed.document.store_id!=store_id or sealed.document.domain!=domain:
            raise IntegrityFailure('Retrieved scope mismatch')
        verify(sealed,key)
        result.append(sealed)
    return result
