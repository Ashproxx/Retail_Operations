const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class Element {
  constructor(tag,text){this.tag=tag;this.textContent=text;this.children=[];this.value='';}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(...nodes){this.children=nodes;}
  remove(){this.removed=true;}
}
(async()=>{
  const main=new Element('main'),pending=[],timers=new Map();let timer=0;
  const context=vm.createContext({window:{addEventListener(){},removeEventListener(){}},
    document:{createElement:tag=>new Element(tag),getElementById:()=>main},Date,URLSearchParams,
    fetch:async()=>({ok:true}),setTimeout:(fn,delay)=>{const id=++timer;timers.set(id,{fn,delay});return id;},clearTimeout:id=>timers.delete(id)});
  vm.runInContext(fs.readFileSync('app/enterprise/static/demo.js','utf8'),context);
  const api=url=>new Promise((resolve,reject)=>pending.push({url,resolve,reject}));
  await context.window.demoWorkspace.start(api,'models');
  const root=main.children[0],form=root.children.find(n=>n.tag==='form');
  const exportButton=root.children.find(n=>n.textContent==='Export displayed records');
  const summary={worker:'running',freshness:'fresh',totals:{},today:{},yesterday_elapsed:{},
    warnings:[],daily:[],monthly:[],seasonal_overlay:[],events:[],stock:[],low_stock:[],stock_summary:{},stores:[],categories:[]};
  pending[0].resolve(summary);await new Promise(setImmediate);
  assert.match(pending[1].url,/demo\/events/);
  form.onsubmit({preventDefault(){}});
  assert.equal(exportButton.disabled,true);
  pending[1].resolve({rows:[],next:100});await new Promise(setImmediate);
  assert.equal(exportButton.disabled,true,'old rows must not become exportable under new filters');
  pending[2].resolve(summary);await new Promise(setImmediate);
  assert.match(pending[3].url,/after=0$/,'new filters start a fresh cursor');
  pending[3].resolve({rows:[],next:0});await new Promise(setImmediate);
  assert.equal(exportButton.disabled,false);assert.equal(timers.size,1);
  form.onsubmit({preventDefault(){}});
  pending[4].reject(new Error('offline'));await new Promise(setImmediate);
  assert.equal(exportButton.disabled,true,'failed refresh must not export old results');
  assert.equal([...timers.values()][0].delay,60000);
  context.window.demoWorkspace.stop();
  assert.equal(root.removed,true);assert.equal(timers.size,0);
  console.log('PASS: demo filter races, cursor reset, export freshness, backoff and cleanup');
})().catch(error=>{console.error(error);process.exitCode=1;});
