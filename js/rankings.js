/**
 * Rankings Tab - Power Rankings with sortable columns
 */
const Rankings = (() => {
  let currentFilter = 'all';

  function render(container, data) {
    const teams = data.teams || [];
    const weights = data.featureWeights || [];

    container.innerHTML = `
      <div class="tab-header">
        <h2>Power Rankings</h2>
        <div class="filter-chips">
          <button class="chip active" data-filter="all">All</button>
          <button class="chip" data-filter="East">East</button>
          <button class="chip" data-filter="West">West</button>
          <button class="chip" data-filter="Elite">Elite</button>
          <button class="chip" data-filter="Contender">Contender</button>
        </div>
      </div>

      <div class="stat-cards">
        ${renderTopCards(teams)}
      </div>

      <div class="table-wrapper">
        <table id="rankings-table" class="data-table">
          <thead>
            <tr>
              <th class="sortable" onclick="Utils.sortTable('rankings-table', 0, 'number')">#</th>
              <th class="sortable" onclick="Utils.sortTable('rankings-table', 1, 'string')">Team</th>
              <th>Tier</th>
              <th>Conf</th>
              <th class="sortable" onclick="Utils.sortTable('rankings-table', 4, 'number')">Strength</th>
              <th class="sortable" onclick="Utils.sortTable('rankings-table', 5, 'number')">Playoff%</th>
              <th class="sortable" onclick="Utils.sortTable('rankings-table', 6, 'number')">Conf%</th>
              <th class="sortable" onclick="Utils.sortTable('rankings-table', 7, 'number')">Cup%</th>
              <th class="sortable" onclick="Utils.sortTable('rankings-table', 8, 'number')">Injuries</th>
            </tr>
          </thead>
          <tbody>
            ${teams.map((t, i) => renderRow(t, i)).join('')}
          </tbody>
        </table>
      </div>

      <div class="weights-section">
        <h3>Learned Feature Weights</h3>
        <div class="weight-bars">
          ${weights.slice(0, 8).map(w => `
            <div class="weight-row">
              <span class="weight-name">${w.name}</span>
              <div class="weight-bar-track">
                <div class="weight-bar-fill" style="width: ${Math.min(w.weight, 100)}%"></div>
              </div>
              <span class="weight-value">${w.weight.toFixed(1)}%</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    // Filter chips
    container.querySelectorAll('.chip').forEach(chip => {
      chip.addEventListener('click', () => {
        container.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        currentFilter = chip.dataset.filter;
        filterTable(container);
      });
    });
  }

  function renderTopCards(teams) {
    const top3 = teams.slice(0, 3);
    return top3.map((t, i) => `
      <div class="stat-card ${Utils.tierClass(t.tier)}">
        <div class="stat-card-rank">#${i + 1}</div>
        <div class="stat-card-team">${t.code}</div>
        <div class="stat-card-name">${t.name}</div>
        <div class="stat-card-value">${Utils.pct(t.cupProbability)}</div>
        <div class="stat-card-label">Cup probability</div>
      </div>
    `).join('');
  }

  function renderRow(team, idx) {
    const injCount = (team.injuries || []).length;
    const warLost = team.totalWarLost || 0;
    const injDisplay = injCount > 0 ? `${injCount} (${warLost.toFixed(1)})` : '-';

    return `
      <tr data-conference="${team.conference}" data-tier="${team.tier}">
        <td class="rank-cell">${team.rank}</td>
        <td class="team-cell">
          <span class="team-code">${team.code}</span>
          <span class="team-name-sub">${team.name}</span>
        </td>
        <td><span class="tier-badge" style="color:${team.tierColor};background:${team.tierBg}">${team.tier}</span></td>
        <td class="muted">${team.conference}</td>
        <td class="mono">${team.compositeStrength.toFixed(1)}</td>
        <td class="mono">${Utils.pct(team.playoffProbability)}</td>
        <td class="mono">${Utils.pct(team.conferenceProbability)}</td>
        <td class="mono bold">${Utils.pct(team.cupProbability)}</td>
        <td class="mono ${injCount > 3 ? 'text-warning' : ''}">${injDisplay}</td>
      </tr>
    `;
  }

  function filterTable(container) {
    const rows = container.querySelectorAll('#rankings-table tbody tr');
    rows.forEach(row => {
      if (currentFilter === 'all') {
        row.style.display = '';
      } else if (['East', 'West'].includes(currentFilter)) {
        row.style.display = row.dataset.conference === currentFilter ? '' : 'none';
      } else {
        row.style.display = row.dataset.tier === currentFilter ? '' : 'none';
      }
    });
  }

  return { render };
})();
