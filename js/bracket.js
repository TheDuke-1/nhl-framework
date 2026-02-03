/**
 * Bracket Tab - Full playoff bracket with Actual + Projected modes
 */
const Bracket = (() => {
  let mode = 'projected';

  function render(container, data) {
    const bracket = data.bracket || {};
    const roundAdv = data.roundAdvancement || {};
    const teams = data.teams || [];
    const teamMap = {};
    teams.forEach(t => { teamMap[t.code] = t; });

    const hasActual = bracket.actual && (bracket.actual.East || bracket.actual.West);

    container.innerHTML = `
      <div class="tab-header">
        <h2>Playoff Bracket</h2>
        <div class="filter-chips">
          <button class="chip ${mode === 'projected' ? 'active' : ''}" data-mode="projected">Projected</button>
          <button class="chip ${mode === 'actual' ? 'active' : ''}" data-mode="actual"
            ${!hasActual ? 'disabled title="No standings data available"' : ''}>Actual</button>
        </div>
      </div>

      <div class="bracket-full-container">
        ${mode === 'projected'
          ? renderProjectedBracket(bracket.projected, roundAdv, teamMap)
          : renderActualBracket(bracket.actual, teamMap)}
      </div>

      <div class="advancement-section">
        <h3>Round Advancement Probabilities</h3>
        ${renderAdvancementTable(roundAdv, teamMap, teams)}
      </div>
    `;

    // Mode toggle
    container.querySelectorAll('.chip[data-mode]').forEach(chip => {
      chip.addEventListener('click', () => {
        if (chip.disabled) return;
        mode = chip.dataset.mode;
        render(container, data);
      });
    });
  }

  // ── Projected Bracket ──────────────────────────────────────────

  function renderProjectedBracket(projected, roundAdv, teamMap) {
    if (!projected) return '<div class="bracket-empty">No projection data available</div>';

    const east = projected.East || {};
    const west = projected.West || {};
    const cupFinal = projected.cupFinal || [];
    const champion = projected.champion;

    return `
      <div class="bracket-full">
        ${renderProjectedConf(east, teamMap, 'East', 'left')}
        ${renderCenterColumn(cupFinal, champion, teamMap, 'projected')}
        ${renderProjectedConf(west, teamMap, 'West', 'right')}
      </div>
    `;
  }

  function renderProjectedConf(conf, teamMap, confName, side) {
    const r1 = conf.round1 || [];
    const r2 = conf.round2 || [];
    const cf = conf.confFinal || [];

    // For left side: R1 → R2 → CF
    // For right side: CF → R2 → R1
    const r1Col = renderR1Projected(r1, teamMap);
    const r2Col = renderR2Projected(r2, teamMap);
    const cfCol = renderCFProjected(cf, teamMap, confName);

    if (side === 'left') {
      return `
        <div class="bracket-conf bracket-conf-left">
          <div class="conf-label">${confName}ern Conference</div>
          <div class="bracket-rounds">
            <div class="bracket-col">${colLabel('Round 1')}${r1Col}</div>
            <div class="bracket-col">${colLabel('Round 2')}${r2Col}</div>
            <div class="bracket-col">${colLabel('Conf Final')}${cfCol}</div>
          </div>
        </div>
      `;
    } else {
      return `
        <div class="bracket-conf bracket-conf-right">
          <div class="conf-label">${confName}ern Conference</div>
          <div class="bracket-rounds">
            <div class="bracket-col">${colLabel('Conf Final')}${cfCol}</div>
            <div class="bracket-col">${colLabel('Round 2')}${r2Col}</div>
            <div class="bracket-col">${colLabel('Round 1')}${r1Col}</div>
          </div>
        </div>
      `;
    }
  }

  function renderR1Projected(matchups, teamMap) {
    if (matchups.length === 0) return '<div class="bracket-slot-empty">TBD</div>'.repeat(4);
    return matchups.map(m => {
      const hProb = m.higherWinProb;
      const lProb = (100 - hProb).toFixed(1);
      return `
        <div class="bracket-matchup-card">
          <div class="bm-team ${hProb >= 50 ? 'bm-favored' : ''}">
            <span class="bm-code">${m.higher}</span>
            <span class="tier-dot" style="background:${Utils.tierColor((teamMap[m.higher]||{}).tier)}"></span>
            <span class="bm-prob mono">${hProb}%</span>
          </div>
          <div class="bm-team ${hProb < 50 ? 'bm-favored' : ''}">
            <span class="bm-code">${m.lower}</span>
            <span class="tier-dot" style="background:${Utils.tierColor((teamMap[m.lower]||{}).tier)}"></span>
            <span class="bm-prob mono">${lProb}%</span>
          </div>
        </div>
      `;
    }).join('');
  }

  function renderR2Projected(matchups, teamMap) {
    if (matchups.length === 0) {
      return `
        <div class="bracket-matchup-card bm-tbd"><div class="bm-team"><span class="bm-code muted">TBD</span></div><div class="bm-team"><span class="bm-code muted">TBD</span></div></div>
        <div class="bracket-matchup-card bm-tbd"><div class="bm-team"><span class="bm-code muted">TBD</span></div><div class="bm-team"><span class="bm-code muted">TBD</span></div></div>
      `;
    }
    // Group R2 matchups into bracket slots (up to 2 slots per conference)
    // Show the most likely matchup per slot, with matchupProb as subtitle
    // We have up to 3 matchups, try to identify which go into which slot
    const slot1 = matchups[0] || null;
    const slot2 = matchups[1] || null;

    return [slot1, slot2].map(m => {
      if (!m) return '<div class="bracket-matchup-card bm-tbd"><div class="bm-team"><span class="bm-code muted">TBD</span></div><div class="bm-team"><span class="bm-code muted">TBD</span></div></div>';
      return renderProbMatchup(m, teamMap);
    }).join('');
  }

  function renderCFProjected(matchups, teamMap, confName) {
    const m = matchups[0] || null;
    if (!m) return '<div class="bracket-matchup-card bm-tbd"><div class="bm-team"><span class="bm-code muted">TBD</span></div><div class="bm-team"><span class="bm-code muted">TBD</span></div></div>';
    return renderProbMatchup(m, teamMap);
  }

  function renderProbMatchup(m, teamMap) {
    const aProb = m.teamAWinProb;
    const bProb = (100 - aProb).toFixed(1);
    const freq = m.matchupProb;
    return `
      <div class="bracket-matchup-card">
        <div class="bm-team ${aProb >= 50 ? 'bm-favored' : ''}">
          <span class="bm-code">${m.teamA}</span>
          <span class="tier-dot" style="background:${Utils.tierColor((teamMap[m.teamA]||{}).tier)}"></span>
          <span class="bm-prob mono">${aProb}%</span>
        </div>
        <div class="bm-team ${aProb < 50 ? 'bm-favored' : ''}">
          <span class="bm-code">${m.teamB}</span>
          <span class="tier-dot" style="background:${Utils.tierColor((teamMap[m.teamB]||{}).tier)}"></span>
          <span class="bm-prob mono">${bProb}%</span>
        </div>
        <div class="bm-freq mono">${freq}% of sims</div>
      </div>
    `;
  }

  // ── Actual Bracket ──────────────────────────────────────────

  function renderActualBracket(actual, teamMap) {
    if (!actual) return '<div class="bracket-empty">No standings data available</div>';

    const east = actual.East || {};
    const west = actual.West || {};

    return `
      <div class="bracket-full">
        ${renderActualConf(east, teamMap, 'East', 'left')}
        ${renderCenterColumn([], null, teamMap, 'actual')}
        ${renderActualConf(west, teamMap, 'West', 'right')}
      </div>
    `;
  }

  function renderActualConf(conf, teamMap, confName, side) {
    const r1 = conf.round1 || [];
    const r1Col = r1.length > 0 ? r1.map(m => `
      <div class="bracket-matchup-card">
        <div class="bm-team">
          <span class="bm-seed">${m.higherSeed}</span>
          <span class="bm-code">${m.higher}</span>
          <span class="tier-dot" style="background:${Utils.tierColor((teamMap[m.higher]||{}).tier)}"></span>
        </div>
        <div class="bm-team">
          <span class="bm-seed">${m.lowerSeed}</span>
          <span class="bm-code">${m.lower}</span>
          <span class="tier-dot" style="background:${Utils.tierColor((teamMap[m.lower]||{}).tier)}"></span>
        </div>
      </div>
    `).join('') : '<div class="bracket-empty">No data</div>';

    const tbdSlot = '<div class="bracket-matchup-card bm-tbd"><div class="bm-team"><span class="bm-code muted">TBD</span></div><div class="bm-team"><span class="bm-code muted">TBD</span></div></div>';
    const r2Col = tbdSlot + tbdSlot;
    const cfCol = tbdSlot;

    if (side === 'left') {
      return `
        <div class="bracket-conf bracket-conf-left">
          <div class="conf-label">${confName}ern Conference</div>
          <div class="bracket-rounds">
            <div class="bracket-col">${colLabel('Round 1')}${r1Col}</div>
            <div class="bracket-col">${colLabel('Round 2')}${r2Col}</div>
            <div class="bracket-col">${colLabel('Conf Final')}${cfCol}</div>
          </div>
        </div>
      `;
    } else {
      return `
        <div class="bracket-conf bracket-conf-right">
          <div class="conf-label">${confName}ern Conference</div>
          <div class="bracket-rounds">
            <div class="bracket-col">${colLabel('Conf Final')}${cfCol}</div>
            <div class="bracket-col">${colLabel('Round 2')}${r2Col}</div>
            <div class="bracket-col">${colLabel('Round 1')}${r1Col}</div>
          </div>
        </div>
      `;
    }
  }

  // ── Center Column (Cup Final + Champion) ───────────────────

  function renderCenterColumn(cupFinal, champion, teamMap, bracketMode) {
    let cupContent = '';
    if (bracketMode === 'projected' && cupFinal && cupFinal.length > 0) {
      const top = cupFinal[0];
      cupContent = `
        <div class="cup-matchup">
          <div class="cup-team">
            <span class="bm-code">${top.teamA}</span>
            <span class="bm-prob mono">${top.teamAWinProb}%</span>
          </div>
          <div class="cup-vs">vs</div>
          <div class="cup-team">
            <span class="bm-code">${top.teamB}</span>
            <span class="bm-prob mono">${(100 - top.teamAWinProb).toFixed(1)}%</span>
          </div>
          <div class="bm-freq mono">${top.matchupProb}% of sims</div>
        </div>
      `;
    } else {
      cupContent = '<div class="cup-matchup"><div class="bm-code muted">TBD</div></div>';
    }

    let champContent = '';
    if (bracketMode === 'projected' && champion) {
      champContent = `
        <div class="cup-champion">
          <div class="champ-label">Projected Champion</div>
          <div class="champ-team">${champion.team}</div>
          <div class="champ-prob mono">${champion.probability}%</div>
        </div>
      `;
    }

    return `
      <div class="bracket-center">
        <div class="cup-trophy-label">Stanley Cup Final</div>
        ${cupContent}
        ${champContent}
      </div>
    `;
  }

  // ── Helpers ─────────────────────────────────────────────────

  function colLabel(text) {
    return `<div class="bracket-col-label">${text}</div>`;
  }

  // ── Advancement Table (unchanged) ──────────────────────────

  function renderAdvancementTable(roundAdv, teamMap, teams) {
    const sorted = teams
      .map(t => ({
        code: t.code,
        tier: t.tier,
        ...roundAdv[t.code]
      }))
      .filter(t => (t.round1 || 0) > 0)
      .sort((a, b) => (b.cupWin || 0) - (a.cupWin || 0))
      .slice(0, 16);

    if (sorted.length === 0) {
      return '<p class="muted">No advancement data available</p>';
    }

    return `
      <table class="data-table compact">
        <thead>
          <tr>
            <th>Team</th>
            <th>Win R1</th>
            <th>Win R2</th>
            <th>Conf Final</th>
            <th>Cup Final</th>
            <th>Win Cup</th>
          </tr>
        </thead>
        <tbody>
          ${sorted.map(t => `
            <tr>
              <td>
                <span class="team-code">${t.code}</span>
                <span class="tier-dot" style="background:${Utils.tierColor(t.tier)}"></span>
              </td>
              <td class="mono">${Utils.pct(t.round1)}</td>
              <td class="mono">${Utils.pct(t.round2)}</td>
              <td class="mono">${Utils.pct(t.confFinal)}</td>
              <td class="mono">${Utils.pct(t.cupFinal)}</td>
              <td class="mono bold">${Utils.pct(t.cupWin)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  return { render };
})();
