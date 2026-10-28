'use strict';
window.demoWorkspace = (() => {
  let stop = () => {}, enabled;
  const el = (tag,text) => {const n=document.createElement(tag);if(text!=null)n.textContent=text;return n;};
  const table = (parent,rows,title) => {
    const details=el('details'),summary=el('summary',title);details.append(summary);
    if(!rows.length)details.append(el('p','No records in this selection. Coverage may be unknown.'));
    else {const wrap=el('div'),t=el('table');wrap.className='table-wrap';const head=t.createTHead().insertRow();
      Object.keys(rows[0]).forEach(k=>{const th=el('th',k.replaceAll('_',' '));th.scope='col';head.append(th);});
      const body=t.createTBody();rows.forEach(row=>{const tr=body.insertRow();Object.values(row).forEach(v=>tr.insertCell().textContent=v==null?'Unknown':typeof v==='object'?JSON.stringify(v):String(v));});wrap.append(t);details.append(wrap);}
    parent.append(details);
  };
  async function start(api,model) {
    stop();let stopped=false,timer,epoch=0,delay=30000;const charts=[];
    const root=el('section');root.className='answer';root.id='live-demo';
    const heading=el('h2','Daily operations'),banner=el('p','SIMULATED DEMO DATA — Asia/Kolkata'),status=el('p');status.role='status';
    banner.className='badge';root.append(banner,heading,status);
    stop=()=>{stopped=true;epoch++;clearTimeout(timer);charts.forEach(c=>c.dispose());root.remove();};
    if(!['models','retail','employees','datasets'].includes(model))return;
    try { enabled ??= (await fetch('/api/demo/enabled',{cache:'no-store'})).ok; } catch {return;}
    if(stopped||!enabled)return;
    document.getElementById('main').append(root);
    const form=el('form'),preset=el('select'),from=el('input'),to=el('input'),store=el('select'),category=el('select'),source=el('select'),sku=el('input');
    from.type=to.type='date';
    [['today','Today'],['yesterday','Yesterday'],['7','Last 7 days'],['30','Last 30 days'],['custom','Custom']].forEach(([v,t])=>{const o=el('option',t);o.value=v;preset.append(o);});
    [['all','All sources'],['generated','Generated simulation'],['imported','Copied / unverified']].forEach(([v,t])=>{const o=el('option',t);o.value=v;source.append(o);});
    [store,category].forEach(s=>{const o=el('option','All');o.value='';s.append(o);});
    const add=(label,node)=>{const l=el('label',label);l.append(node);form.append(l);};
    add('Period',preset);add('From',from);add('Through',to);
    if(model!=='employees'){add('Store',store);add('Category',category);add('Source',source);add('SKU (optional)',sku);}
    const apply=el('button','Apply / refresh');form.append(apply);form.className='demo-filters';root.append(form);
    const summary=el('div'),history=el('div');root.append(summary,history);
    const pager=el('button','Next records'),exportButton=el('button','Export displayed records'),runs=el('button','Run / import history');
    root.append(pager,exportButton);if(model!=='employees')root.append(runs);
    let cursor=model==='employees'?'':0,rows=[],params='',loadedOptions=false;
    const dateString=d=>d.toISOString().slice(0,10);
    function range() {
      if(preset.value==='custom')return;
      const today=new Date(new Date().toLocaleString('en-US',{timeZone:'Asia/Kolkata'}));
      const end=new Date(Date.UTC(today.getFullYear(),today.getMonth(),today.getDate()));
      if(preset.value==='yesterday')end.setUTCDate(end.getUTCDate()-1);
      const begin=new Date(end);if(['7','30'].includes(preset.value))begin.setUTCDate(begin.getUTCDate()-Number(preset.value)+1);
      from.value=dateString(begin);to.value=dateString(end);
    }
    range();preset.onchange=range;
    function query(){return new URLSearchParams({start:from.value,end:to.value,store:store.value,category:category.value,source:source.value,sku:sku.value}).toString();}
    async function page(current) {
      const data=await api('demo/'+(model==='employees'?'staff':'events')+'?'+params+'&after='+encodeURIComponent(cursor));
      if(stopped||current!==epoch)return;
      rows=data.rows;cursor=data.next;history.replaceChildren();table(history,rows,model==='employees'?'Shift and attendance details':'Transactions and stock movements');
      pager.disabled=rows.length<50;
      if(data.page_summary)summary.append(el('p','Displayed shift status counts: '+JSON.stringify(data.page_summary)));
    }
    function trend(parent,data,key,label) {
      table(parent,data,label+' values');if(!window.echarts||!data.length)return;
      const node=el('div');node.className='chart';node.setAttribute('aria-label',label);node.role='img';parent.append(node);
      const chart=echarts.init(node);charts.push(chart);
      chart.setOption({animation:false,aria:{enabled:true},tooltip:{trigger:'axis',renderMode:'richText'},grid:{left:65,right:20,bottom:70},
        xAxis:{type:'category',data:data.map(r=>r[key])},yAxis:{type:'value',name:'Net INR'},
        series:[{type:'bar',data:data.map(r=>r.net_paise==null?null:r.net_paise/100)}]});
    }
    async function refresh() {
      clearTimeout(timer);const current=++epoch;params=query();cursor=model==='employees'?'':0;
      status.textContent='Reading committed records…';
      try {
        if(model!=='employees') {
          const data=await api('demo/summary?'+params);if(stopped||current!==epoch)return;
          charts.splice(0).forEach(c=>c.dispose());summary.replaceChildren();
          status.textContent=data.worker+' · '+data.freshness+' · Last event '+(data.last_received||'unknown')+' · Last run '+(data.last_success||'none')+' · Next slot '+data.next_due;
          const money=v=>v==null?'Unknown':'₹'+(v/100).toLocaleString('en-IN',{maximumFractionDigits:2});
          summary.append(el('p',data.revenue_definition),el('p','Selected range: '+money(data.totals.net_paise)+' · Units '+(data.totals.units??'Unknown')+' · Orders '+(data.totals.orders??'Unknown')+' · Returned units '+(data.totals.returned_units??'Unknown')));
          summary.append(el('p','Today '+money(data.today.net_paise)+' / yesterday at this time '+money(data.yesterday_elapsed.net_paise)),el('p',data.comparison));
          data.warnings.forEach(w=>summary.append(el('p',w)));
          trend(summary,data.daily,'day','Daily net revenue');trend(summary,data.monthly,'month','Monthly net revenue');
          table(summary,data.seasonal_overlay,'Monthly category factors — simulation assumptions');table(summary,data.events,'Dated campaign annotations');
          table(summary,data.stock,'Stock as of '+data.stock_as_of+' — first 100 pairs');table(summary,data.low_stock,'Low stock within displayed pairs');
          summary.append(el('p','Known stock: '+(data.stock_summary.known_units??'Unknown')+' units across '+data.stock_summary.known_pairs+' pairs; '+(data.stock_summary.catalog_pairs-data.stock_summary.known_pairs)+' pairs have unknown stock. Low stock: '+data.stock_summary.low_stock_pairs+' pairs. Select a store / SKU to inspect movements below.'));
          if(!loadedOptions){data.stores.forEach(v=>{const o=el('option',v);o.value=v;store.append(o);});data.categories.forEach(v=>{const o=el('option',v);o.value=v;category.append(o);});loadedOptions=true;}
          runs.hidden=!data.can_review_runs;
        } else {summary.replaceChildren();status.textContent='SIMULATED staff · scheduled and actual attendance are listed separately.';}
        await page(current);delay=30000;
      } catch(error) {if(!stopped&&current===epoch){status.textContent=error.message+' Display may be stale.';delay=Math.min(delay*2,300000);}}
      finally {if(!stopped&&current===epoch)timer=setTimeout(refresh,delay);}
    }
    form.onsubmit=e=>{e.preventDefault();refresh();};pager.onclick=()=>{clearTimeout(timer);page(epoch).catch(e=>status.textContent=e.message);};
    runs.onclick=async()=>{try{const data=await api('demo/runs');if(!stopped)table(history,data.rows,'Run/import history — first 50, API cursor available');}catch(e){if(!stopped)status.textContent=e.message;}};
    exportButton.onclick=()=>{const blob=new Blob([JSON.stringify(rows,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob),a=el('a');a.href=url;a.download='simulated-demo-records.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
    const resize=()=>charts.forEach(c=>c.resize());window.addEventListener('resize',resize);
    const previousStop=stop;stop=()=>{previousStop();window.removeEventListener('resize',resize);};
    refresh();
  }
  return {start,stop:()=>stop()};
})();
