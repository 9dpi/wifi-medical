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
   WIFI-CENSOR — Dashboard App Logic
   Fetches JSON from Google Drive, renders
   real-time status, charts, and timeline.
   ======================================== */


'use strict';

/* ─── CONFIG ─────────────────────────────── */
const CONFIG_KEY   = 'wificensor_config';
const DEFAULT_CFG  = {
  driveUrl:        '',
  refreshInterval: 60,   // seconds
};

let config       = loadConfig();
let refreshTimer = null;
let isConnected  = false;

/* ─── DEMO / FALLBACK DATA ────────────────── */
/* Used when Google Drive is not yet configured */
function generateDemoData() {
  const now   = new Date();
  const hours = [];
  const rssi  = [];
  const variance = [];

  for (let i = 23; i >= 0; i--) {
    const t = new Date(now - i * 3600000);
    hours.push(`${String(t.getHours()).padStart(2,'0')}:00`);
    // Simulate presence pattern: up at 7, out 10-12, home 13-23
    const h = t.getHours();
    const present = h >= 7 && !(h >= 10 && h < 12);
    rssi.push(present ? -55 + (Math.random() - 0.5) * 12 : -75 + (Math.random() - 0.5) * 4);
    variance.push(present ? 4 + Math.random() * 5 : 0.3 + Math.random() * 0.8);
  }

  const timeline = [
    { time: '07:12', status: 'present', event: 'Phát hiện có người',      sub: 'Bắt đầu ngày mới' },
    { time: '10:05', status: 'absent',  event: 'Ra khỏi phòng',           sub: 'Vắng phòng' },
    { time: '12:48', status: 'present', event: 'Trở về',                  sub: 'Nghỉ trưa' },
    { time: '13:30', status: 'present', event: 'Đang ngồi yên',           sub: 'Có thể đang làm việc' },
    { time: '18:20', status: 'alert',   event: '⚠️ Bất động 45 phút',     sub: 'Kiểm tra sức khỏe' },
    { time: '19:10', status: 'present', event: 'Di chuyển bình thường',   sub: 'Đã hoạt động trở lại' },
  ];

  return {
    lastUpdated:  now.toISOString(),
    roomStatus:   'PRESENT',
    confidence:   0.89,
    activity:     'STATIONARY',
    rssiVariance: 3.8,
    rssiCurrent:  -58,
    timeline,
    alerts:       [],
    stats: { presentMinutes: 487, absentMinutes: 153 },
    history: {
      labels:  ['T2','T3','T4','T5','T6','T7','CN'],
      present: [520, 480, 550, 410, 500, 620, 700],
      absent:  [100, 140, 70,  210, 120, 60,  20],
    },
    rssiHistory: { labels: hours, rssi, variance }
  };
}

/* ─── CONFIG PERSISTENCE ─────────────────── */
function loadConfig() {
  try {
    return { ...DEFAULT_CFG, ...JSON.parse(localStorage.getItem(CONFIG_KEY) || '{}') };
  } catch { return { ...DEFAULT_CFG }; }
}
function saveConfig(cfg) {
  localStorage.setItem(CONFIG_KEY, JSON.stringify(cfg));
  config = cfg;
}

/* ─── DATA FETCHING ──────────────────────── */
async function fetchData() {
  if (!config.driveUrl) {
    return generateDemoData();
  }
  try {
    const res = await fetch(config.driveUrl, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[WifiCensor] Fetch failed, using demo data:', err);
    setConnectionState(false);
    return generateDemoData();
  }
}

function setConnectionState(connected) {
  isConnected = connected;
  const badge = document.getElementById('connectionBadge');
  const text  = document.getElementById('connectionText');
  if (connected) {
    badge.className = 'connection-badge connected';
    text.textContent = 'Đã kết nối';
  } else {
    badge.className = config.driveUrl ? 'connection-badge error' : 'connection-badge';
    text.textContent = config.driveUrl ? 'Không kết nối được' : 'Chưa cấu hình';
  }
}

/* ─── RENDER ─────────────────────────────── */
async function refreshData() {
  const data = await fetchData();

  if (config.driveUrl) {
    setConnectionState(true);
  } else {
    setConnectionState(false);
  }

  renderStatus(data);
  renderTimeline(data.timeline || []);
  renderAlerts(data.alerts || []);

  // Charts
  if (data.rssiHistory) {
    initRssiChart(data.rssiHistory.labels, data.rssiHistory.rssi, data.rssiHistory.variance);
  }
  initPresenceChart(data.stats?.presentMinutes || 0, data.stats?.absentMinutes || 0);

  if (data.history) {
    initHistoryChart(data.history.labels, data.history.present, data.history.absent);
  }

  // Update variance badge
  const varianceBadge = document.getElementById('rssiVarianceBadge');
  if (varianceBadge) varianceBadge.textContent = `Variance: ${(data.rssiVariance || 0).toFixed(1)}`;

  // Last updated
  updateTimestamp(data.lastUpdated);
}

function renderStatus(data) {
  const hero      = document.getElementById('statusHero');
  const label     = document.getElementById('statusLabel');
  const sublabel  = document.getElementById('statusSublabel');
  const fill      = document.getElementById('confidenceFill');
  const confVal   = document.getElementById('confidenceValue');
  const icon      = document.getElementById('beaconIcon');

  const present   = document.getElementById('presentMinutes');
  const absent    = document.getElementById('absentMinutes');
  const rssi      = document.getElementById('rssiValue');

  const status     = (data.roomStatus || 'UNKNOWN').toUpperCase();
  const activity   = (data.activity   || '').toUpperCase();
  const confidence = Math.round((data.confidence || 0) * 100);

  // Hero class
  hero.className = 'status-hero';
  if      (status === 'PRESENT' && activity !== 'FALL') hero.classList.add('present');
  else if (status === 'ABSENT')                          hero.classList.add('absent');
  else if (status === 'ALERT')                           hero.classList.add('alert');
  else if (status === 'DANGER' || activity === 'FALL')   hero.classList.add('danger');

  // Labels
  const statusMap = {
    PRESENT: '🟢 Có người trong phòng',
    ABSENT:  '⚪ Vắng phòng',
    ALERT:   '🟡 Cảnh báo',
    DANGER:  '🔴 Khẩn cấp',
    UNKNOWN: '❓ Đang phân tích...',
  };
  const activityMap = {
    WALKING:    '🚶 Đang di chuyển',
    STATIONARY: '🪑 Đang ngồi / nằm nghỉ',
    SLEEPING:   '😴 Có thể đang ngủ',
    MOVING:     '🏃 Đang hoạt động',
    FALL:       '⚠️ Phát hiện ngã — cần kiểm tra!',
    '':         'Đang quan sát...',
  };

  label.textContent    = statusMap[status]   || status;
  sublabel.textContent = activityMap[activity] || activity;

  // Beacon icon
  const iconMap = { PRESENT: '👤', ABSENT: '🏠', ALERT: '⚠️', DANGER: '🆘', UNKNOWN: '📡' };
  icon.textContent = iconMap[status] || '📡';

  // Confidence bar
  fill.style.width    = `${confidence}%`;
  confVal.textContent = `${confidence}%`;

  // Stats
  present.textContent = data.stats?.presentMinutes ?? '--';
  absent.textContent  = data.stats?.absentMinutes  ?? '--';
  rssi.textContent    = data.rssiCurrent ? `${data.rssiCurrent}` : '--';
}

function renderTimeline(events) {
  const container = document.getElementById('activityTimeline');
  if (!events.length) {
    container.innerHTML = '<div class="no-alerts"><span class="no-alerts-icon">📭</span><span>Chưa có sự kiện nào hôm nay</span></div>';
    return;
  }
  container.innerHTML = events.map(e => `
    <div class="timeline-item">
      <div class="timeline-dot ${e.status || 'absent'}"></div>
      <div class="timeline-time">${e.time}</div>
      <div>
        <div class="timeline-event">${e.event}</div>
        ${e.sub ? `<div class="timeline-sub">${e.sub}</div>` : ''}
      </div>
    </div>
  `).join('');
}

function renderAlerts(alerts) {
  const container = document.getElementById('alertsList');
  if (!alerts.length) {
    container.innerHTML = `
      <div class="no-alerts">
        <span class="no-alerts-icon">✅</span>
        <span>Không có cảnh báo</span>
      </div>`;
    return;
  }
  container.innerHTML = alerts.map(a => `
    <div class="alert-item ${a.level || 'warn'}">
      <span>${a.level === 'danger' ? '🔴' : '🟡'}</span>
      <div>
        <div style="font-weight:600">${a.title}</div>
        <div style="font-size:12px;color:var(--text-secondary)">${a.message} · ${a.time}</div>
      </div>
    </div>
  `).join('');
}

function updateTimestamp(iso) {
  const el  = document.getElementById('lastUpdate');
  if (!iso) { el.textContent = '--'; return; }
  const d   = new Date(iso);
  const now = new Date();
  const diff = Math.round((now - d) / 60000);
  if (diff < 1)        el.textContent = 'Vừa cập nhật';
  else if (diff < 60)  el.textContent = `${diff} phút trước`;
  else                 el.textContent = d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
}

/* ─── TAB NAVIGATION ─────────────────────── */
function switchTab(name) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.getElementById(`tab-${name}`)?.classList.add('active');
  document.getElementById(`panel-${name}`)?.classList.add('active');
}

/* ─── SETTINGS ───────────────────────────── */
function saveSettings() {
  const url      = document.getElementById('driveUrl')?.value.trim()    || '';
  const interval = parseInt(document.getElementById('refreshInterval')?.value) || 60;

  saveConfig({ driveUrl: url, refreshInterval: interval });
  startAutoRefresh();
  refreshData();

  const btn = document.querySelector('.btn-primary');
  const orig = btn.textContent;
  btn.textContent = '✅ Đã lưu!';
  setTimeout(() => btn.textContent = orig, 2000);
}

/* Restore settings UI */
function restoreSettingsUI() {
  const urlInput = document.getElementById('driveUrl');
  const intSel   = document.getElementById('refreshInterval');
  if (urlInput) urlInput.value = config.driveUrl || '';
  if (intSel)   intSel.value  = String(config.refreshInterval || 60);
}

/* ─── AUTO REFRESH ───────────────────────── */
function startAutoRefresh() {
  if (refreshTimer) clearInterval(refreshTimer);
  const interval = (config.refreshInterval || 60) * 1000;
  refreshTimer = setInterval(refreshData, interval);
  document.getElementById('footerRefresh').textContent =
    `Auto-refresh: ${config.refreshInterval}s`;
}

/* ─── HISTORY PERIOD ─────────────────────── */
function selectPeriod(days, btn) {
  document.querySelectorAll('.date-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  // In a real app, fetch data for the selected period
  refreshData();
}

/* ─── INIT ───────────────────────────────── */
window.addEventListener('DOMContentLoaded', () => {
  restoreSettingsUI();
  refreshData();
  startAutoRefresh();
  setConnectionState(false);
});
