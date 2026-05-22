/*
 * Copyright 2025 - 2026 Vu Quang Cuong
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/* ========================================
   WIFI-CENSOR — Charts Configuration
   chart.js 4.x wrappers
   ======================================== */

const CHART_COLORS = {
  purple:     '#6366f1',
  cyan:       '#06b6d4',
  green:      '#10b981',
  amber:      '#f59e0b',
  red:        '#ef4444',
  gridLine:   'rgba(255,255,255,0.05)',
  textMuted:  '#4a5568',
  textSecond: '#8892a4',
};

const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: CHART_COLORS.textSecond,
        font: { family: 'Inter', size: 12 },
        boxWidth: 12, boxHeight: 12,
        padding: 20,
      }
    },
    tooltip: {
      backgroundColor: 'rgba(13,17,23,0.95)',
      borderColor: 'rgba(255,255,255,0.1)',
      borderWidth: 1,
      titleColor: '#f0f4ff',
      bodyColor: CHART_COLORS.textSecond,
      padding: 12,
      titleFont: { family: 'Inter', size: 13, weight: '600' },
      bodyFont:  { family: 'Inter', size: 12 },
      cornerRadius: 10,
    }
  },
  scales: {
    x: {
      grid:  { color: CHART_COLORS.gridLine, drawBorder: false },
      ticks: { color: CHART_COLORS.textMuted, font: { family: 'JetBrains Mono', size: 11 } },
      border: { display: false }
    },
    y: {
      grid:  { color: CHART_COLORS.gridLine, drawBorder: false },
      ticks: { color: CHART_COLORS.textMuted, font: { family: 'JetBrains Mono', size: 11 } },
      border: { display: false }
    }
  }
};

let rssiChartInstance    = null;
let presenceChartInst    = null;
let historyChartInstance = null;

/* ─ RSSI Timeline Chart ─ */
function initRssiChart(labels, rssiData, varianceData) {
  const ctx = document.getElementById('rssiChart');
  if (!ctx) return;
  if (rssiChartInstance) rssiChartInstance.destroy();

  rssiChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'RSSI (dBm)',
          data: rssiData,
          borderColor: CHART_COLORS.cyan,
          backgroundColor: 'rgba(6,182,212,0.08)',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 5,
          fill: true,
          tension: 0.4,
          yAxisID: 'y',
        },
        {
          label: 'Variance',
          data: varianceData,
          borderColor: CHART_COLORS.purple,
          backgroundColor: 'rgba(99,102,241,0.06)',
          borderWidth: 1.5,
          pointRadius: 0,
          pointHoverRadius: 4,
          fill: false,
          tension: 0.4,
          borderDash: [5, 3],
          yAxisID: 'y1',
        }
      ]
    },
    options: {
      ...CHART_DEFAULTS,
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: {
          ...CHART_DEFAULTS.scales.x,
          ticks: {
            ...CHART_DEFAULTS.scales.x.ticks,
            maxTicksLimit: 12,
            maxRotation: 0,
          }
        },
        y: {
          ...CHART_DEFAULTS.scales.y,
          position: 'left',
          title: {
            display: true,
            text: 'RSSI (dBm)',
            color: CHART_COLORS.textSecond,
            font: { family: 'Inter', size: 11 }
          },
          suggestedMin: -90,
          suggestedMax: -30,
        },
        y1: {
          ...CHART_DEFAULTS.scales.y,
          position: 'right',
          grid: { drawOnChartArea: false },
          title: {
            display: true,
            text: 'Variance',
            color: CHART_COLORS.textSecond,
            font: { family: 'Inter', size: 11 }
          },
          suggestedMin: 0,
          suggestedMax: 15,
        }
      }
    }
  });
}

/* ─ Presence Donut Chart ─ */
function initPresenceChart(presentMin, absentMin) {
  const ctx = document.getElementById('presenceChart');
  if (!ctx) return;
  if (presenceChartInst) presenceChartInst.destroy();

  presenceChartInst = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Có mặt', 'Vắng phòng'],
      datasets: [{
        data: [presentMin, absentMin],
        backgroundColor: [
          'rgba(16,185,129,0.8)',
          'rgba(107,114,128,0.4)',
        ],
        borderColor: [
          'rgba(16,185,129,1)',
          'rgba(107,114,128,0.5)',
        ],
        borderWidth: 2,
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%',
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: {
          position: 'bottom',
          labels: {
            color: CHART_COLORS.textSecond,
            font: { family: 'Inter', size: 12 },
            boxWidth: 10, boxHeight: 10, padding: 14,
          }
        },
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: {
            label: (ctx) => ` ${ctx.parsed} phút (${Math.round(ctx.parsed / (presentMin + absentMin || 1) * 100)}%)`
          }
        }
      }
    }
  });
}

/* ─ History Area Chart ─ */
function initHistoryChart(labels, presentData, absentData) {
  const ctx = document.getElementById('historyChart');
  if (!ctx) return;
  if (historyChartInstance) historyChartInstance.destroy();

  historyChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Có mặt (phút)',
          data: presentData,
          backgroundColor: 'rgba(16,185,129,0.7)',
          borderColor:      'rgba(16,185,129,1)',
          borderWidth: 1,
          borderRadius: 6,
          borderSkipped: false,
        },
        {
          label: 'Vắng phòng (phút)',
          data: absentData,
          backgroundColor: 'rgba(107,114,128,0.35)',
          borderColor:      'rgba(107,114,128,0.6)',
          borderWidth: 1,
          borderRadius: 6,
          borderSkipped: false,
        }
      ]
    },
    options: {
      ...CHART_DEFAULTS,
      scales: {
        x: CHART_DEFAULTS.scales.x,
        y: {
          ...CHART_DEFAULTS.scales.y,
          stacked: false,
          title: {
            display: true,
            text: 'Phút',
            color: CHART_COLORS.textSecond,
            font: { family: 'Inter', size: 11 }
          }
        }
      }
    }
  });
}

/* ─ Update RSSI chart with streaming data point ─ */
function appendRssiPoint(label, rssiVal, varianceVal) {
  if (!rssiChartInstance) return;
  const maxPoints = 120;
  const ds = rssiChartInstance.data;
  ds.labels.push(label);
  ds.datasets[0].data.push(rssiVal);
  ds.datasets[1].data.push(varianceVal);
  if (ds.labels.length > maxPoints) {
    ds.labels.shift();
    ds.datasets[0].data.shift();
    ds.datasets[1].data.shift();
  }
  rssiChartInstance.update('none');
}
