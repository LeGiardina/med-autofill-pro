
async function extract() {
  const text = document.getElementById('transcript').value.trim();
  const r = await fetch('/api/extract', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text})});
  const data = await r.json();
  // fill fields
  (v=>document.getElementById('cc').value=v||'')(data.subjective?.cc);
  (v=>document.getElementById('hpi').value=v||'')(data.subjective?.hpi);
  (v=>document.getElementById('ros').value=v||'')(data.subjective?.ros);
  const o=data.objective||{};
  ['bp_sys','bp_dia','hr','rr','temp','spo2','exam','labs','imaging'].forEach(k=>{ if(o[k]) document.getElementById(k).value=o[k]; });
  // diagnoses
  const dx = (data.diagnoses || []).map(d=>({code:d.code || '', name:d.name || d}));
  const sel = document.getElementById('diagnoses'); sel.innerHTML='';
  dx.forEach(d=>{const opt=document.createElement('option'); opt.value=d.code||d.name; opt.textContent=d.name; sel.appendChild(opt);});
  // plan
  if(data.plan) document.getElementById('plan').value = data.plan;
}
document.getElementById('extractBtn').addEventListener('click', extract);
document.getElementById('micBtn').addEventListener('click', async ()=>{
  alert('Mic recording uses browser MediaRecorder; keep using transcript box for now.');
});
document.getElementById('insertTemplates').addEventListener('click', async ()=>{
  const dx = Array.from(document.getElementById('diagnoses').selectedOptions).map(o=>o.textContent);
  const r = await fetch('/api/templates/for-dx', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({diagnoses: dx})});
  const t = await r.json();
  const plan = document.getElementById('plan'); plan.value += "\n\n" + (t.join("\n\n") || '');
});
