"""Run the complete conversation UI with disposable, labelled synthetic history."""
import argparse
import hashlib
import secrets
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import uvicorn
from app.main import create_app
from app.integration.config import RuntimeSettings
from app.integration.runtime import Runtime
from app.security.policy import Grant
from app.integration.fixtures import seed
from app.conversation.catalog import import_observations
from app.conversation.dates import today


def seed_conversation(database):
    rows=[]
    products=[('SHIRT-1','shirt','Oxford Shirt','Men','Blue','M',1299),
              ('C2','shirt','Linen Shirt','Men','White','L',1599),
              ('C3','shorts','Cotton Shorts','Women','Beige','M',799),
              ('C4','shorts','Weekend Shorts','Women','Blue','L',899),
              ('C5','tshirt','Essential Tee','Unisex','Black','M',599),
              ('C6','jeans','Straight Jeans','Women','Blue','M',1999)]
    for store,name,factor in [('BANDRA','Bandra',1),('ANDHERI','Andheri',2),('POWAI','Powai',3)]:
        for index in range(120):
            day=today()-timedelta(days=119-index)
            for n,(sku,category,style,gender,color,size,price) in enumerate(products):
                units=3+factor+n+(4 if day.weekday()>=5 else 0)+(index%3)
                stock=60+n*12
                if sku=='C3' and index>=106:units=1;stock=0
                if sku=='C4' and index>=106:units=2
                rows.append(dict(date=day.isoformat(),store_id=store,store_location=name,sku_id=sku,
                    category=category,style_name=style,gender=gender,color=color,size=size,supplier='Synthetic Apparel Co',
                    unit_price_inr=str(price),units_sold=units,opening_stock=stock+units,closing_stock=stock,
                    reorder_point=20,vendor_lead_time_days=5,stockout_risk_flag=stock==0))
    return import_observations(database,rows,source='conversation-showcase-synthetic',fixture=True)


def showcase_app(directory,token):
    directory=Path(directory)
    config=RuntimeSettings(_env_file=None,database_url='sqlite+pysqlite:///'+str(directory/'showcase.db'),
        state_dir=directory/'state',grants_file=None,integrity_key=None,embedding_model_path=None,llm_provider='deterministic')
    grant=Grant(token_sha256=hashlib.sha256(token.encode()).hexdigest(),principal_id='showcase-admin',role='ADMIN')
    def factory(database,settings):
        runtime=Runtime(database,settings,grants=[grant])
        seed(runtime.repository)
        seed_conversation(database)
        return runtime
    return create_app(config,factory)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8000)
    args=parser.parse_args()
    token=secrets.token_urlsafe(32)
    with TemporaryDirectory(prefix='retailops-conversation-') as directory:
        print('\nRetailOps | SYNTHETIC DEMO | 120 days through '+today().isoformat())
        print(f'Open http://127.0.0.1:{args.port}/assistant?demo=1')
        print('Paste this temporary token in Connect (it changes on every launch):')
        print(token,flush=True)
        print('Keep this terminal open. The demo database is deleted on exit.\n',flush=True)
        uvicorn.run(showcase_app(directory,token),host='127.0.0.1',port=args.port)

if __name__=='__main__':main()
