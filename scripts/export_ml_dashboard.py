"""Export pinned aggregate evidence locally; never merge source branches."""
import hashlib
import json
from pathlib import Path
import subprocess

SOURCES = {'forecast.json': ('6b86795e4cf7e2b3bc54f807f87813921c7539b5','docs/ml/FORECAST_RESULTS.json'),
           'auxiliary.json': ('70b02411c3f07782a135111d168f10f2129785ab','docs/auxiliary/RESULTS.json')}


def main():
    root=Path('validation-output/ml-dashboard')
    root.mkdir(parents=True,exist_ok=True)
    manifest={}
    for filename,(commit,path) in SOURCES.items():
        data=subprocess.check_output(['git','show',commit+':'+path])
        json.loads(data)
        (root/filename).write_bytes(data)
        manifest[filename]={'commit':commit,'path':path,'sha256':hashlib.sha256(data).hexdigest()}
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Exported pinned aggregate research evidence; no source code merged.')


if __name__=='__main__':main()
