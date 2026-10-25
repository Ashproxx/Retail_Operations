const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {parseSales} = require('../../app/ml_dashboard/static/live.js');
assert.deepEqual(parseSales(': heartbeat\n\nid: 4\ndata: {"id":4,"quantity":0}\n\n'), [{id:4,quantity:0}]);
assert.deepEqual(parseSales('id: 5\r\ndata: {"id":5}\r\n\r\n'), [{id:5}]);
assert.throws(() => parseSales('event: authentication-required\ndata: {}\n\n'), /Access token/);
assert.throws(() => parseSales('data: invalid\n\n'));

(async () => {
  let unauthorized = 0, scheduled = 0, resolve, signal;
  const element = {textContent:''};
  const context = vm.createContext({AbortController, module:{exports:{}}, $:()=>element,
    setTimeout:()=>{scheduled++;}, clearTimeout:()=>{},
    fetch:async () => ({status:401,ok:false})});
  vm.runInContext(fs.readFileSync('app/ml_dashboard/static/live.js','utf8'), context);
  context.unauthorized = () => { unauthorized++; vm.runInContext('stopLive()',context); };
  vm.runInContext("startLive('secret', unauthorized)",context);
  await new Promise(setImmediate);
  assert.equal(unauthorized,1); assert.equal(scheduled,0);
  context.fetch = (_url,options) => {signal=options.signal; return new Promise(r=>{resolve=r;});};
  vm.runInContext("startLive('secret', unauthorized); stopLive()",context);
  assert.equal(signal.aborted,true);
  resolve({status:200,ok:true,json:async()=>({})});
  await new Promise(setImmediate);
  assert.equal(scheduled,0);
  context.fetch = async () => {throw new TypeError('offline');};
  vm.runInContext("startLive('secret', unauthorized)",context);
  await new Promise(setImmediate);
  assert.match(element.textContent,/Connection lost/); assert.equal(scheduled,1);
  vm.runInContext('stopLive()',context);
  console.log('PASS: SSE parsing, authentication cleanup, abort and reconnect');
})().catch(error=>{console.error(error);process.exitCode=1;});
