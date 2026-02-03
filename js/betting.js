/**
 * Betting Value Tab - Edge calculation with manual odds override
 */
const Betting = (() => {
  const STORAGE_KEY = 'nhl-betting-odds';

  function render(container, data) {
    const teams = data.teams || [];
    const savedOdds = loadSavedOdds();

    // Calculate edges
    const teamsWithEdge = teams.map(t => {
      const manualOdds = savedOdds[t.code];
      const impliedProb = manualOdds ? oddsToImplied(manualOdds) : null;
      const modelProb = t.cupProbability;
      const edge = impliedProb != null ? modelProb - impliedProb : null;
      return { ...t, manualOdds, impliedProb, edge };
    });

    // Sort by edge (biggest value first)
    const valueTeams = teamsWithEdge
      .filter(t => t.edge != null)
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
            ${teamsWithEdge.map(t => renderRow(t)).join('')}
          </tbody>
        </table>
      </div>

      <div class="betting-notes">
        <p>Enter American odds (e.g., +800, -150) in the "Your Odds" column. Values saved to your browser.</p>
        <p>Edge = Model probability - Implied probability. Positive edge = potential value bet.</p>
      </div>
    `;

    // Attach odds input handlers
    container.querySelectorAll('.odds-input').forEach(input => {
      input.addEventListener('change', (e) => {
        const code = e.target.dataset.team;
        const val = e.target.value.trim();
        if (val) {
          savedOdds[code] = val;
        } else {
          delete savedOdds[code];
        }
        saveSavedOdds(savedOdds);
        render(container, data);
      });
    });
  }

  function renderValueFlags(valueTeams) {
    const flags = valueTeams.filter(t => t.edge >= 5);
    if (flags.length === 0) return '';

    return `
      <div class="value-flags">
        <h3>Value Flags (5%+ edge)</h3>
        <div class="stat-cards">
          ${flags.map(t => `
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
    const edgeClass = team.edge == null ? '' :
      team.edge >= 5 ? 'text-positive' :
      team.edge <= -5 ? 'text-negative' : '';
    const signal = team.edge == null ? '-' :
      team.edge >= 5 ? 'VALUE' :
      team.edge >= 2 ? 'Lean' :
      team.edge <= -5 ? 'Fade' : 'Fair';
    const signalClass = signal === 'VALUE' ? 'signal-value' :
      signal === 'Fade' ? 'signal-fade' : '';

    return `
      <tr>
        <td>${team.rank}</td>
        <td><span class="team-code">${team.code}</span></td>
        <td class="mono">${Utils.pct(team.cupProbability)}</td>
        <td>
          <input type="text" class="odds-input" data-team="${team.code}"
            value="${team.manualOdds || ''}" placeholder="+800">
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
    if (odds > 0) return 100 / (odds + 100) * 100;
    if (odds < 0) return Math.abs(odds) / (Math.abs(odds) + 100) * 100;
    return null;
  }

  function loadSavedOdds() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    } catch { return {}; }
  }

  function saveSavedOdds(odds) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(odds));
    } catch {}
  }

  return { render };
})();
