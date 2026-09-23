"""Explicit download of the public pinned model for development evaluation only."""
import argparse
import json
from pathlib import Path
from huggingface_hub import snapshot_download

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    spec=json.loads(Path('evaluation/models.json').read_text())['embedding']
    snapshot_download(repo_id=spec['repository'],revision=spec['revision'],local_dir=args.output,
        allow_patterns=['*.json','*.safetensors','vocab.txt','1_Pooling/config.json','README.md'],
        ignore_patterns=['onnx/*','openvino/*'])
    print(json.dumps({'repository':spec['repository'],'revision':spec['revision'],'download':'complete'}))

if __name__=='__main__':main()
