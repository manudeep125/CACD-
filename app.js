function esc(s) { return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

async function analyze(kind) {
  const box = document.getElementById('result');
  const value = document.getElementById(kind + '-input').value.trim();
  box.innerHTML = '<div class="text-center"><div class="spinner-border text-primary"></div></div>';
  try {
    const res = await fetch('/api/analyze/' + kind, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(kind === 'email' ? {text: value} : {url: value})
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
    const bad = data.label === 'Phishing';
    box.innerHTML = `<div class="card shadow-sm result-card ${bad ? 'bad' : 'good'}"><div class="card-body">
      <h3 class="${bad ? 'text-danger' : 'text-success'}">${bad ? '&#9888; Phishing Detected' : '&#10004; Looks Safe'}</h3>
      <div class="progress mb-3"><div class="progress-bar ${bad ? 'bg-danger' : 'bg-success'}" style="width:${data.confidence}%">${data.confidence}%</div></div>
      <h6>Why?</h6><ul class="mb-0">${data.reasons.map(r => `<li>${esc(r)}</li>`).join('')}</ul></div></div>`;
  } catch (e) {
    box.innerHTML = `<div class="alert alert-danger">${esc(e.message)}</div>`;
  }
}
