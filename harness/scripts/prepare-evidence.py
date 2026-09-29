#!/usr/bin/env python3
"""Package an observation already obtained by the current MCP session.
Does not call Figma and cannot prove a caller is trustworthy.
"""
import argparse,json,time
from pathlib import Path
from live_evidence import digest
from verify import ROOT,read
p=argparse.ArgumentParser();p.add_argument('--observed-at',required=True,type=float);p.add_argument('--visual-review',required=True,type=Path);a=p.parse_args()
folder=ROOT/'runs/library';snapshot=read(folder/'figma-live.json');review=read(a.visual_review)
if review['snapshot_sha256']!=digest(folder/'figma-live.json'):raise SystemExit('Visual review targets another snapshot')
required=['harness/rules.yaml','harness/defaults.yaml','harness/scripts/verify.py','harness/scripts/run.py','harness/scripts/live_evidence.py','harness/scripts/collect-figma.js','harness/scripts/prepare-evidence.py']
required += ['runs/library/'+s+'.json' for s in ['research','design','draft','approval','system','screens']]
required += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'docs').glob('*.md'))]
e={'source':'Figma MCP use_figma','file_key':snapshot['file_key'],'observed_at':a.observed_at,'input_hashes':{p:digest(ROOT/p) for p in required},'snapshot_sha256':digest(folder/'figma-live.json'),'visual_reviewed_nodes':review['visual_reviewed_nodes'],'visual_errors':review['visual_errors']}
path=folder/'evidence.json';path.write_text(json.dumps(e,ensure_ascii=False,indent=2));print(digest(path))
