/* Real browser + real disposable API. Install Playwright before running. */
const {chromium} = require('playwright');
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const path = require('node:path');
const output = path.resolve('validation-output/dashboard');
fs.mkdirSync(output,{recursive:true});
const server = spawn(process.env.RETAILOPS_PYTHON || 'python',
  ['-m','app.integration.showcase','--port','18765'],{stdio:['ignore','pipe','pipe']});
let startup = '';
server.stdout.on('data',chunk=>{startup+=chunk.toString();});
server.stderr.on('data',()=>{}); // Do not persist credentials or request logs.
const delay = ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(check){for(let i=0;i<100;i++){if(await check())return;await delay(100);}throw Error('UI update timed out');}
(async()=>{
 let browser;
 try {
  let ready=false;
  for(let i=0;i<60;i++){
   if(server.exitCode!==null)throw Error('Showcase server exited before readiness.');
   try{const r=await fetch('http://127.0.0.1:18765/health');if(r.ok){ready=true;break;}}catch{}
   await delay(500);
  }
  assert.ok(ready,'Showcase startup timed out');
  const token=startup.split('dialog:\n')[1]?.split('\n')[0]?.trim();
  assert.ok(token && token.length>=32,'Missing temporary token');
  browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:1050}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:18765/dashboard?demo=1');
  await page.locator('#token').fill('invalid');
  await page.getByRole('button',{name:'Connect workspace'}).click();
  await page.getByText('Access token rejected. Reconnect with a valid token.').waitFor();
  await page.locator('#token').fill(token);
  await page.getByRole('button',{name:'Connect workspace'}).click();
  await until(async()=>await page.locator('#sales').textContent()!=='—');
  assert.equal(await page.locator('#sales-chart .bar-row').count(),3);
  assert.equal(await page.locator('#token').inputValue(),'');
  assert.equal(await page.evaluate(()=>localStorage.length+sessionStorage.length),0);
  await page.screenshot({path:path.join(output,'desktop.png'),fullPage:true});
  await page.locator('#store').fill('ANDHERI');await page.locator('#store').press('Tab');
  await until(async()=>await page.locator('#stock').textContent()==='245');
  await page.locator('[data-view="inventory"]').click();
  await until(async()=>await page.locator('#inventory-table tbody tr').count()===6);
  assert.equal(await page.locator('#inventory-table tbody tr').count(),6);
  await page.locator('#low-only').check();
  assert.equal(await page.locator('#inventory-table tbody tr').count(),2);
  await page.locator('[data-view="forecast"]').click();
  await page.getByRole('button',{name:'Generate forecast'}).click();
  await page.waitForSelector('.forecast-column');
  assert.equal(await page.locator('.forecast-column').count(),7);
  await page.locator('[data-view="assistant"]').click();
  await page.locator('#store').fill('');await page.locator('#store').press('Tab');
  await until(async()=>await page.locator('#refresh').isEnabled());
  await page.locator('#message').fill('Which products are low in Bandra?');
  await page.getByRole('button',{name:'Send',exact:false}).click();
  await page.getByText('Inspect evidence, parameters & warnings').waitFor();
  assert.ok((await page.locator('#messages').textContent()).includes('matching inventory items'));
  await page.getByRole('button',{name:'Helpful',exact:true}).click();
  await page.getByText('Feedback recorded').waitFor();
  await page.locator('#message').fill('What about Andheri?');
  await page.getByRole('button',{name:'Send',exact:false}).click();
  await until(async()=>await page.locator('#messages details').count()===2);
  await page.screenshot({path:path.join(output,'assistant.png'),fullPage:true});
  await page.locator('[data-view="activity"]').click();
  await page.getByRole('button',{name:'Load activity',exact:true}).click();
  await page.waitForSelector('#audit-result tbody tr');
  assert.ok((await page.locator('#audit-result').textContent()).includes('ADMIN'));
  assert.ok(!(await page.locator('#audit-result').textContent()).includes('undefined'));
  await page.locator('[data-view="overview"]').click();
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Mobile page overflow');
  await page.setViewportSize({width:1440,height:1050});
  await page.locator('#connection').click();
  await page.locator('#disconnect').click();
  assert.equal(await page.locator('#sales').textContent(),'—');
  assert.equal(await page.locator('#messages').textContent(),'');
  assert.deepEqual(errors,[]);
  console.log('PASS: real API authentication, three-store overview, inventory filter, forecast, chat/follow-up, feedback, audit, mobile layout and disconnect.');
 } finally {
  if(browser)await browser.close();
  server.kill('SIGINT');
 }
})().catch(error=>{console.error(error);process.exitCode=1;});
