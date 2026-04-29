/* ============================================================
   SmartCook — dashboard.js
   Handles: prediction display, meal switcher, chart, mini-table
   In production: replace mock data with fetch() calls to Flask API
   ============================================================ */

/* ---------- Mock Data (replace with Flask API calls) ---------- */
const MOCK = {
  breakfast: {
    headcount: 142, meal: 'Breakfast', sub: 'Normal Wednesday · No special events',
    rice: '28.4 kg', dal: '17.1 L', roti: '284 pcs', sabzi: '14.2 kg',
    saving: '₹1,130', avg7: 138, vsYest: +4,
    event: null, capacity: 250,
    riskPct: 12, riskLabel: 'Low', riskTip: 'Steady weekday — normal attendance expected.'
  },
  lunch: {
    headcount: 164, meal: 'Lunch', sub: 'Normal Wednesday · No special events',
    rice: '32.8 kg', dal: '21.3 L', roti: '328 pcs', sabzi: '16.4 kg',
    saving: '₹1,298', avg7: 171, vsYest: +5,
    event: null, capacity: 250,
    riskPct: 18, riskLabel: 'Low', riskTip: 'Normal weekday — steady attendance expected.'
  },
  dinner: {
    headcount: 198, meal: 'Dinner', sub: 'Normal Wednesday · No special events',
    rice: '39.6 kg', dal: '25.7 L', roti: '396 pcs', sabzi: '19.8 kg',
    saving: '₹1,540', avg7: 195, vsYest: -3,
    event: null, capacity: 250,
    riskPct: 22, riskLabel: 'Low', riskTip: 'Dinner sees peak attendance — prepare accordingly.'
  }
};

const CHART_DATA_7 = {
  labels: ['20 Apr', '21 Apr', '22 Apr', '23 Apr', '24 Apr', '25 Apr', '26 Apr', '27 Apr'],
  actual:  [105, 98, 80, 103, 100, 75, 72, 100],
  optimal: [95, 92, 68, 98, 95, 60, 65, 96]
};
const CHART_DATA_14 = {
  labels: ['14 Apr','15 Apr','16 Apr','17 Apr','18 Apr','19 Apr','20 Apr','21 Apr','22 Apr','23 Apr','24 Apr','25 Apr','26 Apr','27 Apr'],
  actual:  [110, 105, 95, 108, 103, 78, 105, 98, 80, 103, 100, 75, 72, 100],
  optimal: [100, 97, 88, 100, 96, 65, 95, 92, 68, 98, 95, 60, 65, 96]
};

const MINI_ROWS = [
  { date: '27 Apr 2026', day: 'Mon', meal: 'Lunch', predicted: 182, actual: 182, wasted: 8, wastePct: 4.21, event: 'none' },
  { date: '26 Apr 2026', day: 'Sun', meal: 'Lunch', predicted: 130, actual: 110, wasted: 30, wastePct: 21.43, event: 'weekend' },
  { date: '25 Apr 2026', day: 'Sat', meal: 'Lunch', predicted: 140, actual: 120, wasted: 30, wastePct: 20.00, event: 'weekend' },
  { date: '24 Apr 2026', day: 'Fri', meal: 'Lunch', predicted: 185, actual: 185, wasted: 10, wastePct: 5.13, event: 'none' },
];

/* ---------- State ---------- */
let currentMeal = 'lunch';
let wasteChart = null;
let chartRange = 7;

/* ---------- Init ---------- */
document.addEventListener('DOMContentLoaded', () => {
  setContextDate();
  updateDashboard('lunch');
  initChart(CHART_DATA_7);
  renderMiniTable();
  bindMealSwitcher();
  bindChartToggle();
});

/* ---------- Date ---------- */
function setContextDate() {
  const now = new Date();
  const opts = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
  document.getElementById('contextDate').textContent = now.toLocaleDateString('en-IN', opts);
}

/* ---------- Dashboard update ---------- */
function updateDashboard(meal) {
  const d = MOCK[meal];
  currentMeal = meal;

  /* Hero */
  animateNumber('heroCount', parseInt(document.getElementById('heroCount').textContent) || 0, d.headcount);
  document.getElementById('heroMeal').textContent = d.meal;
  document.getElementById('heroSub').textContent = d.sub;
  const pct = Math.round((d.headcount / d.capacity) * 100);
  document.getElementById('heroBar').style.width = pct + '%';
  document.getElementById('heroCapacity').textContent = 'Capacity: ' + d.capacity;

  /* Stats */
  document.getElementById('stat7day').textContent = d.avg7;
  const diff = d.vsYest;
  const vsEl = document.getElementById('statVsYest');
  vsEl.textContent = (diff > 0 ? '+' : '') + diff;
  vsEl.style.color = diff >= 0 ? 'var(--green-700)' : 'var(--red-700)';
  document.getElementById('statSaving').textContent = d.saving;

  /* Cooking quantities */
  document.getElementById('qRiceVal').textContent = d.rice;
  document.getElementById('qDalVal').textContent = d.dal;
  document.getElementById('qRotiVal').textContent = d.roti;
  document.getElementById('qSabziVal').textContent = d.sabzi;

  /* Risk */
  const riskFill = document.getElementById('riskFill');
  const riskLevel = document.getElementById('riskLevel');
  const riskTip = document.getElementById('riskTip');
  riskFill.style.width = d.riskPct + '%';
  riskLevel.textContent = d.riskLabel;
  riskTip.textContent = d.riskTip;
  riskFill.className = 'risk-bar-fill' + (d.riskLabel === 'Medium' ? ' medium' : d.riskLabel === 'High' ? ' high' : '');
  riskLevel.className = 'risk-level' + (d.riskLabel === 'Medium' ? ' medium' : d.riskLabel === 'High' ? ' high' : '');

  /* Event banner */
  if (d.event) {
    const banner = document.getElementById('eventBanner');
    document.getElementById('bannerText').textContent =
      d.event === 'festival' ? 'Festival day detected — attendance may drop significantly.' :
      d.event === 'exam' ? 'Exam period — attendance patterns may vary.' : '';
    banner.classList.remove('hidden');
  }

  /* Context pill */
  document.getElementById('contextPill').textContent = d.event ? d.event.charAt(0).toUpperCase() + d.event.slice(1) + ' day' : 'Normal day';
}

/* ---------- Animated number counter ---------- */
function animateNumber(id, from, to) {
  const el = document.getElementById(id);
  const duration = 600;
  const start = performance.now();
  function step(now) {
    const t = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = Math.round(from + (to - from) * eased);
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

/* ---------- Meal switcher ---------- */
function bindMealSwitcher() {
  document.querySelectorAll('.meal-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.meal-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      updateDashboard(btn.dataset.meal);
    });
  });
}

/* ---------- Chart ---------- */
function initChart(data) {
  const ctx = document.getElementById('wasteChart').getContext('2d');
  if (wasteChart) wasteChart.destroy();

  wasteChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [
        {
          label: 'Actual cooked (kg)',
          data: data.actual,
          borderColor: '#0F6E56',
          backgroundColor: 'rgba(15,110,86,0.08)',
          borderWidth: 2.5,
          pointRadius: 5,
          pointBackgroundColor: '#fff',
          pointBorderColor: '#0F6E56',
          pointBorderWidth: 2,
          tension: 0.4,
          fill: true
        },
        {
          label: 'Optimal required (kg)',
          data: data.optimal,
          borderColor: '#5DCAA5',
          backgroundColor: 'transparent',
          borderWidth: 2,
          borderDash: [5, 4],
          pointRadius: 4,
          pointBackgroundColor: '#fff',
          pointBorderColor: '#5DCAA5',
          pointBorderWidth: 2,
          tension: 0.4,
        }
      ]
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            font: { family: "'DM Sans', sans-serif", size: 12 },
            color: '#6b6b68',
            boxWidth: 14,
            usePointStyle: true,
            pointStyle: 'rectRounded'
          }
        },
        tooltip: {
          backgroundColor: '#fff',
          titleColor: '#1a1a18',
          bodyColor: '#6b6b68',
          borderColor: '#e0ddd8',
          borderWidth: 1,
          padding: 12,
          titleFont: { family: "'DM Sans', sans-serif", size: 13, weight: '500' },
          bodyFont: { family: "'DM Sans', sans-serif", size: 12 },
          callbacks: {
            label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y} kg`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(0,0,0,0.04)' },
          ticks: { font: { family: "'DM Sans', sans-serif", size: 11 }, color: '#888' }
        },
        y: {
          grid: { color: 'rgba(0,0,0,0.04)' },
          ticks: { font: { family: "'DM Sans', sans-serif", size: 11 }, color: '#888' },
          title: { display: true, text: 'Total weight (kg)', font: { size: 11 }, color: '#888' }
        }
      }
    }
  });
}

function bindChartToggle() {
  document.querySelectorAll('.ctbtn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.ctbtn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      chartRange = parseInt(btn.dataset.range);
      initChart(chartRange === 7 ? CHART_DATA_7 : CHART_DATA_14);
    });
  });
}

/* ---------- Mini Table ---------- */
function renderMiniTable() {
  const tbody = document.getElementById('miniTableBody');
  tbody.innerHTML = MINI_ROWS.map(r => `
    <tr>
      <td>${r.date} <span style="font-size:11px;color:#888">${r.day}</span></td>
      <td><span class="badge badge-${r.meal.toLowerCase()}">${r.meal}</span></td>
      <td>${r.actual}</td>
      <td>${r.predicted}</td>
      <td class="${wasteClass(r.wastePct)}">${r.wastePct.toFixed(2)}%</td>
      <td><span class="badge badge-${r.event}">${r.event}</span></td>
    </tr>
  `).join('');
}

function wasteClass(pct) {
  if (pct < 10) return 'waste-ok';
  if (pct < 20) return 'waste-warn';
  return 'waste-bad';
}

/* ============================================================
   TO CONNECT TO FLASK API — replace mock data above with:

   async function fetchPrediction(meal) {
     const res = await fetch(`/predict?meal=${meal}&date=${getDate()}`);
     const data = await res.json();
     return data;
   }
   ============================================================ */