import copy,json,tempfile,unittest
from pathlib import Path
from verify import ROOT,read,check,evaluate,fingerprint
from run import run
class Gates(unittest.TestCase):
 def setUp(self):
  self.r=read(ROOT/'harness/rules.yaml')
  self.research=read(ROOT/'runs/library/research.json');self.design=read(ROOT/'runs/library/design.json')
  self.frame={'screen_id':'library-list','node_id':'1:2','width':390,'height':844,'fonts':[self.r['font']],'colors':['#ffffff'],'shadow_count':0}
 def test_each_gate_positive_and_negative(self):
  f=copy.deepcopy(self.frame);f['screen_id']='resource-detail';f['node_id']='1:3'
  cases={'research':self.research,'design':self.design,'draft':{'frames':[self.frame,f]},'system':{'font':self.r['font'],'tokens':['ink'],'components':[{'node_id':'1:4','bindings':['ink']}]},'screens':{'frames':[self.frame,f],'expected_screens':['library-list','resource-detail']}}
  for stage,value in cases.items():
   with self.subTest(stage=stage):
    self.assertEqual(check(stage,value,self.r),[])
    bad=copy.deepcopy(value)
    if stage=='research': bad['references']=bad['references'][:1]
    elif stage=='design':bad['service']['sale_roles']=['paid','seller']
    elif stage=='system':bad['components']=[]
    else:bad['frames'][0]['fonts']=['Inter']
    self.assertTrue(check(stage,bad,self.r))
 def test_privacy_and_scope(self):
  self.design['service']['asset_default']='public';self.design['features']+=['payment']
  self.assertEqual(len(check('design',self.design,self.r)),2)
 def test_duplicate_reference(self):
  self.research['references'][1]['source']=self.research['references'][0]['source']
  self.assertIn('duplicate sources',check('research',self.research,self.r))
 def test_state_and_approval(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);folder=root/'runs/test';folder.mkdir(parents=True);(root/'docs').mkdir();(root/'harness').mkdir()
   for name in ['prd','design','story-service','story-work','harness-purpose']:(root/'docs'/f'{name}.md').write_text('fixture')
   (root/'harness/rules.yaml').write_text(json.dumps(self.r))
   for stage,value in [('research',self.research),('design',self.design)]: (folder/f'{stage}.json').write_text(json.dumps(value))
   for _ in range(4):
    code,state=run(root,'test');self.assertEqual(code,1);self.assertFalse(state['blocked']);self.assertEqual(state['status'],'waiting')
   (folder/'draft.json').write_text('{}')
   approval={'decision':'approved','reviewer':'human fixture','input_hash':fingerprint(root,folder)}
   (folder/'approval.json').write_text(json.dumps(approval));self.assertEqual(evaluate(root,folder,'approval'),([],False))
   (folder/'design.json').write_text('{}');self.assertTrue(evaluate(root,folder,'approval')[0])
   (folder/'design.json').write_text(json.dumps(self.design))
   bad=copy.deepcopy(self.research);bad['references']=[];(folder/'research.json').write_text(json.dumps(bad))
   for _ in range(self.r['max_failures']):code,state=run(root,'test')
   self.assertEqual(code,3);self.assertTrue(state['blocked']);self.assertEqual(run(root,'test')[0],3)
 def test_live_evidence_not_auto_pass(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'harness').mkdir();(root/'harness/rules.yaml').write_text(json.dumps(self.r))
   runpath=root/'runs/test';runpath.mkdir(parents=True)
   (runpath/'design.json').write_text(json.dumps(self.design))
   f=copy.deepcopy(self.frame);f['screen_id']='resource-detail'
   (runpath/'draft.json').write_text(json.dumps({'frames':[self.frame,f]}))
   errors,pending=evaluate(root,runpath,'draft');self.assertTrue(pending);self.assertTrue(errors)
class LiveEvidence(unittest.TestCase):
 def setUp(self):
  import shutil,time
  from live_evidence import digest
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  for folder in ['docs','harness','runs']:
   shutil.copytree(ROOT/folder,self.root/folder,ignore=shutil.ignore_patterns('__pycache__'))
  self.folder=self.root/'runs/library';(self.folder/'state.json').unlink(missing_ok=True)
  (self.folder/'approval.json').write_text(json.dumps({'decision':'approved','reviewer':'test fixture','input_hash':fingerprint(self.root,self.folder)}))
  required=['harness/rules.yaml','harness/defaults.yaml','harness/scripts/verify.py','harness/scripts/run.py','harness/scripts/live_evidence.py','harness/scripts/collect-figma.js','harness/scripts/prepare-evidence.py']
  required += ['runs/library/'+s+'.json' for s in ['research','design','draft','approval','system','screens']]
  required += [str(p.relative_to(self.root)) for p in sorted((self.root/'docs').glob('*.md'))]
  snapshot=read(self.folder/'figma-live.json')
  self.e={'source':'Figma MCP use_figma','file_key':snapshot['file_key'],'observed_at':time.time(),'input_hashes':{p:digest(self.root/p) for p in required},'snapshot_sha256':digest(self.folder/'figma-live.json'),'visual_reviewed_nodes':[f['node_id'] for f in snapshot['frames']],'visual_errors':[]}
  self.path=self.folder/'evidence-test.json';self.save()
 def tearDown(self):self.temp.cleanup()
 def save(self):
  from live_evidence import digest
  self.path.write_text(json.dumps(self.e));self.sha=digest(self.path)
 def test_end_to_end(self):
  code,state=run(self.root,'library',self.path,self.sha)
  self.assertEqual(code,0,state);self.assertEqual(len(state['results']),7)
  self.assertTrue(all(x['status']=='pass' for x in state['results']))
 def test_stale_evidence(self):
  self.e['observed_at']-=3600;self.save();self.assertEqual(run(self.root,'library',self.path,self.sha)[0],2)
 def test_future_evidence(self):
  self.e['observed_at']+=3600;self.save();self.assertEqual(run(self.root,'library',self.path,self.sha)[0],2)
 def test_tampered_snapshot(self):
  (self.folder/'figma-live.json').write_text('{}');self.assertEqual(run(self.root,'library',self.path,self.sha)[0],2)
 def test_changed_input(self):
  (self.root/'docs/design.md').write_text('changed');self.assertEqual(run(self.root,'library',self.path,self.sha)[0],2)
 def test_wrong_checksum(self):self.assertEqual(run(self.root,'library',self.path,'0'*64)[0],2)
 def test_wrong_file(self):
  self.e['file_key']='other';self.save();self.assertEqual(run(self.root,'library',self.path,self.sha)[0],2)
 def test_missing_visual_review(self):
  self.e['visual_reviewed_nodes'].pop();self.save();self.assertEqual(run(self.root,'library',self.path,self.sha)[0],2)
 def test_missing_manifest(self):
  self.e['input_hashes'].pop('harness/rules.yaml');self.save();self.assertEqual(run(self.root,'library',self.path,self.sha)[0],2)
 def test_replay_without_fresh_evidence_waits(self):
  self.assertEqual(run(self.root,'library',self.path,self.sha)[0],0)
  code,state=run(self.root,'library');self.assertEqual(code,1);self.assertEqual(state['status'],'waiting')
 def test_live_font_mismatch_fails(self):
  live=read(self.folder/'figma-live.json');live['frames'][0]['fonts']=['Inter']
  errors,pending=evaluate(self.root,self.folder,'draft',live);self.assertTrue(errors);self.assertFalse(pending)
 def test_missing_state_fails(self):
  p=self.folder/'screens.json';data=read(p);data['state_frames'].pop();p.write_text(json.dumps(data))
  errors,pending=evaluate(self.root,self.folder,'screens',read(self.folder/'figma-live.json'));self.assertTrue(errors);self.assertFalse(pending)
 def test_error_is_not_waiting(self):
  p=self.folder/'draft.json';data=read(p);data['frames'][0]['width']=100;p.write_text(json.dumps(data))
  errors,pending=evaluate(self.root,self.folder,'draft');self.assertTrue(errors);self.assertFalse(pending)
if __name__=='__main__':unittest.main(verbosity=2)
