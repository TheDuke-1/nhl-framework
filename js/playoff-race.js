/**
 * Playoff Race Tab - Conference standings with playoff line
 */
const PlayoffRace = (() => {
  function render(container, data) {
    const teams = data.teams || [];
    const east = teams
      .filter(t => t.conference === 'East')
      .sort((a, b) => b.playoffProbability - a.playoffProbability);
    const west = teams
      .filter(t => t.conference === 'West')
      .sort((a, b) => b.playoffProbability - a.playoffProbability);

    container.innerHTML = `
      <div class="tab-header">
        <h2>Playoff Race</h2>
        <p class="tab-subtitle">Current projected standings by conference. Top 8 make the playoffs.</p>
      </div>

      <div class="conference-grid">
        <div class="conference-panel">
          <h3>Eastern Conference</h3>
          ${renderConference(east)}
        </div>
        <div class="conference-panel">
          <h3>Western Conference</h3>
          ${renderConference(west)}
        </div>
      </div>

      <div class="bubble-section">
        <h3>Bubble Watch</h3>
        <div class="bubble-teams">
          ${renderBubble(east, west)}
        </div>
      </div>
    `;
  }

  function renderConference(teams) {
    return `
      <table class="data-table compact">
        <thead>
          <tr>
            <th>#</th>
            <th>Team</th>
            <th>Div</th>
            <th>Strength</th>
            <th>Playoff%</th>
            <th>Cup%</th>
          </tr>
        </thead>
        <tbody>
          ${teams.map((t, i) => {
            const isPlayoffLine = i === 7;
            const inPlayoffs = i < 8;
            return `
              <tr class="${inPlayoffs ? 'in-playoffs' : 'out-playoffs'} ${isPlayoffLine ? 'playoff-line' : ''}">
                <td>${i + 1}</td>
                <td>
                  <span class="team-code">${t.code}</span>
                  <span class="tier-dot" style="background:${Utils.tierColor(t.tier)}"></span>
                </td>
                <td class="muted">${t.division}</td>
                <td class="mono">${t.compositeStrength.toFixed(1)}</td>
                <td class="mono">${Utils.pct(t.playoffProbability)}</td>
                <td class="mono">${Utils.pct(t.cupProbability)}</td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    `;
  }

  function renderBubble(east, west) {
    // Teams ranked 6-10 in each conference (around the playoff line)
    const bubbleTeams = [
      ...east.slice(5, 10).map(t => ({ ...t, conf: 'East' })),
      ...west.slice(5, 10).map(t => ({ ...t, conf: 'West' }))
    ].sort((a, b) => b.playoffProbability - a.playoffProbability);

    return bubbleTeams.map(t => `
      <div class="bubble-card">
        <div class="bubble-team">${t.code}</div>
        <div class="bubble-conf">${t.conf}</div>
        <div class="bubble-prob">
          <div class="prob-bar-track">
            <div class="prob-bar-fill" style="width:${Math.min(t.playoffProbability, 100)}%;background:${t.playoffProbability >= 50 ? '#10b981' : '#f59e0b'}"></div>
          </div>
          <span class="mono">${Utils.pct(t.playoffProbability)}</span>
        </div>
      </div>
    `).join('');
  }

  return { render };
})();
