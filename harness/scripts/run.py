#!/usr/bin/env python3
import json,sys
from pathlib import Path
from verify import ROOT,read,evaluate
from live_evidence import validate

def run(root,slug,evidence=None,expected_sha=None):
    if not slug or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in slug): raise ValueError('invalid slug')
    folder=root/'runs'/slug; folder.mkdir(parents=True,exist_ok=True)
    statefile=folder/'state.json'
    state=read(statefile) if statefile.exists() else {'failures':{},'blocked':False}
    if state['blocked']: return 3,state
    live=None
    if evidence is not None or expected_sha is not None:
        try: live,issues=validate(root,folder,evidence,expected_sha)
        except (ValueError,TypeError,KeyError,OSError) as e: return 2,{'status':'error','errors':['invalid live evidence: '+str(e)]}
        if issues: return 2,{'status':'error','errors':issues}
    r=read(root/'harness/rules.yaml');results=[];code=0
    for stage in ['prepare','research','design','draft','approval','system','screens']:
        try:
            errors,pending=evaluate(root,folder,stage,live)
            status='waiting' if pending else 'fail' if errors else 'pass'
        except (ValueError,TypeError,KeyError,OSError) as e: errors=[str(e)];status='error'
        results.append({'stage':stage,'status':status,'errors':errors})
        if status=='pass': state['failures'][stage]=0;continue
        code=2 if status=='error' else 1
        if status=='fail':
            state['failures'][stage]=state['failures'].get(stage,0)+1
            if state['failures'][stage]>=r['max_failures']: state['blocked']=True;code=3
        break
    state['evidence_sha256']=expected_sha
    state['results']=results;state['status']='blocked' if state['blocked'] else results[-1]['status']
    temp=statefile.with_suffix('.tmp');temp.write_text(json.dumps(state,ensure_ascii=False,indent=2));temp.replace(statefile)
    return code,state
if __name__=='__main__':
    try:
        import argparse
        p=argparse.ArgumentParser();p.add_argument('slug',nargs='?',default='library');p.add_argument('--live-evidence',type=Path);p.add_argument('--evidence-sha256');a=p.parse_args()
        code,state=run(ROOT,a.slug,a.live_evidence,a.evidence_sha256);print(json.dumps(state,ensure_ascii=False,indent=2));raise SystemExit(code)
    except (ValueError,OSError) as e: print(str(e));raise SystemExit(2)
