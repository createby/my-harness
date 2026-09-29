#!/usr/bin/env python3
"""Read-only structural gates. Figma JSON is evidence to inspect, not trusted attestation."""
import argparse, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(p): return json.loads(Path(p).read_text())
def fingerprint(root, run):
    files=[*sorted((root/'docs').glob('*.md')),root/'harness/rules.yaml',run/'research.json',run/'design.json',run/'draft.json']
    return hashlib.sha256(b''.join(str(p.relative_to(root)).encode()+b'\0'+p.read_bytes()+b'\0' for p in files)).hexdigest()
def check(stage,data,r):
    errors=[]
    def need(ok,msg):
        if not ok: errors.append(msg)
    if stage=='research':
        refs=data['references']; ids=[x['id'] for x in refs]
        need(len(refs)>=r['min_references'],'insufficient references')
        need(len(ids)==len(set(ids)),'duplicate reference IDs')
        need(len({x['source'] for x in refs})==len(refs),'duplicate sources')
        need(all(x['source'] and x['observation'] for x in refs),'empty reference')
        need(bool(data['applications']),'missing applications')
        need(all(x['reference_id'] in ids and x['decision'] for x in data['applications']),'untraceable application')
    elif stage=='design':
        screens=data['screens']; ids=[x['id'] for x in screens]
        need(bool(ids) and len(ids)==len(set(ids)),'empty or duplicate screens')
        need(all(x['title'] and x['sections'] and x['roles'] for x in screens),'incomplete screen')
        need(data['service']['sale_roles']==r['sale_roles'],'sale permission violation')
        need(set(r['review_states'])<=set(data['service']['review_states']),'review bypass')
        need(data['service']['asset_default']=='private','asset privacy violation')
        need(not set(data['features']) & set(r['excluded']),'excluded feature included')
    elif stage in ('draft','screens'):
        frames=data['frames']; ids=[x['screen_id'] for x in frames]
        need(bool(frames) and len(ids)==len(set(ids)),'empty or duplicate frames')
        if stage=='draft': need(r['key_screens'][0]<=len(frames)<=r['key_screens'][1],'key screen count')
        for x in frames:
            need(bool(x['node_id']),'missing Figma node')
            need([x['width'],x['height']]==r['frame'],'frame size mismatch')
            need(bool(x['fonts']) and set(x['fonts'])=={r['font']},'font mismatch')
            need(bool(x['colors']) and set(x['colors'])<=set(r['colors']),'palette violation')
            need(x['shadow_count']==0,'shadow violation')
            need(not x.get('errors',[]),'live geometry violation')
        if stage=='screens':
            need(set(ids)==set(data['expected_screens']),'screen coverage mismatch')
    elif stage=='system':
        need(data['font']==r['font'],'font mismatch')
        need(bool(data['tokens']) and bool(data['components']),'empty system')
        need(all(x['node_id'] and x['bindings'] for x in data['components']),'unbound component')
    else: raise ValueError('unknown stage')
    return errors

def evaluate(root, run, stage, live=None):
    r=read(root/'harness/rules.yaml')
    if stage=='prepare':
        needed=['prd.md','design.md','story-service.md','story-work.md','harness-purpose.md']
        return (['missing '+n for n in needed if not (root/'docs'/n).is_file()],False)
    file=run/(stage+'.json')
    if not file.exists(): return (['missing '+file.name],True)
    data=read(file)
    if stage=='approval':
        valid=data.get('input_hash')==fingerprint(root,run) and data.get('decision')=='approved' and bool(data.get('reviewer'))
        return ([] if valid else ['missing or stale human approval'], not valid)
    errors=check(stage,data,r)
    if stage in ('draft','screens'):
        design=read(run/'design.json')
        allowed={x['id'] for x in design['screens']}
        actual={x['screen_id'] for x in data['frames']}
        if not actual<=allowed or (stage=='screens' and actual!=allowed): errors.append('design coverage mismatch')
    if stage not in ('draft','system','screens'): return errors,False
    if errors: return errors,False
    if live is None: return ['fresh pinned live evidence required'],True
    if stage=='system':
        if data!=live['system']: errors.append('system differs from live data')
        token_ids={t['id'] for t in data['tokens']}
        for t in data['tokens']:
            if not t['codeSyntax'].get('WEB','').startswith('var('): errors.append('missing token code syntax')
            if 'ALL_SCOPES' in t['scopes']: errors.append('overbroad token scope')
            for value in t['values'].values():
                if isinstance(value,dict) and value.get('type')=='VARIABLE_ALIAS' and value['id'] not in token_ids: errors.append('broken token alias')
        for c in data['components']:
            if not all(x in token_ids for x in c['fillBindings']): errors.append('unbound component fill')
            if any(t['font']!=r['font'] for t in c['children']): errors.append('component font mismatch')
    else:
        actual={f['node_id']:f for f in live['frames']}
        fields=['node_id','screen_id','width','height','fonts','colors','shadow_count']
        for f in data['frames']:
            observed=actual.get(f['node_id'])
            if not observed or any(f[k]!=observed[k] for k in fields):errors.append('frame differs from live data')
            elif observed['errors']:errors.extend(observed['errors'])
        if stage=='screens':
            states=data['state_frames']
            if {f['state'] for f in data['frames']+states} != set(design['states']): errors.append('state coverage mismatch')
            declared={f['node_id'] for f in data['frames']+states}
            if declared!=set(actual): errors.append('live node coverage mismatch')
            for f in states:
                if actual.get(f['node_id'])!=f:errors.append('state differs from live data')
                probe=dict(f,screen_id=f['node_id'])
                errors.extend(check('screens',{'frames':[probe],'expected_screens':[probe['screen_id']]},r))
                if f['state']=='permission_denied':
                    text=' '.join(f['texts'])
                    if '멤버십 안내 보기' not in text or '워크북 다운로드' in text:errors.append('restricted-state access violation')
    return errors,False

def main():
    p=argparse.ArgumentParser();p.add_argument('stage');p.add_argument('--run',default='library');a=p.parse_args()
    if not a.run or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in a.run): p.error('invalid run slug')
    try:
        errors,pending=evaluate(ROOT,ROOT/'runs'/a.run,a.stage)
        result={'stage':a.stage,'status':'waiting' if pending else ('fail' if errors else 'pass'),'errors':errors}
        print(json.dumps(result,ensure_ascii=False));return 1 if errors or pending else 0
    except (KeyError,TypeError,ValueError,OSError) as e:
        print(json.dumps({'status':'error','error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__': raise SystemExit(main())
