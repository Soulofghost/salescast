const API_BASE = '/api';

let currentDatasets = [];
let currentDatasetDetail = null;

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initModal();
  initForecastTrigger();
  loadStats();
  loadDatasets();
});

function initTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const target = tab.dataset.tab === 'projections' ? 'paneProjections' : 'paneHistorical';
      document.getElementById(target)?.classList.add('active');
    });
  });
}

function initModal() {
  const modal = document.getElementById('datasetModal');
  const openBtn = document.getElementById('openDatasetModal');
  const closeBtn = document.getElementById('closeDatasetBtn');
  const cancelBtn = document.getElementById('cancelDatasetBtn');
  const form = document.getElementById('createDatasetForm');

  openBtn?.addEventListener('click', () => modal.classList.add('active'));
  closeBtn?.addEventListener('click', () => modal.classList.remove('active'));
  cancelBtn?.addEventListener('click', () => modal.classList.remove('active'));

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('dsName').value.trim();
    const description = document.getElementById('dsDesc').value.trim();

    try {
      const res = await fetch(`${API_BASE}/datasets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description })
      });

      if (!res.ok) throw new Error('Failed to create dataset');
      const data = await res.json();
      modal.classList.remove('active');
      form.reset();
      await loadStats();
      await loadDatasets();
      document.getElementById('datasetSelect').value = data.id;
      await onDatasetChange(data.id);
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  });
}

function initForecastTrigger() {
  const select = document.getElementById('datasetSelect');
  select?.addEventListener('change', () => onDatasetChange(select.value));

  const runBtn = document.getElementById('runForecastBtn');
  runBtn?.addEventListener('click', async () => {
    const dsId = select.value;
    if (!dsId) {
      alert('Please select or create a dataset first.');
      return;
    }
    const model_type = document.getElementById('modelSelect').value;
    const horizon_days = parseInt(document.getElementById('horizonSelect').value, 10);

    runBtn.disabled = true;
    runBtn.innerText = 'Fitting Models...';

    try {
      const res = await fetch(`${API_BASE}/datasets/${dsId}/forecast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_type, horizon_days })
      });

      if (!res.ok) throw new Error('Forecast execution failed');
      const data = await res.json();
      renderForecast(data);
      loadStats();
    } catch (err) {
      alert(err.message);
    } finally {
      runBtn.disabled = false;
      runBtn.innerText = '⚡ Generate Projections';
    }
  });
}

async function onDatasetChange(dsId) {
  if (!dsId) return;
  try {
    const res = await fetch(`${API_BASE}/datasets/${dsId}`);
    if (!res.ok) throw new Error('Failed to fetch dataset');
    currentDatasetDetail = await res.json();
    renderHistoricalData(currentDatasetDetail.records || []);

    // Auto-run forecast
    document.getElementById('runForecastBtn').click();
  } catch (err) {
    console.warn(err);
  }
}

function renderForecast(data) {
  document.getElementById('modelMape').innerText = `${data.mape.toFixed(1)}%`;
  document.getElementById('modelRmse').innerText = `$${data.rmse.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
  document.getElementById('modelMae').innerText = `$${data.mae.toLocaleString(undefined, {minimumFractionDigits: 2})}`;

  const totalProj = data.forecast_points.reduce((acc, p) => acc + p.predicted_revenue, 0);
  document.getElementById('projectedTotal').innerText = `$${totalProj.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
  document.getElementById('activeHorizonBadge').innerText = `${data.horizon_days}-Day Forecast (${data.model_type})`;

  const tbody = document.getElementById('projectionsTableBody');
  tbody.innerHTML = data.forecast_points.map(p => {
    const spread = (p.upper_bound - p.lower_bound).toFixed(2);
    return `
      <tr>
        <td class="text-mono"><strong>${p.date}</strong></td>
        <td style="color: var(--accent-emerald); font-weight:700;">$${p.predicted_revenue.toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
        <td class="text-mono" style="color: var(--text-secondary);">$${p.lower_bound.toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
        <td class="text-mono" style="color: var(--text-secondary);">$${p.upper_bound.toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
        <td class="text-mono">±$${(spread / 2).toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
      </tr>
    `;
  }).join('');
}

function renderHistoricalData(records) {
  document.getElementById('historicalCountBadge').innerText = `${records.length} Records`;
  const tbody = document.getElementById('historicalTableBody');
  if (records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">No historical records available.</td></tr>`;
    return;
  }
  tbody.innerHTML = records.map(r => `
    <tr>
      <td class="text-mono"><strong>${r.date}</strong></td>
      <td style="font-weight:600;">$${r.revenue.toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
      <td>${r.units_sold}</td>
      <td><span class="badge badge-info">${r.channel}</span></td>
    </tr>
  `).join('');
}

async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    const data = await res.json();
    document.getElementById('statDatasets').innerText = data.totalDatasets;
    document.getElementById('statRevenue').innerText = `$${data.totalHistoricalRevenue.toLocaleString(undefined, {maximumFractionDigits: 0})}`;
    document.getElementById('statMape').innerText = `${data.averageModelMAPE.toFixed(1)}%`;
  } catch (err) {
    console.warn('Failed to load stats', err);
  }
}

async function loadDatasets() {
  const select = document.getElementById('datasetSelect');
  try {
    const res = await fetch(`${API_BASE}/datasets`);
    const list = await res.json();
    currentDatasets = list || [];

    if (currentDatasets.length === 0) {
      // Auto seed default dataset
      const seedRes = await fetch(`${API_BASE}/datasets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Enterprise Cloud Subscriptions', description: 'Default seeded recurring sales stream' })
      });
      if (seedRes.ok) {
        return loadDatasets();
      }
    }

    select.innerHTML = currentDatasets.map(d => `<option value="${d.id}">${escapeHtml(d.name)} (${d.data_points_count} days)</option>`).join('');
    if (currentDatasets.length > 0) {
      await onDatasetChange(currentDatasets[0].id);
    }
  } catch (err) {
    select.innerHTML = `<option value="">Error loading datasets</option>`;
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
