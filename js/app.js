/**
 * NHL Superhuman Dashboard - Main App
 * Handles routing, data loading, and tab management.
 */

const App = (() => {
  let data = null;
  let currentTab = 'mission-control';
  let tabButtons = [];

  const TABS = ['mission-control', 'rankings', 'playoff-race', 'betting', 'bracket', 'performance', 'insights'];

  async function init() {
    try {
      data = await loadData();
      setupTabs();
      updateHeader();
    } catch (err) {
      document.getElementById('tab-content').innerHTML =
        `<div class="error-card"><h2>Failed to load data</h2><p>${err.message}</p></div>`;
    }
  }

  async function loadData() {
    let payload = null;

    // Try fetch first (works on GitHub Pages / any HTTP server)
    try {
      const resp = await fetch('dashboard_data.json', { cache: 'no-store' });
      if (resp.ok) {
        payload = await resp.json();
        payload.meta = payload.meta || {};
        payload.meta.dataOrigin = 'dashboard-json';
      } else {
        // Server is reachable but returned an error — don't silently fall back
        throw new Error(`HTTP ${resp.status}: Could not load dashboard_data.json`);
      }
    } catch (e) {
      // Network error (e.g. file:// CORS) — fall through to inline fallback
      if (e.message.startsWith('HTTP ')) throw e;
    }

    // Fallback: data embedded via js/data.js (for file:// protocol)
    if (!payload && window.DASHBOARD_DATA) {
      payload = window.DASHBOARD_DATA;
      payload.meta = payload.meta || {};
      payload.meta.dataOrigin = 'embedded-fallback';
    }
    if (!payload) {
      throw new Error('Could not load dashboard data. Ensure dashboard_data.json or js/data.js exists.');
    }

    // Optional benchmark payload (for quality deltas and Vegas status cards)
    const benchmark = await loadBenchmarkData(payload);
    if (benchmark) {
      payload.benchmark = benchmark;
    }
    const releaseCycle = await loadReleaseCycleData(payload);
    if (releaseCycle) {
      payload.releaseCycle = releaseCycle;
    }
    const dashboardGrade = await loadDashboardGradeData(payload);
    if (dashboardGrade) {
      payload.dashboardGrade = dashboardGrade;
    }
    return payload;
  }

  async function loadBenchmarkData(payload) {
    if (payload.benchmark && payload.benchmark.current) {
      return payload.benchmark;
    }
    try {
      const resp = await fetch('reports/benchmark_latest.json', { cache: 'no-store' });
      if (resp.ok) return resp.json();
      // Server is reachable but returned an error — don't silently fall back
    } catch (e) {
      // Optional file; ignore if unavailable.
    }
    return null;
  }

  async function loadReleaseCycleData(payload) {
    if (payload.releaseCycle && (payload.releaseCycle.status || payload.releaseCycle.shipGateStatus || payload.releaseCycle.strict?.status)) {
      return payload.releaseCycle;
    }
    try {
      const resp = await fetch('reports/phase7_release_cycle_latest.json', { cache: 'no-store' });
      if (resp.ok) return resp.json();
    } catch (e) {
      // Optional file; ignore if unavailable.
    }
    try {
      const resp = await fetch('reports/phase7_release_cycle.json', { cache: 'no-store' });
      if (resp.ok) return resp.json();
    } catch (e) {
      // Optional file; ignore if unavailable.
    }
    return null;
  }

  async function loadDashboardGradeData(payload) {
    if (payload.dashboardGrade && payload.dashboardGrade.dashboard) {
      return payload.dashboardGrade;
    }
    try {
      const resp = await fetch('reports/current_model_dashboard_grade.json', { cache: 'no-store' });
      if (resp.ok) return resp.json();
    } catch (e) {
      // Optional file; ignore if unavailable.
    }
    return null;
  }

  function setupTabs() {
    tabButtons = Array.from(document.querySelectorAll('.tab'));
    tabButtons.forEach((btn, idx) => {
      btn.setAttribute('tabindex', btn.dataset.tab === currentTab ? '0' : '-1');
      btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        if (tab === currentTab) return;
        activateTab(tab, true);
      });
      btn.addEventListener('keydown', (e) => {
        const key = e.key;
        if (key === 'ArrowRight' || key === 'ArrowLeft') {
          e.preventDefault();
          const delta = key === 'ArrowRight' ? 1 : -1;
          const nextIndex = (idx + delta + tabButtons.length) % tabButtons.length;
          tabButtons[nextIndex].focus();
          return;
        }
        if (key === 'Home' || key === 'End') {
          e.preventDefault();
          const target = key === 'Home' ? tabButtons[0] : tabButtons[tabButtons.length - 1];
          target.focus();
          return;
        }
        if (key === 'Enter' || key === ' ') {
          e.preventDefault();
          activateTab(btn.dataset.tab, true);
        }
      });
    });

    // Handle URL hash
    const hash = window.location.hash.slice(1);
    if (TABS.includes(hash)) {
      activateTab(hash, false);
      return;
    }
    activateTab(currentTab, false);
  }

  function activateTab(tab, updateHash) {
    if (!TABS.includes(tab)) return;
    currentTab = tab;
    tabButtons.forEach(btn => {
      const isActive = btn.dataset.tab === tab;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
      btn.setAttribute('tabindex', isActive ? '0' : '-1');
    });
    renderTab(tab);
    if (updateHash) {
      history.replaceState(null, '', `#${tab}`);
    }
  }

  function updateHeader() {
    if (!data || !data.meta) return;

    const lastUpdate = document.getElementById('last-updated');
    if (lastUpdate) {
      lastUpdate.textContent = 'Last updated: ' + (data.meta.lastUpdate || 'Unknown');
      lastUpdate.title = 'Click for source freshness';
      lastUpdate.addEventListener('click', toggleFreshnessPopover);
      lastUpdate.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          toggleFreshnessPopover(event);
        }
      });
    }

    const season = document.getElementById('season-label');
    if (season) {
      season.textContent = (data.meta.seasonDisplay || '2025-26') + ' Season';
    }

    setFreshnessValues();
    updateDataStatusBanner();
  }

  function setFreshnessValues() {
    const sourceFreshness = data.meta.sourceFreshness || data.meta.freshness || {};
    const fallbackValue = data.meta.generated || data.meta.lastUpdate || 'Unknown';
    const freshness = {
      'fresh-nhl': sourceFreshness.nhl || sourceFreshness.nhl_standings || fallbackValue,
      'fresh-moneypuck': sourceFreshness.moneypuck || sourceFreshness.moneypuck_stats || fallbackValue,
      'fresh-nst': sourceFreshness.nst || sourceFreshness.nst_stats || fallbackValue,
      'fresh-model': data.meta.generated || fallbackValue
    };
    Object.entries(freshness).forEach(([id, value]) => {
      const node = document.getElementById(id);
      if (node) node.textContent = formatFreshness(value);
    });
  }

  function formatFreshness(value) {
    if (value == null || value === '') return '--';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return String(value);
    return parsed.toLocaleString(undefined, {
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function updateDataStatusBanner() {
    const banner = document.getElementById('offseason-banner');
    if (!banner) return;

    banner.style.display = 'none';
    banner.removeAttribute('data-kind');
    banner.textContent = '';

    const seasonState = String(data.meta.seasonState || data.meta.phase || '').toLowerCase();
    const explicitOffseason = data.meta.isOffseason === true || seasonState.includes('offseason');
    if (explicitOffseason) {
      banner.style.display = 'block';
      banner.setAttribute('data-kind', 'offseason');
      banner.textContent = `Off-season: Showing final results from ${data.meta.seasonDisplay || 'the latest season'}`;
      return;
    }

    const dataOrigin = String(data.meta.dataOrigin || '');
    if (dataOrigin === 'embedded-fallback') {
      banner.style.display = 'block';
      banner.setAttribute('data-kind', 'stale');
      banner.textContent = 'Using embedded fallback data. Serve the project over HTTP to load the latest dashboard_data.json.';
      return;
    }

    if (!data.meta.generated) return;
    const generated = new Date(data.meta.generated);
    if (Number.isNaN(generated.getTime())) return;

    const daysSince = (Date.now() - generated.getTime()) / (1000 * 60 * 60 * 24);
    const staleThresholdDays = 2;
    if (daysSince > staleThresholdDays) {
      banner.style.display = 'block';
      banner.setAttribute('data-kind', 'stale');
      banner.textContent = `Data freshness warning: model output is ${Math.floor(daysSince)} day(s) old.`;
      return;
    }

    const benchmarkTimestamp = data.meta.benchmarkTimestamp;
    if (!benchmarkTimestamp) return;
    const benchmarkDate = new Date(benchmarkTimestamp);
    if (Number.isNaN(benchmarkDate.getTime())) return;
    const benchmarkAgeDays = (Date.now() - benchmarkDate.getTime()) / (1000 * 60 * 60 * 24);
    if (benchmarkAgeDays > staleThresholdDays) {
      banner.style.display = 'block';
      banner.setAttribute('data-kind', 'stale');
      banner.textContent = `Benchmark freshness warning: scorecard is ${Math.floor(benchmarkAgeDays)} day(s) old.`;
    }
  }

  function toggleFreshnessPopover(event) {
    event.stopPropagation();
    const popover = document.getElementById('freshness-popover');
    const trigger = document.getElementById('last-updated');
    if (!popover || !trigger) return;

    const shouldOpen = popover.hidden;
    if (shouldOpen) {
      popover.hidden = false;
      trigger.setAttribute('aria-expanded', 'true');
      document.addEventListener('click', handleOutsidePopoverClick);
      document.addEventListener('keydown', handlePopoverEscape);
    } else {
      closeFreshnessPopover();
    }
  }

  function handleOutsidePopoverClick(event) {
    const popover = document.getElementById('freshness-popover');
    const trigger = document.getElementById('last-updated');
    if (!popover || !trigger) return;
    if (!popover.contains(event.target) && event.target !== trigger) {
      closeFreshnessPopover();
    }
  }

  function handlePopoverEscape(event) {
    if (event.key === 'Escape') {
      closeFreshnessPopover();
    }
  }

  function closeFreshnessPopover() {
    const popover = document.getElementById('freshness-popover');
    const trigger = document.getElementById('last-updated');
    if (popover) popover.hidden = true;
    if (trigger) trigger.setAttribute('aria-expanded', 'false');
    document.removeEventListener('click', handleOutsidePopoverClick);
    document.removeEventListener('keydown', handlePopoverEscape);
  }

  function renderTab(tab) {
    const container = document.getElementById('tab-content');
    if (!container || !data) return;

    container.innerHTML = '<div class="loading">Loading...</div>';

    switch (tab) {
      case 'mission-control':
        MissionControl.render(container, data);
        break;
      case 'rankings':
        Rankings.render(container, data);
        break;
      case 'playoff-race':
        PlayoffRace.render(container, data);
        break;
      case 'betting':
        Betting.render(container, data);
        break;
      case 'bracket':
        Bracket.render(container, data);
        break;
      case 'performance':
        Performance.render(container, data);
        break;
      case 'insights':
        Insights.render(container, data);
        break;
      default:
        container.innerHTML = '<div class="error-card">Unknown tab</div>';
    }
  }

  function getData() { return data; }

  return { init, getData };
})();

// Shared utility functions
const Utils = {
  tierClass(tier) {
    return 'tier-' + (tier || 'unknown').toLowerCase();
  },

  tierColor(tier) {
    const colors = {
      Elite: '#10b981', Contender: '#3b82f6',
      Bubble: '#f59e0b', Longshot: '#ef4444'
    };
    return colors[tier] || '#64748b';
  },

  pct(val, decimals = 1) {
    return val != null ? val.toFixed(decimals) + '%' : '-';
  },

  sortTable(tableId, colIdx, type = 'number') {
    const table = document.getElementById(tableId);
    if (!table) return;
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const headers = Array.from(table.querySelectorAll('thead th'));

    const currentDir = table.dataset.sortDir === 'asc' ? 'desc' : 'asc';
    table.dataset.sortDir = currentDir;
    table.dataset.sortCol = colIdx;

    headers.forEach((header, idx) => {
      if (!header.classList.contains('sortable')) return;
      header.classList.remove('sort-asc', 'sort-desc');
      header.setAttribute('aria-sort', 'none');
      if (idx === colIdx) {
        header.classList.add(currentDir === 'asc' ? 'sort-asc' : 'sort-desc');
        header.setAttribute('aria-sort', currentDir === 'asc' ? 'ascending' : 'descending');
      }
    });

    rows.sort((a, b) => {
      const aVal = a.children[colIdx]?.textContent.replace('%', '').trim() || '';
      const bVal = b.children[colIdx]?.textContent.replace('%', '').trim() || '';
      let cmp;
      if (type === 'number') {
        cmp = (parseFloat(aVal) || 0) - (parseFloat(bVal) || 0);
      } else {
        cmp = aVal.localeCompare(bVal);
      }
      return currentDir === 'asc' ? cmp : -cmp;
    });

    rows.forEach(r => tbody.appendChild(r));
  }
};

document.addEventListener('DOMContentLoaded', App.init);
