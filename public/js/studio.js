
let current=null;
async function reload(q=''){
  const r = await fetch('/api/templates?q='+encodeURIComponent(q)); const items = await r.json();
  const list = document.getElementById('list'); list.innerHTML='';
  items.forEach(t=>{const li=document.createElement('li'); li.className='item'; li.innerHTML=`<span>${t.title}</span><span>›</span>`; li.onclick=()=>{current=t; fill(t)}; list.appendChild(li)});
}
function fill(t){ title.value=t.title||''; slug.value=t.slug||''; icd.value=t.icd||''; body.value=t.body||''; }
document.getElementById('add').onclick=()=>{current=null; fill({})};
document.getElementById('save').onclick=async()=>{
  const t={title:title.value, slug:slug.value, icd:icd.value, body:body.value, id: current&&current.id};
  const method = current?'PUT':'POST'; await fetch('/api/templates',{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(t)}); reload();
};
document.getElementById('publish').onclick=async()=>{
  const t={title:title.value, slug:slug.value, icd:icd.value, body:body.value}; await fetch('/api/templates/publish',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(t)});
  alert('Published');
};
reload();
