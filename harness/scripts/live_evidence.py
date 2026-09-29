"""Validate a pinned, recent MCP observation supplied by the current session.

This validates content/provenance records, not a cryptographic Figma attestation.
The caller must obtain the observation through the Figma tool, not an agent export.
"""
import hashlib,json,time

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def validate(root,run,evidence,expected_sha,now=None):
    if not evidence or not expected_sha:return None,['fresh pinned live evidence required']
    if digest(evidence)!=expected_sha:return None,['live evidence checksum mismatch']
    obj=json.loads(evidence.read_text());rules=json.loads((root/'harness/rules.yaml').read_text())
    now=time.time() if now is None else now
    age=now-obj['observed_at']
    if not 0<=age<=rules['live_evidence_max_age_seconds']:return None,['live evidence expired or future dated']
    if obj['source']!='Figma MCP use_figma' or obj['file_key']!=json.loads((root/'harness/defaults.yaml').read_text())['figma_file']:
        return None,['unexpected evidence origin/file']
    required=['harness/rules.yaml','harness/defaults.yaml','harness/scripts/verify.py','harness/scripts/run.py','harness/scripts/live_evidence.py','harness/scripts/collect-figma.js','harness/scripts/prepare-evidence.py']
    required += ['runs/'+run.name+'/'+s+'.json' for s in ['research','design','draft','approval','system','screens']]
    required += [str(p.relative_to(root)) for p in sorted((root/'docs').glob('*.md'))]
    if set(obj['input_hashes'])!=set(required):return None,['incomplete evidence input manifest']
    if any(digest(root/p)!=obj['input_hashes'][p] for p in required):return None,['inputs changed since live observation']
    snapshot=json.loads((run/'figma-live.json').read_text())
    if digest(run/'figma-live.json')!=obj['snapshot_sha256']:return None,['snapshot checksum mismatch']
    if snapshot['file_key']!=obj['file_key']:return None,['snapshot file mismatch']
    ids=[f['node_id'] for f in snapshot['frames']]
    if len(ids)!=len(set(ids)):return None,['duplicate live node IDs']
    if set(obj['visual_reviewed_nodes'])!=set(ids) or obj['visual_errors']:
        return None,['visual review missing or failed']
    return snapshot,[]
