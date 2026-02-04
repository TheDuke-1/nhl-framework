/**
 * NHL Superhuman Dashboard - Main App
 * Handles routing, data loading, and tab management.
 */

const App = (() => {
  let data = null;
  let currentTab = 'rankings';

  const TABS = ['rankings', 'playoff-race', 'betting', 'bracket', 'performance', 'insights'];

  async function init() {
    try {
      data = await loadData();
      setupTabs();
      updateHeader();
      renderTab(currentTab);
    } catch (err) {
      document.getElementById('tab-content').innerHTML =
        `<div class="error-card"><h2>Failed to load data</h2><p>${err.message}</p></div>`;
    }
  }

  async function loadData() {
    // Try fetch first (works on GitHub Pages / any HTTP server)
    try {
      const resp = await fetch('dashboard_data.json');
      if (resp.ok) return resp.json();
      // Server is reachable but returned an error — don't silently fall back
      throw new Error(`HTTP ${resp.status}: Could not load dashboard_data.json`);
    } catch (e) {
      // Network error (e.g. file:// CORS) — fall through to inline fallback
      if (e.message.startsWith('HTTP ')) throw e;
    }
    // Fallback: data embedded via js/data.js (for file:// protocol)
    if (window.DASHBOARD_DATA) return window.DASHBOARD_DATA;
    throw new Error('Could not load dashboard data. Ensure dashboard_data.json or js/data.js exists.');
  }

  function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab');
    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        if (tab === currentTab) return;
        tabButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentTab = tab;
        renderTab(tab);
        history.replaceState(null, '', `#${tab}`);
      });
    });

    // Handle URL hash
    const hash = window.location.hash.slice(1);
    if (TABS.includes(hash)) {
      currentTab = hash;
      tabButtons.forEach(b => {
        b.classList.toggle('active', b.dataset.tab === hash);
      });
    }
  }

  function updateHeader() {
    if (!data || !data.meta) return;

    const lastUpdate = document.getElementById('last-updated');
    if (lastUpdate) {
      lastUpdate.textContent = 'Last updated: ' + (data.meta.lastUpdate || 'Unknown');
      lastUpdate.title = 'Click for source freshness';
      lastUpdate.style.cursor = 'pointer';
      lastUpdate.addEventListener('click', showFreshnessPopover);
    }

    const season = document.getElementById('season-label');
    if (season) {
      season.textContent = (data.meta.seasonDisplay || '2025-26') + ' Season';
    }

    // Off-season detection: if generated > 30 days ago, show banner
    if (data.meta.generated) {
      const genDate = new Date(data.meta.generated);
      const daysSince = (Date.now() - genDate.getTime()) / (1000 * 60 * 60 * 24);
      if (daysSince > 30) {
        const banner = document.getElementById('offseason-banner');
        if (banner) {
          banner.style.display = 'block';
          banner.textContent = 'Off-season: Showing final results from ' + data.meta.seasonDisplay;
        }
      }
    }
  }

  function showFreshnessPopover(e) {
    // Remove existing popover
    const existing = document.querySelector('.freshness-popover');
    if (existing) { existing.remove(); return; }

    const popover = document.createElement('div');
    popover.className = 'freshness-popover';
    popover.innerHTML = `
      <div class="freshness-title">Data Freshness</div>
      <div class="freshness-row"><span>Generated:</span><span>${data.meta.generated || 'Unknown'}</span></div>
      <div class="freshness-row"><span>Model:</span><span>${data.meta.modelVersion || 'Unknown'}</span></div>
      <div class="freshness-row"><span>Season:</span><span>${data.meta.seasonDisplay || 'Unknown'}</span></div>
    `;
    e.target.parentNode.appendChild(popover);

    // Close on outside click
    setTimeout(() => {
      document.addEventListener('click', function handler(ev) {
        if (!popover.contains(ev.target) && ev.target !== e.target) {
          popover.remove();
          document.removeEventListener('click', handler);
        }
      });
    }, 10);
  }

  function renderTab(tab) {
    const container = document.getElementById('tab-content');
    if (!container || !data) return;

    container.innerHTML = '<div class="loading">Loading...</div>';

    switch (tab) {
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

    const currentDir = table.dataset.sortDir === 'asc' ? 'desc' : 'asc';
    table.dataset.sortDir = currentDir;
    table.dataset.sortCol = colIdx;

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
