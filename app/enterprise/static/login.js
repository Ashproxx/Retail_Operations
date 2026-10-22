(() => {
  const $=id=>document.getElementById(id);let email='';
  async function submit(path,body,form){
    const buttons=form.querySelectorAll('button');buttons.forEach(b=>b.disabled=true);$('login-status').textContent='Please wait…';
    try{const r=await fetch('/api/auth/'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await r.json();
      if(r.status===403){$('email-form').hidden=true;$('verify-form').hidden=true;$('login-title').textContent='Access denied';$('login-description').textContent="You don't have access to this page.";$('retry').hidden=false;$('login-status').textContent='';return false;}
      if(!r.ok)throw new Error(data.detail||data.message||'Unable to sign in. Please try again.');
      $('login-status').textContent=data.message||'';return true;
    }catch(e){$('login-status').textContent=e.message;return false;}finally{buttons.forEach(b=>b.disabled=false);}
  }
  $('email-form').onsubmit=async e=>{e.preventDefault();email=$('email').value.trim().toLowerCase();if(await submit('request',{email},e.target)){$('email-form').hidden=true;$('verify-form').hidden=false;$('login-description').textContent='Enter the token sent to '+email+'.';$('access-token').focus();}};
  $('verify-form').onsubmit=async e=>{e.preventDefault();if(await submit('verify',{email,token:$('access-token').value.trim()},e.target)){location.replace('/models');}else $('access-token').value='';};
  $('start-over').onclick=()=>{$('verify-form').hidden=true;$('email-form').hidden=false;$('access-token').value='';$('login-status').textContent='';$('login-description').textContent='Enter your approved email address to receive a temporary access token.';};
})();
