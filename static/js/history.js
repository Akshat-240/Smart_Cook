/* ============================================================
   SmartCook — history.js
   Handles: table render, sort, filter, chart, CSV export
   ============================================================ */

/* ---------- Mock Data ---------- */
const ALL_RECORDS = [
  { date: '27 Apr 2026', day: 'Mon', meal: 'lunch',     actual: 182, cooked: 190, wasted: 8,  wastePct: 4.21,  event: 'none' },
  { date: '26 Apr 2026', day: 'Sun', meal: 'lunch',     actual: 110, cooked: 140, wasted: 30, wastePct: 21.43, event: 'weekend' },
  { date: '25 Apr 2026', day: 'Sat', meal: 'lunch',     actual: 120, cooked: 150, wasted: 30, wastePct: 20.00, event: 'weekend' },
  { date: '24 Apr 2026', day: 'Fri', meal: 'lunch',     actual: 185, cooked: 195, wasted: 10, wastePct: 5.13,  event: 'none' },
  { date: '23 Apr 2026', day: 'Thu', meal: 'lunch',     actual: 190, cooked: 200, wasted: 10, wastePct: 5.00,  event: 'none' },
  { date: '22 Apr 2026', day: 'Wed', meal: 'lunch',     actual: 160, cooked: 210, wasted: 50, wastePct: 23.81, event: 'festival' },
  { date: '21 Apr 2026', day: 'Tue', meal: 'lunch',     actual: 175, cooked: 190, wasted: 15, wastePct: 7.89,  event: 'none' },
  { date: '20 Apr 2026', day: 'Mon', meal: 'lunch',     actual: 180, cooked: 200, wasted: 20, wastePct: 10.00, event: 'none' },
];

/* ---------- State ---------- */
let filtered = [...ALL_RECORDS];
let sortKey = 'date';
let sortAsc = false;
let histChart = null;

/* ---------- Init ---------- */
document.addEventListener('DOMContentLoaded', () => {
  updateStats();
  renderTable(filtered);
  initHistoryChart();
});

/* ---------- Stats ---------- */
function updateStats() {
  const total = filtered.length;
  const avgWaste = filtered.reduce((s, r) => s + r.wastePct, 0) / (total || 1);
  const totalWasted = filtered.reduce((s, r) => s + r.wasted, 0);
  const moneyWasted = totalWasted * 346; // ₹346 per kg estimated
  const best = Math.min(...filtered.map(r => r.wastePct));

  document.getElementById('hSessions').textContent = total;
  document.getElementById('hAvgWaste').textContent = avgWaste.toFixed(2) + '%';
  document.getElementById('hMoneyWasted').textContent = '₹' + moneyWasted.toLocaleString('en-IN');
  document.getElementById('hBestDay').textContent = isFinite(best) ? best.toFixed(2) + '%' : '—';
  document.getElementById('recordCount').textContent = `Showing ${total} record${total !== 1 ? 's' : ''}`;
}

/* ---------- Table render ---------- */
function renderTable(rows) {
  const tbody = document.getElementById('historyBody');
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:24px;color:#888">No records match the filters.</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map((r, i) => `
    <tr style="animation: fadeUp 0.25s ${i * 0.04}s ease both; opacity:0; animation-fill-mode:forwards">
      <td class="date-cell">${r.date} <span class="day-label">${r.day}</span></td>
      <td><span class="badge badge-${r.meal}">${cap(r.meal)}</span></td>
      <td>${r.actual}</td>
      <td>${r.cooked}</td>
      <td>${r.wasted}</td>
      <td class="${wasteClass(r.wastePct)}">${r.wastePct.toFixed(2)}%</td>
      <td><span class="badge badge-${r.event}">${r.event}</span></td>
    </tr>
  `).join('');
}

/* ---------- Sort ---------- */
function sortTable(key) {
  if (sortKey === key) sortAsc = !sortAsc;
  else { sortKey = key; sortAsc = false; }

  filtered.sort((a, b) => {
    let va = a[key], vb = b[key];
    if (typeof va === 'string') return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    return sortAsc ? va - vb : vb - va;
  });

  document.querySelectorAll('.sort-icon').forEach(el => el.textContent = '↕');
  event.currentTarget.querySelector('.sort-icon').textContent = sortAsc ? '↑' : '↓';
  renderTable(filtered);
}

/* ---------- Filter ---------- */
function applyFilters() {
  const from  = document.getElementById('filterFrom').value;
  const to    = document.getElementById('filterTo').value;
  const meal  = document.getElementById('filterMeal').value;
  const event = document.getElementById('filterEvent').value;

  filtered = ALL_RECORDS.filter(r => {
    const d = new Date(r.date);
    if (from && d < new Date(from)) return false;
    if (to   && d > new Date(to))   return false;
    if (meal  !== 'all' && r.meal  !== meal)  return false;
    if (event !== 'all' && r.event !== event) return false;
    return true;
  });

  sortKey = 'date'; sortAsc = false;
  updateStats();
  renderTable(filtered);
  updateHistoryChart();
}

function resetFilters() {
  document.getElementById('filterFrom').value = '';
  document.getElementById('filterTo').value   = '';
  document.getElementById('filterMeal').value = 'all';
  document.getElementById('filterEvent').value = 'all';
  filtered = [...ALL_RECORDS];
  sortKey = 'date'; sortAsc = false;
  updateStats();
  renderTable(filtered);
  updateHistoryChart();
}

/* ---------- History chart ---------- */
function initHistoryChart() {
  const ctx = document.getElementById('historyChart').getContext('2d');
  const labels = ALL_RECORDS.map(r => r.date.slice(0, 6)).reverse();
  const wastePcts = ALL_RECORDS.map(r => r.wastePct).reverse();

  histChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Waste %',
        data: wastePcts,
        backgroundColor: wastePcts.map(v =>
          v < 10 ? 'rgba(15,110,86,0.7)' :
          v < 20 ? 'rgba(239,159,39,0.7)' :
                   'rgba(162,45,45,0.7)'
        ),
        borderRadius: 5,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#fff',
          titleColor: '#1a1a18',
          bodyColor: '#6b6b68',
          borderColor: '#e0ddd8',
          borderWidth: 1,
          padding: 10,
          titleFont: { family: "'DM Sans', sans-serif", size: 12 },
          bodyFont:  { family: "'DM Sans', sans-serif", size: 12 },
          callbacks: { label: ctx => ` Waste: ${ctx.parsed.y.toFixed(2)}%` }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { family: "'DM Sans', sans-serif", size: 11 }, color: '#888' } },
        y: {
          grid: { color: 'rgba(0,0,0,0.04)' },
          ticks: { font: { family: "'DM Sans', sans-serif", size: 11 }, color: '#888', callback: v => v + '%' },
          max: 30
        }
      }
    }
  });
}

function updateHistoryChart() {
  if (!histChart) return;
  const rev = [...filtered].reverse();
  histChart.data.labels = rev.map(r => r.date.slice(0, 6));
  const pcts = rev.map(r => r.wastePct);
  histChart.data.datasets[0].data = pcts;
  histChart.data.datasets[0].backgroundColor = pcts.map(v =>
    v < 10 ? 'rgba(15,110,86,0.7)' :
    v < 20 ? 'rgba(239,159,39,0.7)' :
             'rgba(162,45,45,0.7)'
  );
  histChart.update();
}

/* ---------- Export CSV ---------- */
function exportCSV() {
  const headers = ['Date', 'Day', 'Meal', 'Actual', 'Cooked For', 'Wasted', 'Waste %', 'Event'];
  const rows = filtered.map(r => [r.date, r.day, r.meal, r.actual, r.cooked, r.wasted, r.wastePct.toFixed(2), r.event]);
  const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'smartcook_history.csv';
  a.click();
  URL.revokeObjectURL(url);
}

/* ---------- Helpers ---------- */
function wasteClass(pct) {
  if (pct < 10) return 'waste-ok';
  if (pct < 20) return 'waste-warn';
  return 'waste-bad';
}
function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }