const logEl = () => document.getElementById('log');
const filesEl = () => document.getElementById('files');

function getSessionId() {
  return document.getElementById('sessionId').value.trim() || 'demo_session_001';
}

function appendLog(message) {
  const now = new Date().toLocaleTimeString();
  logEl().textContent += `\n[${now}] ${message}`;
}

async function runTask(endpoint, payload) {
  appendLog(`POST ${endpoint}`);
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    appendLog(JSON.stringify(data, null, 2));
    if (data.job_id) {
      await pollJob(data.job_id);
    }
    await refreshFiles();
  } catch (error) {
    appendLog(`ERROR: ${error.message}`);
  }
}

async function pollJob(jobId) {
  for (let i = 0; i < 60; i += 1) {
    const response = await fetch(`/api/jobs/${jobId}`);
    const job = await response.json();
    appendLog(`job ${jobId}: ${job.status}`);
    if (job.status === 'finished' || job.status === 'failed') {
      if (job.log) appendLog(job.log.join('\n'));
      return job;
    }
    await new Promise((resolve) => setTimeout(resolve, 800));
  }
  appendLog(`job ${jobId}: polling timeout`);
}

async function refreshFiles() {
  try {
    const response = await fetch(`/api/files/${getSessionId()}`);
    const data = await response.json();
    filesEl().innerHTML = '';
    for (const file of data.files || []) {
      const li = document.createElement('li');
      li.textContent = file;
      filesEl().appendChild(li);
    }
  } catch (error) {
    appendLog(`File refresh failed: ${error.message}`);
  }
}

async function checkHealth() {
  try {
    const response = await fetch('/api/health');
    const data = await response.json();
    appendLog(`Backend ready: ${data.status}`);
  } catch (error) {
    appendLog('Backend health check failed. Is FastAPI running?');
  }
}

window.addEventListener('load', () => {
  checkHealth();
  refreshFiles();
});
