
let currentId=null;
async function loadList(q=''){
  const r = await fetch('/api/templates?q='+encodeURIComponent(q));
  const items = await r.json();
  const ul = document.getElementById('list'); ul.innerHTML='';
  items.forEach(t=>{
    const li=document.createElement('li');
    li.innerHTML = `<div class="card" style="cursor:pointer"><b>${t.title}</b><div style='color:#a9b6c5;font-size:12px'>/${t.slug}</div></div>`;
    li.onclick=()=>{ currentId=t.id; fill(t); };
    ul.appendChild(li);
  });
}
function fill(t){ document.getElementById('title').value=t.title||''; document.getElementById('slug').value=t.slug||''; document.getElementById('icd').value=t.icd||''; document.getElementById('snomed').value=t.snomed||''; document.getElementById('body').value=t.body||''; }
document.getElementById('q').addEventListener('input', e=>loadList(e.target.value));
document.getElementById('newBtn').addEventListener('click', ()=>{ currentId=null; fill({}); });
document.getElementById('save').addEventListener('click', async ()=>{
  const t=collect(); const r= await fetch('/api/templates', {method: currentId?'PUT':'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({...t, id: currentId})}); await loadList();
});
document.getElementById('submit').addEventListener('click', ()=>alert('Submit would trigger review workflow in a real system.'));
document.getElementById('publish').addEventListener('click', async ()=>{
  const t=collect(); const r= await fetch('/api/templates/publish', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(t)});
  alert('Published! Now accessible from Assessment → Insert Template(s).');
});
function collect(){ return { title: val('title'), slug: val('slug'), icd: val('icd'), snomed: val('snomed'), body: val('body') }; }
function val(id){return document.getElementById(id).value.trim()}
loadList();
