let monitoring = false;

const toggleBtn = document.getElementById('toggleBtn');
const cpuEl = document.getElementById('cpu');
const memEl = document.getElementById('mem');
const blockedEl = document.getElementById('blocked');
const processList = document.getElementById('processList');
const connList = document.getElementById('connList');
const threatList = document.getElementById('threatList');
const urlInput = document.getElementById('urlInput');
const checkResult = document.getElementById('checkResult');
const monitoredList = document.getElementById('monitoredList');

/* ---------- URL MONITORING FUNCTIONS ---------- */
async function checkUrl() {
  const url = urlInput.value.trim();
  if (!url) {
    checkResult.textContent = '⚠️ Enter a URL';
    checkResult.style.color = '#f55';
    return;
  }
  
  checkResult.textContent = '🔍 Checking...';
  checkResult.style.color = '#4a5';
  
  try {
    const res = await fetch('/api/check-url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const data = await res.json();
    
    if (data.status === 'SAFE') {
      checkResult.textContent = '✅ URL is SAFE - No threats detected';
      checkResult.style.color = '#4f4';
    } else {
      checkResult.textContent = `🚨 THREAT DETECTED - ${data.threats[0]?.threatType || 'Unknown threat'}`;
      checkResult.style.color = '#f55';
    }
  } catch (e) {
    checkResult.textContent = '❌ Error checking URL (API key configured?)';
    checkResult.style.color = '#f55';
  }
}

async function addDomain() {
  const url = urlInput.value.trim();
  if (!url) {
    checkResult.textContent = '⚠️ Enter a URL';
    return;
  }
  
  try {
    const res = await fetch('/api/add-domain', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const data = await res.json();
    
    if (data.status === 'THREAT_DETECTED') {
      checkResult.textContent = `🚨 THREAT DETECTED while adding - Not added to monitoring`;
      checkResult.style.color = '#f55';
    } else {
      checkResult.textContent = `✅ Added to monitoring: ${url}`;
      checkResult.style.color = '#4f4';
      urlInput.value = '';
      loadMonitoredDomains();
    }
  } catch (e) {
    checkResult.textContent = '❌ Error adding domain';
  }
}

async function removeDomain(url) {
  try {
    await fetch('/api/remove-domain', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    loadMonitoredDomains();
  } catch (e) {
    console.error(e);
  }
}

async function loadMonitoredDomains() {
  try {
    const res = await fetch('/api/monitored-domains');
    const data = await res.json();
    
    monitoredList.innerHTML = '';
    if (data.domains.length === 0) {
      monitoredList.innerHTML = '<p style="color: #666;">No domains monitored yet</p>';
    } else {
      data.domains.forEach(domain => {
        monitoredList.innerHTML += `
          <div class="card" style="display: flex; justify-content: space-between; align-items: center;">
            <span>${domain}</span>
            <button onclick="removeDomain('${domain}')" style="background: #f55; border: none; color: white; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Remove</button>
          </div>
        `;
      });
    }
  } catch (e) {
    console.error(e);
  }
}

// Load monitored domains on startup
loadMonitoredDomains();

/* ---------- UI HELPERS ---------- */
const badge = (text, type) =>
  `<span class="badge ${type}">${text}</span>`;

const animateStat = (el, value, suffix = '') => {
  el.classList.add('stat-flash');
  el.textContent = value + suffix;
  setTimeout(() => el.classList.remove('stat-flash'), 300);
};

const card = (html, danger = false) =>
  `<div class="card ${danger ? 'danger-glow' : ''}">${html}</div>`;

/* ---------- TOGGLE ---------- */
toggleBtn.addEventListener('click', async () => {
  toggleBtn.classList.add('btn-loading');
  const url = monitoring ? '/api/stop' : '/api/start';
  await fetch(url, { method: 'POST' });
  monitoring = !monitoring;
  toggleBtn.textContent = monitoring ? '🛑 Stop Protection' : '🟢 Start Protection';
  toggleBtn.classList.remove('btn-loading');
});

/* ---------- FETCH STATUS ---------- */
async function fetchStatus() {
  try {
    const res = await fetch('/api/status');
    if (!res.ok) return;
    const data = await res.json();

    /* ---- STATS ---- */
    animateStat(cpuEl, data.systemStats.cpuUsage, '%');
    animateStat(memEl, data.systemStats.memoryUsage, '%');
    animateStat(blockedEl, data.systemStats.blockedThreats);

    /* ---- PROCESSES ---- */
    processList.innerHTML = '';
    data.activeProcesses.forEach(p => {
      processList.innerHTML += card(`
        <div class="row">
          <div>
            <div class="title">${p.name}</div>
            <div class="sub mono">PID ${p.pid} · CPU ${p.cpu}%</div>
          </div>
          ${p.isSuspicious ? badge('THREAT', 'danger') : badge('SAFE', 'safe')}
        </div>
      `, p.isSuspicious);
    });

    /* ---- CONNECTIONS ---- */
    connList.innerHTML = '';
    data.networkConnections.forEach(c => {
      connList.innerHTML += card(`
        <div class="row">
          <div>
            <div class="title">${c.domain}</div>
            <div class="sub mono">${c.ip}:${c.port}</div>
          </div>
          ${c.status === 'blocked'
            ? badge('BLOCKED', 'danger')
            : badge('ALLOWED', 'safe')}
        </div>
      `, c.status === 'blocked');
    });

    /* ---- THREATS ---- */
    threatList.innerHTML = '';
    data.threats.slice(0, 15).forEach(t => {
      threatList.innerHTML += `
        <div class="threat-card ${t.severity}">
          <div class="threat-head">
            🚨 ${t.severity.toUpperCase()}
            <span class="time">${t.time}</span>
          </div>
          <div class="threat-body">${t.description}</div>
        </div>
      `;
    });

    monitoring = data.monitoring;
    toggleBtn.textContent = monitoring ? '🛑 Stop Protection' : '🟢 Start Protection';

  } catch (e) {
    console.error(e);
  }
}

setInterval(fetchStatus, 2000);
fetchStatus();