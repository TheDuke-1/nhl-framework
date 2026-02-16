/**
 * Betting Value Tab - Edge calculation with manual odds override
 */
const Betting = (() => {
  const STORAGE_KEY = 'nhl-betting-odds';
  let inputErrors = {};

  function render(container, data) {
    const teams = data.teams || [];
    const savedOdds = loadSavedOdds();
    const normalizedOdds = normalizeSavedOdds(savedOdds);
    inputErrors = normalizedOdds.errors;

    // Calculate edges
    const teamsWithEdge = teams.map((t) => {
      const manualOdds = normalizedOdds.odds[t.code];
      const impliedProb = manualOdds ? oddsToImplied(manualOdds) : null;
      const modelProb = t.cupProbability;
      const edge = impliedProb != null ? modelProb - impliedProb : null;
      return {
        ...t,
        manualOdds,
        impliedProb,
        edge,
        inputError: inputErrors[t.code] || null
      };
    });

    // Sort by edge (biggest value first)
    const valueTeams = teamsWithEdge
      .filter((t) => t.edge != null)
      .sort((a, b) => b.edge - a.edge);

    container.innerHTML = `
      <div class="tab-header">
        <h2>Betting Value</h2>
        <p class="tab-subtitle">Compare model probabilities vs market odds. Enter Cup futures odds to find value.</p>
      </div>

      ${valueTeams.length > 0 ? renderValueFlags(valueTeams) : ''}

      <div class="table-wrapper">
        <table id="betting-table" class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Team</th>
              <th>Model Cup%</th>
              <th>Your Odds</th>
              <th>Implied%</th>
              <th>Edge</th>
              <th>Signal</th>
            </tr>
          </thead>
          <tbody>
            ${teamsWithEdge.map((t) => renderRow(t)).join('')}
          </tbody>
        </table>
      </div>

      <div class="betting-notes">
        <p>Enter American odds (e.g., +800, -150) in the "Your Odds" column. Values saved to your browser.</p>
        <p>Valid values must include sign and be at least +/-100 (for example: +450, -135).</p>
        <p>Edge = Model probability - Implied probability. Positive edge = potential value bet.</p>
      </div>
    `;

    // Attach odds input handlers
    container.querySelectorAll('.odds-input').forEach((input) => {
      input.addEventListener('change', (event) => {
        const code = event.target.dataset.team;
        const raw = event.target.value.trim();

        if (!raw) {
          delete normalizedOdds.odds[code];
          delete inputErrors[code];
        } else {
          const normalized = normalizeOdds(raw);
          if (!normalized) {
            inputErrors[code] = 'Use +800 or -150 format (minimum +/-100).';
          } else {
            normalizedOdds.odds[code] = normalized;
            delete inputErrors[code];
          }
        }

        saveSavedOdds(normalizedOdds.odds);
        render(container, data);
      });

      input.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
          event.preventDefault();
          input.blur();
        }
      });
    });
  }

  function normalizeSavedOdds(savedOdds) {
    const cleaned = {};
    const errors = {};

    Object.entries(savedOdds).forEach(([code, raw]) => {
      const normalized = normalizeOdds(raw);
      if (normalized) {
        cleaned[code] = normalized;
      } else if (String(raw || '').trim()) {
        errors[code] = 'Use +800 or -150 format (minimum +/-100).';
      }
    });

    if (Object.keys(cleaned).length !== Object.keys(savedOdds).length) {
      saveSavedOdds(cleaned);
    }

    return { odds: cleaned, errors };
  }

  function normalizeOdds(value) {
    const raw = String(value || '').trim().replace(/\s+/g, '');
    if (!raw) return null;
    if (!/^[+-]?\d+$/.test(raw)) return null;

    const odds = parseInt(raw, 10);
    if (!Number.isFinite(odds) || odds === 0) return null;
    if (Math.abs(odds) < 100) return null;

    return odds > 0 ? `+${odds}` : `${odds}`;
  }

  function renderValueFlags(valueTeams) {
    const flags = valueTeams.filter((t) => t.edge >= 5);
    if (flags.length === 0) return '';

    return `
      <div class="value-flags">
        <h3>Value Flags (5%+ edge)</h3>
        <div class="stat-cards">
          ${flags.map((t) => `
            <div class="stat-card value-card">
              <div class="stat-card-team">${t.code}</div>
              <div class="stat-card-value text-positive">+${t.edge.toFixed(1)}%</div>
              <div class="stat-card-label">Model: ${Utils.pct(t.cupProbability)} vs Market: ${Utils.pct(t.impliedProb)}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  function renderRow(team) {
    const edgeClass = team.edge == null ? ''
      : team.edge >= 5 ? 'text-positive'
      : team.edge <= -5 ? 'text-negative' : '';

    const signal = team.edge == null ? '-'
      : team.edge >= 5 ? 'VALUE'
      : team.edge >= 2 ? 'Lean'
      : team.edge <= -5 ? 'Fade' : 'Fair';

    const signalClass = signal === 'VALUE' ? 'signal-value'
      : signal === 'Fade' ? 'signal-fade' : '';

    const inputClass = team.inputError ? 'odds-input odds-input-invalid' : 'odds-input';
    const inputError = team.inputError
      ? `<div class="odds-input-error">${team.inputError}</div>`
      : '';

    return `
      <tr>
        <td>${team.rank}</td>
        <td><span class="team-code">${team.code}</span></td>
        <td class="mono">${Utils.pct(team.cupProbability)}</td>
        <td>
          <input type="text" class="${inputClass}" data-team="${team.code}" aria-invalid="${team.inputError ? 'true' : 'false'}"
            value="${team.manualOdds || ''}" placeholder="+800">
          ${inputError}
        </td>
        <td class="mono">${team.impliedProb != null ? Utils.pct(team.impliedProb) : '-'}</td>
        <td class="mono bold ${edgeClass}">
          ${team.edge != null ? (team.edge >= 0 ? '+' : '') + team.edge.toFixed(1) + '%' : '-'}
        </td>
        <td><span class="${signalClass}">${signal}</span></td>
      </tr>
    `;
  }

  function oddsToImplied(oddsStr) {
    const odds = parseInt(oddsStr, 10);
    if (isNaN(odds)) return null;
    if (odds > 0) return (100 / (odds + 100)) * 100;
    if (odds < 0) return (Math.abs(odds) / (Math.abs(odds) + 100)) * 100;
    return null;
  }

  function loadSavedOdds() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    } catch {
      return {};
    }
  }

  function saveSavedOdds(odds) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(odds));
    } catch {
      // Ignore localStorage failures silently.
    }
  }

  return { render };
})();
