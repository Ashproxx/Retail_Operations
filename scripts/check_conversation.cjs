/* Real browser, actual authenticated API, disposable synthetic observations. */
const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const output=path.resolve('validation-output/conversation');fs.mkdirSync(output,{recursive:true});
const server=spawn(process.env.RETAILOPS_PYTHON||'python',['-m','app.conversation.showcase','--port','18766'],{stdio:['ignore','pipe','pipe']});
let startup='';server.stdout.on('data',c=>startup+=c);server.stderr.on('data',()=>{});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{let browser;try{
let ready=false;for(let i=0;i<100;i++){if(server.exitCode!==null)throw Error('Server exited');try{if((await fetch('http://127.0.0.1:18766/health')).ok){ready=true;break;}}catch{}await delay(300);}assert(ready,'startup');
const token=startup.split('launch):\n')[1]?.split('\n')[0]?.trim();assert(token?.length>=32);
browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1440,height:1050}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:18766/assistant?demo=1');await page.screenshot({path:path.join(output,'welcome-desktop.png'),fullPage:true});
await page.locator('#connect').click();await page.locator('#token').fill('invalid');await page.getByRole('button',{name:'Connect workspace'}).click();await page.getByText('Token not accepted.',{exact:false}).waitFor();await page.locator('#token').fill(token);await page.getByRole('button',{name:'Connect workspace'}).click();await page.getByText('Connected ✓',{exact:true}).waitFor();assert.equal(await page.locator('#token').inputValue(),'');
async function ask(text){await page.locator('#message').fill(text);await page.locator('#message').press('Enter');await page.locator('.answer').last().locator('.summary').waitFor();}
async function choose(label){await page.locator('.answer').last().getByRole('button',{name:label,exact:true}).click();await page.locator('.answer').last().locator('.summary').waitFor();}
await ask("Show today's sales");await choose('Bandra');assert.match(await page.locator('.answer').last().textContent(),/units sold/);await ask('What about last week?');await choose('View graph');await choose('pie');await page.locator('.chart canvas').waitFor();await page.screenshot({path:path.join(output,'sales-chart-desktop.png'),fullPage:true});
await ask('Why are shorts not selling?');assert.match(await page.locator('.answer').last().textContent(),/STOCK CONSTRAINED/);await ask('What should we do about it?');assert.match(await page.locator('.answer').last().textContent(),/replenishment/);await ask('Who competes with it?');assert.match(await page.locator('.answer').last().textContent(),/External market competitor information is not configured/);
await ask('Forecast next 7 days');assert.match(await page.locator('.answer').last().textContent(),/Chronological model comparison/);
await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(output,'forecast-mobile.png'),fullPage:true});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'mobile overflow');
assert.equal(await page.evaluate(()=>localStorage.length+sessionStorage.length),0);assert.deepEqual(errors,[]);
await page.locator('#reset').click();assert.equal(await page.locator('.turn').count(),0);await page.screenshot({path:path.join(output,'welcome-mobile.png'),fullPage:true});
console.log('PASS: authenticated progressive dialogue, exact scope, charts, diagnostics, recommendations, competition, forecast, desktop/mobile and memory-only token');
}finally{if(browser)await browser.close();server.kill('SIGTERM');}})().catch(e=>{console.error(e.message);process.exitCode=1;});
