/* Real browser/API check. Use RETAILOPS_PHASE3_DATABASE for full imported source acceptance. */
const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const output=path.resolve('validation-output/phase3');fs.mkdirSync(output,{recursive:true});
const db=process.env.RETAILOPS_PHASE3_DATABASE;
const server=spawn(process.env.RETAILOPS_PYTHON||'python',['-m',db?'app.enterprise.launch':'tests.phase3.browser_server','--port','18767',...(db?['--database',db]:[])],{stdio:['ignore','pipe','pipe']});
let startup='';server.stdout.on('data',c=>startup+=c);server.stderr.on('data',()=>{});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{let browser;try{
  let ready=false;for(let i=0;i<100;i++){if(server.exitCode!==null)throw Error('Server exited');try{if((await fetch('http://127.0.0.1:18767/health')).ok){ready=true;break;}}catch{}await delay(300);}assert(ready,'startup');
  const token=startup.match(/Temporary token \(expires in 8 hours\): (\S+)/)?.[1];assert(token?.length>=32);
  const headers={Authorization:'Bearer '+token};
  const options=await (await fetch('http://127.0.0.1:18767/api/retail/options',{headers})).json();
  browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1440,height:1050}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:18767/models');assert.equal(await page.locator('.model-card').count(),4);await page.screenshot({path:path.join(output,'models-desktop.png'),fullPage:true});
  await page.locator('.model-card[href="/retail"]').click();await page.locator('#connect').click();await page.locator('#token').fill(token);await page.getByRole('button',{name:'Connect workspace',exact:true}).click();await page.locator('#connection').waitFor({state:'hidden'});
  async function ask(text){const count=await page.locator('.turn').count();await page.locator('#message').fill(text);await page.locator('#message').press('Enter');await page.locator('.turn').nth(count).waitFor();}
  async function choose(text){const count=await page.locator('.turn').count();await page.locator('.answer').last().getByRole('button',{name:text,exact:true}).click();await page.locator('.turn').nth(count).waitFor();}
  await ask('How were sales?');await choose(options.locations[0].label);await choose('Latest available day');assert.match(await page.locator('.answer').last().textContent(),/net sales/);
  await ask('Show pie chart');assert.equal(await page.locator('.answer').last().locator('.chart canvas').count(),1);
  await page.screenshot({path:path.join(output,'retail-desktop.png'),fullPage:true});
  for(const type of ['bar','horizontal bar','doughnut']){await ask('Show '+type+' chart');assert.equal(await page.locator('.answer').last().locator('.chart canvas').count(),1);}
  await ask('Show daily line chart');await ask('Show area chart');
  await ask('Compare stores');await ask('Show grouped bar chart');for(const type of ['stacked bar','multi-line','heatmap']){await ask('Show '+type+' chart');assert.equal(await page.locator('.answer').last().locator('.chart canvas').count(),1);}
  await ask('Show sales on 2030-01-01');assert.match(await page.locator('.answer').last().textContent(),/No sales records/);await choose('Show latest available day');
  await ask('Current inventory');assert.match(await page.locator('.answer').last().textContent(),/no measured on-hand/);
  await page.locator('nav a[href="/employees"]').click();await page.locator('#employee-search').waitFor();assert.equal(await page.locator('.turn').count(),0);
  await ask('Show employees');const name=await page.locator('.answer').last().locator('.choices button').first().evaluate(n=>n.childNodes[0].textContent);
  await page.locator('.answer').last().locator('.choices button').first().click();await page.locator('.profile-grid').waitFor();assert.equal(await page.locator('.profile-grid').count(),1);await ask('What is her attendance?');assert.match(await page.locator('.answer').last().textContent(),/attendance/i);await ask('What is her salary?');assert.match(await page.locator('.answer').last().textContent(),/monthly gross salary/i);
  await page.locator('#reset').click();await page.locator('#search-name').fill(name.split(' ')[0]);await page.locator('#search-form button').click();await page.locator('#search-results button').first().waitFor();await page.locator('#search-results button').first().click();await page.locator('.profile-grid').waitFor();
  await page.screenshot({path:path.join(output,'employee-desktop.png'),fullPage:true});await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(output,'employee-mobile.png'),fullPage:true});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'mobile overflow');
  await ask('Who should be fired?');assert.match(await page.locator('.answer').last().textContent(),/authorized human/);
  await page.locator('nav a[href="/employee-work"]').click();await page.locator('#coming').waitFor();assert.match(await page.locator('#coming').textContent(),/Coming soon/);await page.locator('nav a[href="/management"]').click();assert.match(await page.locator('#future-title').textContent(),/Management/);
  await page.locator('nav a[href="/models"]').click();await page.screenshot({path:path.join(output,'models-mobile.png'),fullPage:true});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  assert.equal(await page.evaluate(()=>localStorage.length+sessionStorage.length),0);assert.deepEqual(errors,[]);await page.locator('#disconnect').click();assert.equal(await page.locator('.profile-grid').count(),0);
  const report={passed:true,dataset:db?'Full imported user-supplied synthetic workbooks':'Disposable CI fixtures',checks:['selector','progressive clarification','ten chart types','future date','inventory boundary','employee name search','profile followups','decision refusal','separate workspace conversation','coming soon','desktop/mobile','memory-only credentials']};fs.writeFileSync(path.join(output,'browser.json'),JSON.stringify(report,null,2));console.log('PASS: Phase 3 browser workflows ('+report.dataset+')');
}finally{if(browser)await browser.close();server.kill('SIGTERM');}})().catch(e=>{console.error(e.stack);process.exitCode=1;});
