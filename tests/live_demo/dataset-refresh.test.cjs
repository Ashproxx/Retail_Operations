const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('app/enterprise/static/app.js','utf8');
const implementation=source.slice(source.indexOf('  async function loadDataset('),source.indexOf('  async function loadDatasets('));

(async()=>{
  const pending=[],renders=[],timers=new Map();let nextTimer=0;
  const box={setAttribute(){},removeAttribute(){},contains(){return false;},append(){},
    replaceChildren(...nodes){renders.push(nodes);}};
  const context=vm.createContext({generation:1,token:'local-test',charts:[],datasetTimers:{},datasetRequests:{},
    $:()=>box,el:(_tag,text)=>({text}),metric(){},table(){},chart(){},button(){},
    api:url=>new Promise((resolve,reject)=>pending.push({url,resolve,reject})),
    setTimeout:(fn,delay)=>{const id=++nextTimer;timers.set(id,{fn,delay});return id;},
    clearTimeout:id=>timers.delete(id)});
  vm.runInContext(implementation,context);
  const payload=title=>({live:true,title,source:'demo',metrics:{},note:'simulation',groups:{},rows:[],total:null});
  const first=context.loadDataset('products',0),second=context.loadDataset('products',25);
  pending[1].resolve(payload('new page'));await second;
  pending[0].resolve(payload('stale page'));await first;
  assert.equal(renders.length,1);assert.equal(renders[0][0].text,'new page');
  assert.equal(timers.size,1);
  [...timers.values()][0].fn();
  assert.match(pending[2].url,/offset=25$/,'polling retains the selected page');
  context.generation++;context.token='';
  pending[2].resolve(payload('after disconnect'));await new Promise(setImmediate);
  assert.equal(renders.length,1,'late response must not restore protected data');
  assert.equal(timers.size,0);
  context.token='local-test';
  const stale=context.loadDataset('products'),current=context.loadDataset('products');
  pending[4].resolve(payload('current'));await current;
  pending[3].reject(new Error('late network failure'));await stale;
  assert.equal(renders.at(-1)[0].text,'current','stale errors cannot replace current results');
  console.log('PASS: dataset races, page-preserving refresh, disconnect and stale errors');
})().catch(error=>{console.error(error);process.exitCode=1;});
