// Read-only use_figma collector. Caller supplies rules and targets from local JSON.
await figma.setCurrentPageAsync(await figma.getNodeByIdAsync('6:7'));
function visible(node,root){let p=node;while(p&&p!==root){if(p.visible===false)return false;p=p.parent;}return true;}
const frames=[];
for(const {node_id,screen_id,state} of targets){
 const n=await figma.getNodeByIdAsync(node_id);if(!n)throw new Error('Missing '+node_id);
 const all=[n,...n.findAll(()=>true)].filter(x=>visible(x,n));const fonts=new Set(),colors=new Set(),errors=[],texts=[];let shadows=0;
 for(const x of all){
  if(x.type==='TEXT'){
   for(const seg of x.getStyledTextSegments(['fontName']))fonts.add(seg.fontName.family);
   texts.push(x.characters);
   const b=x.absoluteBoundingBox,r=n.absoluteBoundingBox;
   if(b.x<r.x-.5||b.x+b.width>r.x+r.width+.5||b.y<r.y-.5||b.y+b.height>r.y+r.height+.5)errors.push('text overflow '+x.id);
  }
  if('effects' in x)shadows+=x.effects.filter(e=>e.visible!==false&&['DROP_SHADOW','INNER_SHADOW'].includes(e.type)).length;
  for(const field of ['fills','strokes'])if(field in x&&Array.isArray(x[field]))for(const p of x[field])if(p.type==='SOLID'&&p.visible!==false)colors.add('#'+[p.color.r,p.color.g,p.color.b].map(c=>Math.round(c*255).toString(16).padStart(2,'0')).join(''));
  if('layoutMode' in x&&x.layoutMode!=='NONE')for(const k of ['paddingLeft','paddingRight','paddingTop','paddingBottom','itemSpacing'])if(!rules.spacing.includes(x[k]))errors.push('spacing '+x.id+' '+k);
  if(x.name.endsWith('.cta')&&(x.height!==rules.button_height||x.cornerRadius<x.height/2))errors.push('button geometry '+x.id);
 }
 frames.push({node_id,screen_id,state,width:n.width,height:n.height,fonts:[...fonts],colors:[...colors],shadow_count:shadows,errors,texts});
}
const variables=(await figma.variables.getLocalVariablesAsync()).map(v=>({id:v.id,name:v.name,scopes:v.scopes,values:v.valuesByMode,codeSyntax:v.codeSyntax}));
const components=[];
for(const id of componentIds){const c=await figma.getNodeByIdAsync(id);if(!c)throw new Error('Missing component '+id);components.push({node_id:id,name:c.name,bindings:Object.keys(c.boundVariables),fillBindings:c.fills.map(p=>p.boundVariables?.color?.id),children:c.findAllWithCriteria({types:['TEXT']}).map(t=>({id:t.id,font:t.fontName.family,style:t.textStyleId}))});}
return {file_key:figma.fileKey,frames,system:{font:rules.font,tokens:variables,components}};
