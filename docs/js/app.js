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

/* ─── GITHUB CONFIG ──────────────────────── */
let githubConfig = {
  token:  localStorage.getItem('github_token') || '',
  owner:  localStorage.getItem('github_owner') || '',
  repo:   localStorage.getItem('github_repo') || '',
  branch: localStorage.getItem('github_branch') || 'main',
  device: localStorage.getItem('device_view') || 'desktop'
};

// Auto-load config from URL Query Parameters for 1-click Bat file configuration integration
try {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has('token') || urlParams.has('owner') || urlParams.has('repo')) {
    const paramToken = urlParams.get('token') || '';
    const paramOwner = urlParams.get('owner') || '';
    const paramRepo = urlParams.get('repo') || '';
    const paramDevice = urlParams.get('device') || 'desktop';
    const paramBranch = urlParams.get('branch') || 'main';

    localStorage.setItem('github_token', paramToken);
    localStorage.setItem('github_owner', paramOwner);
    localStorage.setItem('github_repo', paramRepo);
    localStorage.setItem('device_view', paramDevice);
    localStorage.setItem('github_branch', paramBranch);

    githubConfig.token = paramToken;
    githubConfig.owner = paramOwner;
    githubConfig.repo = paramRepo;
    githubConfig.device = paramDevice;
    githubConfig.branch = paramBranch;

    // Clean URL query parameters for security and aesthetic reasons
    window.history.replaceState({}, document.title, window.location.pathname);
  }
} catch (e) {
  console.error("Error auto-loading config from URL:", e);
}

/* ─── PRODUCTION EMPTY STATE ──────────────── */
/* Returns a clean empty structure for production when unconfigured */
function generateEmptyState() {
  return {
    lastUpdated:  "",
    roomStatus:   'UNKNOWN',
    confidence:   0,
    activity:     '',
    rssiVariance: 0,
    rssiCurrent:  null,
    timeline:     [],
    alerts:       [],
    stats: { presentMinutes: 0, absentMinutes: 0 },
    history: {
      labels:  [],
      present: [],
      absent:  [],
    },
    rssiHistory: { labels: [], rssi: [], variance: [] },
    // Bio-signal fields (null = no data yet)
    heartRate:   { bpm: null, confidence: 0, estimated: true, source: 'rssi_variance' },
    bodyTemp:    { celsius: null, estimated: true, basis: 'activity', source: 'inference' },
    peopleCount: { count: null, confidence: 0, estimated: true },
    spo2:        { percent: null, estimated: true, source: 'unavailable' },
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
  const isGithubConfigured = githubConfig.owner && githubConfig.repo;
  if (isGithubConfigured) {
    const path = `docs/data/wificensor_status_${githubConfig.device}.json`;
    let url;
    let headers = {};
    if (githubConfig.token) {
      url = `https://api.github.com/repos/${githubConfig.owner}/${githubConfig.repo}/contents/${path}?ref=${githubConfig.branch}&t=${Date.now()}`;
      headers['Authorization'] = `token ${githubConfig.token}`;
      headers['Accept'] = 'application/vnd.github.v3.raw';
    } else {
      url = `https://raw.githubusercontent.com/${githubConfig.owner}/${githubConfig.repo}/${githubConfig.branch}/${path}?t=${Date.now()}`;
    }

    try {
      const res = await fetch(url, { headers, cache: 'no-store' });
      if (res.ok) {
        let json;
        if (githubConfig.token) {
          const apiRes = await fetch(`https://api.github.com/repos/${githubConfig.owner}/${githubConfig.repo}/contents/${path}?ref=${githubConfig.branch}&t=${Date.now()}`, {
            headers: { 'Authorization': `token ${githubConfig.token}` },
            cache: 'no-store'
          });
          if (apiRes.ok) {
            const data = await apiRes.json();
            const content = atob(data.content.replace(/\s/g, ''));
            json = JSON.parse(content);
          } else {
            throw new Error(`API returned ${apiRes.status}`);
          }
        } else {
          json = await res.json();
        }
        setConnectionState(true);
        return json;
      }
    } catch (err) {
      console.warn('[WifiCensor] GitHub Fetch failed:', err);
    }
  }

  if (config.driveUrl) {
    try {
      const res = await fetch(config.driveUrl, { cache: 'no-store' });
      if (res.ok) {
        setConnectionState(true);
        return await res.json();
      }
    } catch (err) {
      console.warn('[WifiCensor] Drive Fetch failed:', err);
    }
  }

  setConnectionState(false);
  return generateEmptyState();
}

function setConnectionState(connected) {
  isConnected = connected;
  const badge = document.getElementById('connectionBadge');
  const text  = document.getElementById('connectionText');
  
  const isGithubConfigured = githubConfig.owner && githubConfig.repo;
  const isAnyConfigured = isGithubConfigured || config.driveUrl;

  // Show or hide the unconfigured banner in production mode
  const banner = document.getElementById('unconfiguredBanner');
  if (banner) {
    banner.style.display = isAnyConfigured ? 'none' : 'flex';
  }

  if (connected) {
    badge.className = 'connection-badge connected';
    text.textContent = isGithubConfigured ? `GitHub: ${githubConfig.device}` : 'Đã kết nối';
  } else {
    badge.className = isAnyConfigured ? 'connection-badge error' : 'connection-badge';
    text.textContent = isAnyConfigured ? 'Không kết nối được' : 'Chưa cấu hình';
  }
}

/* ─── RENDER ─────────────────────────────── */
async function refreshData() {
  const data = await fetchData();

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

  // Show/Hide Remote Control Panel
  const remotePanel = document.getElementById('remote-control-panel');
  if (remotePanel) {
    const isGithubConfigured = githubConfig.owner && githubConfig.repo;
    if (isGithubConfigured) {
      remotePanel.style.display = 'flex';
      
      // Update sensitivity range slider UI if present in data
      const sensSlider = document.getElementById('remote-sensitivity');
      const sensVal = document.getElementById('remote-sensitivity-value');
      if (sensSlider && sensVal && data.sensitivity !== undefined) {
        sensSlider.value = data.sensitivity;
        sensVal.textContent = `${Number(data.sensitivity).toFixed(2)}x`;
      }

      // Show/Hide remote ACK button based on alert status
      const ackBtn = document.getElementById('remote-ack-alert');
      if (ackBtn) {
        const isAlert = data.roomStatus === 'ALERT' || data.roomStatus === 'DANGER';
        ackBtn.style.display = isAlert ? 'inline-block' : 'none';
      }
    } else {
      remotePanel.style.display = 'none';
    }
  }

  // Scan all devices connected via GitHub in background
  scanDevices();

  // Bio-signal rendering
  renderBioSignals(data);
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

  // GitHub inputs
  const tokenInput  = document.getElementById('github-token');
  const ownerInput  = document.getElementById('github-owner');
  const repoInput   = document.getElementById('github-repo');
  const branchInput = document.getElementById('github-branch');
  const devSelect   = document.getElementById('device-selector');

  if (tokenInput)  tokenInput.value  = githubConfig.token || '';
  if (ownerInput)  ownerInput.value  = githubConfig.owner || '';
  if (repoInput)   repoInput.value   = githubConfig.repo || '';
  if (branchInput) branchInput.value = githubConfig.branch || 'main';
  if (devSelect)   devSelect.value   = githubConfig.device || 'desktop';
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
  setConnectionState(false);
  refreshData();
  startAutoRefresh();
});

/* ─── GITHUB REMOTE SYNC & CONTROL ───────── */
function saveGithubSettings() {
  const token  = document.getElementById('github-token')?.value.trim()  || '';
  const owner  = document.getElementById('github-owner')?.value.trim()  || '';
  const repo   = document.getElementById('github-repo')?.value.trim()   || '';
  const branch = document.getElementById('github-branch')?.value.trim() || 'main';
  const device = document.getElementById('device-selector')?.value       || 'desktop';

  localStorage.setItem('github_token', token);
  localStorage.setItem('github_owner', owner);
  localStorage.setItem('github_repo', repo);
  localStorage.setItem('github_branch', branch);
  localStorage.setItem('device_view', device);

  githubConfig = { token, owner, repo, branch, device };

  const statusEl = document.getElementById('github-sync-status');
  if (statusEl) {
    statusEl.style.color = '#10b981';
    statusEl.textContent = '✅ Đã lưu cấu hình GitHub!';
    setTimeout(() => statusEl.textContent = '', 3000);
  }

  refreshData();
}

async function testGithubConnection() {
  const token  = document.getElementById('github-token')?.value.trim()  || '';
  const owner  = document.getElementById('github-owner')?.value.trim()  || '';
  const repo   = document.getElementById('github-repo')?.value.trim()   || '';
  const statusEl = document.getElementById('github-sync-status');

  if (!owner || !repo) {
    if (statusEl) {
      statusEl.style.color = '#ef4444';
      statusEl.textContent = '❌ Vui lòng điền Owner và Repo!';
    }
    return;
  }

  if (statusEl) {
    statusEl.style.color = '#06b6d4';
    statusEl.textContent = '⏳ Đang kết nối thử...';
  }

  const url = `https://api.github.com/repos/${owner}/${repo}`;
  const headers = token ? { 'Authorization': `token ${token}` } : {};

  try {
    const res = await fetch(url, { headers });
    if (res.ok) {
      const data = await res.json();
      if (statusEl) {
        statusEl.style.color = '#10b981';
        statusEl.textContent = `✅ Kết nối thành công! Repo: ${data.name}`;
      }
    } else {
      throw new Error(`HTTP ${res.status}`);
    }
  } catch (err) {
    if (statusEl) {
      statusEl.style.color = '#ef4444';
      statusEl.textContent = `❌ Kết nối thất bại: ${err.message}`;
    }
  }
}

async function sendRemoteCommand(action, value = null) {
  if (!githubConfig.token || !githubConfig.owner || !githubConfig.repo) {
    alert('Vui lòng cấu hình GitHub Token và Repository trước khi điều khiển từ xa!');
    return false;
  }

  const controlPath = 'docs/data/wificensor_control.json';
  const getUrl = `https://api.github.com/repos/${githubConfig.owner}/${githubConfig.repo}/contents/${controlPath}`;
  const headers = {
    'Authorization': `token ${githubConfig.token}`,
    'Content-Type': 'application/json'
  };

  let sha = null;
  let commands = [];

  try {
    const res = await fetch(getUrl, { headers, cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      sha = data.sha;
      commands = JSON.parse(atob(data.content.replace(/\s/g, '')));
    }
  } catch (e) {
    console.log('[WifiCensor] Control file not found, creating new one');
  }

  commands.push({
    id: Date.now(),
    device: githubConfig.device,
    action: action,
    value: value,
    timestamp: new Date().toISOString()
  });

  const newContent = btoa(unescape(encodeURIComponent(JSON.stringify(commands, null, 2))));
  const body = {
    message: `Remote command: ${action} from Web Dashboard`,
    content: newContent,
    branch: githubConfig.branch
  };
  if (sha) body.sha = sha;

  try {
    const putRes = await fetch(getUrl, {
      method: 'PUT',
      headers,
      body: JSON.stringify(body)
    });
    return putRes.ok;
  } catch (err) {
    console.error('[WifiCensor] Failed to send remote command:', err);
    return false;
  }
}

async function sendRemoteAck() {
  const btn = document.getElementById('remote-ack-alert');
  const origText = btn.textContent;
  btn.textContent = '⏳ Đang tắt...';
  btn.disabled = true;

  const success = await sendRemoteCommand('acknowledge_alert');
  if (success) {
    btn.textContent = '✅ Đã gửi lệnh!';
    setTimeout(() => {
      btn.textContent = origText;
      btn.disabled = false;
      btn.style.display = 'none';
    }, 2000);
  } else {
    btn.textContent = '❌ Lỗi!';
    setTimeout(() => {
      btn.textContent = origText;
      btn.disabled = false;
    }, 2000);
  }
}

async function sendRemoteCalibrate() {
  const btn = document.querySelector('[onclick="sendRemoteCalibrate()"]');
  const origText = btn.textContent;
  btn.textContent = '⏳ Đang gửi...';
  btn.disabled = true;

  const success = await sendRemoteCommand('calibrate');
  if (success) {
    btn.textContent = '✅ Đã gửi yêu cầu!';
    setTimeout(() => {
      btn.textContent = origText;
      btn.disabled = false;
    }, 2500);
  } else {
    btn.textContent = '❌ Thất bại!';
    setTimeout(() => {
      btn.textContent = origText;
      btn.disabled = false;
    }, 2500);
  }
}

async function sendRemoteSensitivity(val) {
  const sensVal = document.getElementById('remote-sensitivity-value');
  if (sensVal) {
    sensVal.textContent = `${Number(val).toFixed(2)}x`;
  }
  await sendRemoteCommand('set_sensitivity', val);
}

/* ─── DEVICE AUTODISCOVERY & VIEWS ───────── */
async function scanDevices() {
  const container = document.getElementById('connectedDevicesList');
  const badge = document.getElementById('devicesCountBadge');
  
  const isGithubConfigured = githubConfig.owner && githubConfig.repo;
  if (!isGithubConfigured) {
    if (container) {
      container.innerHTML = `
        <div class="empty-state" style="text-align: center; padding: 20px 0;">
          <span style="font-size: 24px; display: block; margin-bottom: 8px;">🔌</span>
          <span style="font-size: 13px; color: var(--text-secondary);">Chưa cấu hình đồng bộ GitHub</span>
        </div>`;
    }
    if (badge) badge.textContent = 'Chưa kết nối';
    return;
  }

  let activeCount = 0;
  let totalCount = 0;
  let html = '';

  const devices = [
    { id: 'desktop', name: 'Windows Desktop', icon: '💻' },
    { id: 'mobile', name: 'Android Mobile', icon: '📱' }
  ];

  for (const dev of devices) {
    const path = `docs/data/wificensor_status_${dev.id}.json`;
    let url;
    let headers = {};
    if (githubConfig.token) {
      url = `https://api.github.com/repos/${githubConfig.owner}/${githubConfig.repo}/contents/${path}?ref=${githubConfig.branch}&t=${Date.now()}`;
      headers['Authorization'] = `token ${githubConfig.token}`;
      headers['Accept'] = 'application/vnd.github.v3.raw';
    } else {
      url = `https://raw.githubusercontent.com/${githubConfig.owner}/${githubConfig.repo}/${githubConfig.branch}/${path}?t=${Date.now()}`;
    }

    try {
      const res = await fetch(url, { headers, cache: 'no-store' });
      if (res.ok) {
        totalCount++;
        let json;
        if (githubConfig.token) {
          const apiRes = await fetch(`https://api.github.com/repos/${githubConfig.owner}/${githubConfig.repo}/contents/${path}?ref=${githubConfig.branch}&t=${Date.now()}`, {
            headers: { 'Authorization': `token ${githubConfig.token}` },
            cache: 'no-store'
          });
          if (apiRes.ok) {
            const data = await apiRes.json();
            const content = atob(data.content.replace(/\s/g, ''));
            json = JSON.parse(content);
          } else {
            throw new Error('API Content read failed');
          }
        } else {
          json = await res.json();
        }

        // Calculate Online/Offline (updated within last 5 minutes)
        let isOnline = false;
        let timeStr = 'Không rõ';
        if (json.lastUpdated) {
          const lastTime = new Date(json.lastUpdated);
          const diffMin = Math.round((new Date() - lastTime) / 60000);
          isOnline = diffMin < 5;
          if (diffMin < 1) timeStr = 'Vừa xong';
          else if (diffMin < 60) timeStr = `${diffMin}p trước`;
          else timeStr = lastTime.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
        }

        const roomStatusMap = {
          PRESENT: '🟢 Có mặt',
          ABSENT: '⚪ Vắng phòng',
          ALERT: '🟡 Cảnh báo',
          DANGER: '🔴 Khẩn cấp',
          UNKNOWN: '❓ Đang quét'
        };

        const statusLabel = roomStatusMap[(json.roomStatus || 'UNKNOWN').toUpperCase()] || 'Đang quét';
        const isActive = githubConfig.device === dev.id;

        if (isOnline) activeCount++;

        html += `
          <div class="device-item ${isActive ? 'active' : ''}" onclick="selectDeviceView('${dev.id}')">
            <div class="device-info">
              <div class="device-avatar">${dev.icon}</div>
              <div class="device-details">
                <span class="device-name">${dev.name}</span>
                <span class="device-status-text">${statusLabel}</span>
              </div>
            </div>
            <div class="device-meta">
              <span class="device-status-badge ${isOnline ? 'online' : 'offline'}">${isOnline ? 'Online' : 'Offline'}</span>
              <span class="device-time">${timeStr}</span>
            </div>
          </div>
        `;
      } else {
        // Device file doesn't exist on git
        html += `
          <div class="device-item" style="opacity: 0.5; cursor: not-allowed;">
            <div class="device-info">
              <div class="device-avatar">${dev.icon}</div>
              <div class="device-details">
                <span class="device-name">${dev.name}</span>
                <span class="device-status-text" style="color: var(--text-muted)">Chưa có dữ liệu</span>
              </div>
            </div>
            <div class="device-meta">
              <span class="device-status-badge offline">Offline</span>
              <span class="device-time">--</span>
            </div>
          </div>
        `;
      }
    } catch (e) {
      console.warn(`[WifiCensor] Failed to scan device ${dev.id}`, e);
    }
  }

  if (container) {
    container.innerHTML = html;
  }
  if (badge) badge.textContent = `${activeCount} Online / ${totalCount} Cấu hình`;
}

function selectDeviceView(deviceId) {
  localStorage.setItem('device_view', deviceId);
  githubConfig.device = deviceId;
  
  const devSelect = document.getElementById('device-selector');
  if (devSelect) devSelect.value = deviceId;
  
  refreshData();
}

/* ─── BIO-SIGNAL RENDERING ────────────────── */
function renderBioSignals(data) {

  /* ── 1. Heart Rate ────────────────────────── */
  const hrCard   = document.getElementById('bioCardHeart');
  const hrBpmEl  = document.getElementById('heartRateBpm');
  const hrFill   = document.getElementById('heartRateConfFill');
  const hrConf   = document.getElementById('heartRateConfVal');
  const hrHint   = document.getElementById('heartRateHint');
  const hrSource = document.getElementById('heartRateSource');
  const hrIcon   = document.getElementById('heartbeatIcon');

  const hr = data.heartRate;
  if (hr && hr.bpm !== null && hr.bpm !== undefined) {
    const bpm  = Math.round(hr.bpm);
    const conf = Math.round((hr.confidence || 0) * 100);

    hrBpmEl.textContent = bpm;
    hrFill.style.width  = `${conf}%`;
    hrConf.textContent  = `${conf}%`;

    // BPM category
    let hint;
    if      (bpm < 50)  hint = '💤 Rất chậm — ngủ sâu';
    else if (bpm < 60)  hint = '😴 Chậm — đang nghỉ ngơi';
    else if (bpm < 80)  hint = '✅ Bình thường';
    else if (bpm < 100) hint = '🙂 Hơi nhanh';
    else if (bpm < 120) hint = '🏃 Đang hoạt động';
    else                hint = '⚠️ Nhịp tim cao';
    hrHint.textContent = hint;

    // Heartbeat animation speed (1 beat = 60/bpm seconds)
    const period = (60 / bpm).toFixed(2);
    if (hrIcon) hrIcon.style.setProperty('--heartbeat-duration', `${period}s`);

    // Source badge
    if (hrSource) {
      hrSource.textContent = hr.source === 'max30102'
        ? '🟢 Cảm biến MAX30102 · Dữ liệu thực'
        : '📡 Ước tính từ tín hiệu Wi-Fi · Có thể kết nối MAX30102';
    }
    hrCard?.classList.remove('bio-no-data');
  } else {
    hrBpmEl.textContent = '--';
    hrFill.style.width  = '0%';
    hrConf.textContent  = '--%';
    hrHint.textContent  = 'Chờ dữ liệu...';
    hrCard?.classList.add('bio-no-data');
  }

  /* ── 2. Body Temperature ──────────────────── */
  const tempCard   = document.getElementById('bioCardTemp');
  const tempValEl  = document.getElementById('bodyTempValue');
  const tempBasis  = document.getElementById('bodyTempBasis');
  const tempNeedle = document.getElementById('tempNeedle');
  const tempBadge  = document.getElementById('tempBadge');
  const sensorBadge = document.getElementById('tempSensorBadge');

  const bt = data.bodyTemp;
  if (bt && bt.celsius !== null && bt.celsius !== undefined) {
    const temp = bt.celsius;
    tempValEl.textContent = temp.toFixed(1);

    // Needle position on gradient bar (35°C–41°C range → 0–100%)
    const pct = Math.min(100, Math.max(0, (temp - 35) / (41 - 35) * 100));
    if (tempNeedle) tempNeedle.style.left = `${pct}%`;

    // Basis label
    const basisMap = {
      sensor:   '🟢 Cảm biến hồng ngoại MLX90614',
      activity: '📊 Suy luận từ hoạt động Wi-Fi',
    };
    if (tempBasis) tempBasis.textContent = basisMap[bt.basis] || bt.basis;

    // Badge
    if (tempBadge) {
      if (bt.source === 'mlx90614') {
        tempBadge.textContent = 'Cảm biến thực';
        tempBadge.classList.remove('estimated-badge-warm');
        tempBadge.classList.add('estimated-badge-blue');
      } else {
        tempBadge.textContent = 'Suy luận';
        tempBadge.classList.remove('estimated-badge-blue');
        tempBadge.classList.add('estimated-badge-warm');
      }
    }

    // Sensor ready badge
    if (sensorBadge) {
      sensorBadge.style.display = bt.source === 'mlx90614' ? 'none' : 'flex';
    }

    // Fever / low temp coloring
    tempCard?.classList.remove('bio-no-data', 'temp-fever', 'temp-low');
    if (temp >= 38.0)      tempCard?.classList.add('temp-fever');
    else if (temp < 36.0)  tempCard?.classList.add('temp-low');
  } else {
    tempValEl.textContent = '--.-';
    if (tempNeedle) tempNeedle.style.left = '25%';
    if (tempBasis)  tempBasis.textContent  = 'Chờ dữ liệu...';
    tempCard?.classList.add('bio-no-data');
  }

  /* ── 3. People Count ──────────────────────── */
  const peopleCard    = document.getElementById('bioCardPeople');
  const peopleCountEl = document.getElementById('peopleCountValue');
  const peopleFill    = document.getElementById('peopleConfFill');
  const peopleConfEl  = document.getElementById('peopleConfVal');
  const peopleDescEl  = document.getElementById('peopleCountDesc');
  const iconsGrid     = document.getElementById('peopleIconsGrid');

  const pc = data.peopleCount;
  if (pc && pc.count !== null && pc.count !== undefined) {
    const count = pc.count;
    const conf  = Math.round((pc.confidence || 0) * 100);

    peopleCountEl.textContent = count;
    peopleFill.style.width    = `${conf}%`;
    peopleConfEl.textContent  = `${conf}%`;

    // Person icon grid (max 8 icons)
    if (iconsGrid) {
      if (count === 0) {
        iconsGrid.innerHTML = '<span style="font-size:13px;color:var(--text-muted)">Phòng trống</span>';
      } else {
        iconsGrid.innerHTML = Array(Math.min(count, 8))
          .fill(null)
          .map(() => '<span class="person-icon-item">👤</span>')
          .join('');
      }
    }

    // Description
    const descMap = {
      0: 'Không phát hiện ai trong khu vực',
      1: 'Phát hiện 1 người trong khu vực',
      2: 'Phát hiện khoảng 2 người',
      3: 'Phát hiện khoảng 3 người',
    };
    if (peopleDescEl) {
      peopleDescEl.textContent = descMap[count] || `Phát hiện khoảng ${count} người`;
    }

    peopleCard?.classList.remove('bio-no-data');
  } else {
    peopleCountEl.textContent = '--';
    peopleFill.style.width    = '0%';
    peopleConfEl.textContent  = '--%';
    if (peopleDescEl)  peopleDescEl.textContent  = 'Chờ dữ liệu...';
    if (iconsGrid)     iconsGrid.innerHTML = '';
    peopleCard?.classList.add('bio-no-data');
  }
}
