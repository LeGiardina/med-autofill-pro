
const tabEls = document.querySelectorAll('.tab');
const panes = {note: 't-note', email: 't-email', codes: 't-codes', transcript: 't-transcript'};
tabEls.forEach(t => t.addEventListener('click', () => {
  tabEls.forEach(x=>x.classList.remove('active')); t.classList.add('active');
  Object.values(panes).forEach(id => document.getElementById(id).style.display='none');
  const key = t.dataset.t; document.getElementById(panes[key]).style.display='block';
}));

async function extract(){
  const text = document.getElementById('transcript').value;
  const r = await fetch('/api/extract',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});
  const d = await r.json();
  fill(d);
  document.getElementById('email').value = d.email || '';
  const codes = (d.codes||[]).map(c=>`<li>${c.code} — ${c.name}</li>`).join('');
  document.getElementById('codes').innerHTML = codes;
}
function fill(d){
  const s=d.subjective||{}, o=d.objective||{};
  document.getElementById('cc').value=s.cc||'';
  document.getElementById('hpi').value=s.hpi||'';
  document.getElementById('ros').value=s.ros||'';
  ['bp_sys','bp_dia','hr','rr','temp','spo2','exam','labs','imaging'].forEach(k=>{ if(o[k]) document.getElementById(k).value=o[k]; });
  if(d.plan) document.getElementById('plan').value=d.plan;
}
document.getElementById('extract').onclick=extract;

// Mic stub
document.getElementById('startMic').onclick=()=>alert('Mic start (wire to MediaRecorder)');
document.getElementById('stopMic').onclick=()=>alert('Mic stop');

// Template insert
document.getElementById('insertTemplates').onclick=async()=>{
  const r = await fetch('/api/templates/for-dx',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({diagnoses:['pneumonia']})});
  const t = await r.json(); document.getElementById('plan').value += '\n\n'+t.join('\n\n');
};

// Push to EHR (FHIR hook)
document.getElementById('pushFHIR').onclick=async()=>{
  const payload = {
    resourceType: 'Observation',
    code: {text:'Clinical Note'},
    valueString: document.getElementById('plan').value || ''
  };
  const r = await fetch('/api/emr/fhir/Observation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const d = await r.json(); alert('Pushed to FHIR sandbox: '+(d.id||JSON.stringify(d)));
};

// Simple chat to backend assistant
document.getElementById('ask').onclick=async()=>{
  const q = document.getElementById('q').value.trim(); if(!q) return;
  const chat = document.getElementById('chat');
  chat.insertAdjacentHTML('beforeend', `<div class="msg user">${q}</div>`);
  const r = await fetch('/api/assistant',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({q})});
  const d = await r.json(); chat.insertAdjacentHTML('beforeend', `<div class="msg">${d.a||'...'}</div>`);
};
