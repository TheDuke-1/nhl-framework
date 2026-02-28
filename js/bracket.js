/**
 * Bracket Tab - Full playoff bracket with Actual + Projected modes
 */
const Bracket = (() => {
  let mode = 'projected';

  function render(container, data) {
    const bracket = data.bracket || {};
    const roundAdv = data.roundAdvancement || {};
    const teams = data.teams || [];
    const meta = data.meta || {};
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
          ? renderProjectedBracket(bracket.projected, roundAdv, teamMap, teams, meta)
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

  function renderProjectedBracket(projected, roundAdv, teamMap, teams, meta) {
    if (!projected) return '<div class="bracket-empty">No projection data available</div>';

    const east = projected.East || {};
    const west = projected.West || {};
    const cupFinal = projected.cupFinal || [];
    const champion = projected.champion;
    const coherentPath = projected.coherentPath || buildCoherentPath(projected);
    const displayPath = buildCoherentPath(projected, coherentPath);
    const seedContexts = buildProjectedSeedContexts(projected, teams, teamMap);

    return `
      ${renderProjectedDataStrip(meta, seedContexts)}
      <div class="bracket-full">
        ${renderProjectedConf(east, teamMap, 'East', 'left', displayPath.East || null, seedContexts.East || null)}
        ${renderCenterColumn(cupFinal, champion, teamMap, 'projected', displayPath)}
        ${renderProjectedConf(west, teamMap, 'West', 'right', displayPath.West || null, seedContexts.West || null)}
      </div>
    `;
  }

  function renderProjectedConf(conf, teamMap, confName, side, coherentConfPath, seedContext) {
    const rawR1 = conf.round1 || [];
    const r1 = Array.isArray(coherentConfPath?.round1Ordered)
      ? coherentConfPath.round1Ordered
      : rawR1;
    const r2 = conf.round2 || [];
    const cf = conf.confFinal || [];
    const selectedR2 = Array.isArray(coherentConfPath?.round2Selected)
      ? coherentConfPath.round2Selected
      : extractDefaultR2Selected(r2);
    const selectedCF = coherentConfPath?.confFinalSelected || cf[0] || null;
    const seedAudit = auditRound1SeedAlignment(r1, seedContext);

    // For left side: R1 → R2 → CF
    // For right side: CF → R2 → R1
    const r1Col = renderR1Projected(r1, teamMap, seedContext, seedAudit);
    const r2Col = renderR2Projected(selectedR2, teamMap, seedContext);
    const cfCol = renderCFProjected(selectedCF, teamMap, confName, seedContext);
    const seedWarning = seedAudit.mismatchCount > 0
      ? `<div class="conf-seed-warning">${seedAudit.mismatchCount}/${Math.max(r1.length, 1)} Round 1 pairs differ from projected seed table.</div>`
      : '';

    if (side === 'left') {
      return `
        <div class="bracket-conf bracket-conf-left">
          <div class="conf-label">${confName}ern Conference</div>
          ${renderProjectedSeedStrip(seedContext)}
          ${seedWarning}
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
          ${renderProjectedSeedStrip(seedContext)}
          ${seedWarning}
          <div class="bracket-rounds">
            <div class="bracket-col">${colLabel('Conf Final')}${cfCol}</div>
            <div class="bracket-col">${colLabel('Round 2')}${r2Col}</div>
            <div class="bracket-col">${colLabel('Round 1')}${r1Col}</div>
          </div>
        </div>
      `;
    }
  }

  function renderR1Projected(matchups, teamMap, seedContext, seedAudit) {
    if (matchups.length === 0) return '<div class="bracket-slot-empty">TBD</div>'.repeat(4);
    const mismatchKeys = seedAudit?.mismatchKeys || new Set();
    return matchups.map(m => {
      const hProb = parsePercent(m.higherWinProb);
      const lProb = (100 - hProb).toFixed(1);
      const higherSeed = seedContext?.teamSeeds?.[m.higher] || null;
      const lowerSeed = seedContext?.teamSeeds?.[m.lower] || null;
      const higherPts = formatProjectedPoints(seedContext?.projectedPts?.[m.higher]);
      const lowerPts = formatProjectedPoints(seedContext?.projectedPts?.[m.lower]);
      const isSeedMismatch = mismatchKeys.has(matchupKey(m.higher, m.lower));
      return `
        <div class="bracket-matchup-card ${isSeedMismatch ? 'bm-seed-mismatch' : ''}">
          <div class="bm-team ${hProb >= 50 ? 'bm-favored' : ''}">
            ${higherSeed ? `<span class="bm-seed">${higherSeed}</span>` : ''}
            <span class="bm-code">${m.higher}</span>
            <span class="tier-dot" style="background:${Utils.tierColor((teamMap[m.higher]||{}).tier)}"></span>
            ${higherPts ? `<span class="bm-pts mono">${higherPts}</span>` : ''}
            <span class="bm-prob mono">${hProb.toFixed(1)}%</span>
          </div>
          <div class="bm-team ${hProb < 50 ? 'bm-favored' : ''}">
            ${lowerSeed ? `<span class="bm-seed">${lowerSeed}</span>` : ''}
            <span class="bm-code">${m.lower}</span>
            <span class="tier-dot" style="background:${Utils.tierColor((teamMap[m.lower]||{}).tier)}"></span>
            ${lowerPts ? `<span class="bm-pts mono">${lowerPts}</span>` : ''}
            <span class="bm-prob mono">${lProb}%</span>
          </div>
          ${isSeedMismatch ? '<div class="bm-seed-note">Seed mismatch</div>' : ''}
        </div>
      `;
    }).join('');
  }

  function renderR2Projected(selectedMatchups, teamMap, seedContext) {
    const pick = Array.isArray(selectedMatchups) ? selectedMatchups : [];
    const cards = [pick[0] || null, pick[1] || null];
    return cards.map((m) => m ? renderProbMatchup(m, teamMap, seedContext) : tbdCard()).join('');
  }

  function renderCFProjected(selectedMatchup, teamMap, confName, seedContext) {
    const m = selectedMatchup || null;
    if (!m) return tbdCard();
    return renderProbMatchup(m, teamMap, seedContext);
  }

  function renderProbMatchup(m, teamMap, seedContext) {
    const aProb = parsePercent(m.teamAWinProb);
    const bProb = (100 - aProb).toFixed(1);
    const freq = parsePercent(m.matchupProb);
    const teamASeed = seedContext?.teamSeeds?.[m.teamA] || null;
    const teamBSeed = seedContext?.teamSeeds?.[m.teamB] || null;
    const teamAPts = formatProjectedPoints(seedContext?.projectedPts?.[m.teamA]);
    const teamBPts = formatProjectedPoints(seedContext?.projectedPts?.[m.teamB]);
    return `
      <div class="bracket-matchup-card">
        <div class="bm-team ${aProb >= 50 ? 'bm-favored' : ''}">
          ${teamASeed ? `<span class="bm-seed">${teamASeed}</span>` : ''}
          <span class="bm-code">${m.teamA}</span>
          <span class="tier-dot" style="background:${Utils.tierColor((teamMap[m.teamA]||{}).tier)}"></span>
          ${teamAPts ? `<span class="bm-pts mono">${teamAPts}</span>` : ''}
          <span class="bm-prob mono">${aProb.toFixed(1)}%</span>
        </div>
        <div class="bm-team ${aProb < 50 ? 'bm-favored' : ''}">
          ${teamBSeed ? `<span class="bm-seed">${teamBSeed}</span>` : ''}
          <span class="bm-code">${m.teamB}</span>
          <span class="tier-dot" style="background:${Utils.tierColor((teamMap[m.teamB]||{}).tier)}"></span>
          ${teamBPts ? `<span class="bm-pts mono">${teamBPts}</span>` : ''}
          <span class="bm-prob mono">${bProb}%</span>
        </div>
        <div class="bm-freq mono">${freq.toFixed(1)}% of sims</div>
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

  function renderCenterColumn(cupFinal, champion, teamMap, bracketMode, coherentPath) {
    const selectedCup = coherentPath?.cupFinalSelected || (cupFinal && cupFinal[0]) || null;
    const coherentChampion = coherentPath?.champion || null;
    let cupContent = '';
    if (bracketMode === 'projected' && selectedCup) {
      const top = selectedCup;
      const topProb = parsePercent(top.teamAWinProb);
      cupContent = `
        <div class="cup-matchup">
          <div class="cup-team">
            <span class="bm-code">${top.teamA}</span>
            <span class="bm-prob mono">${topProb.toFixed(1)}%</span>
          </div>
          <div class="cup-vs">vs</div>
          <div class="cup-team">
            <span class="bm-code">${top.teamB}</span>
            <span class="bm-prob mono">${(100 - topProb).toFixed(1)}%</span>
          </div>
          <div class="bm-freq mono">${parsePercent(top.matchupProb).toFixed(1)}% of sims</div>
        </div>
      `;
    } else {
      cupContent = '<div class="cup-matchup"><div class="bm-code muted">TBD</div></div>';
    }

    let champContent = '';
    const championCard = coherentChampion || champion || null;
    if (bracketMode === 'projected' && championCard) {
      champContent = `
        <div class="cup-champion">
          <div class="champ-label">${coherentChampion ? 'Most-Likely Path Champion' : 'Projected Champion'}</div>
          <div class="champ-team">${championCard.team}</div>
          <div class="champ-prob mono">${championCard.probability}%</div>
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

  function tbdCard() {
    return '<div class="bracket-matchup-card bm-tbd"><div class="bm-team"><span class="bm-code muted">TBD</span></div><div class="bm-team"><span class="bm-code muted">TBD</span></div></div>';
  }

  function parsePercent(value) {
    const num = Number(value);
    if (!Number.isFinite(num)) return 0;
    return Math.max(0, Math.min(100, num));
  }

  function formatProjectedPoints(value) {
    const num = Number(value);
    if (!Number.isFinite(num)) return null;
    return `${num.toFixed(1)} pts`;
  }

  function formatSourceTimestamp(value) {
    if (!value) return null;
    const dt = new Date(value);
    if (Number.isNaN(dt.getTime())) return String(value);
    return dt.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function renderProjectedDataStrip(meta, seedContexts) {
    const lastUpdate = meta?.lastUpdate || meta?.generated || 'Unknown';
    const freshness = (meta?.sourceFreshness && typeof meta.sourceFreshness === 'object')
      ? meta.sourceFreshness
      : {};
    const sourceChips = Object.entries(freshness)
      .filter(([, value]) => Boolean(value))
      .map(([source, value]) => `
        <span class="projected-source-chip">
          <span class="projected-source-label">${source.toUpperCase()}</span>
          <span class="mono">${formatSourceTimestamp(value)}</span>
        </span>
      `)
      .join('');
    const fallbackConfs = Object.entries(seedContexts || {})
      .filter(([, context]) => context && context.source !== 'projected-seeds')
      .map(([conf]) => conf);
    const fallbackNote = fallbackConfs.length
      ? `<div class="projected-data-note">Using ${fallbackConfs.join('/')} fallback seeding from current playoff probabilities.</div>`
      : '';

    return `
      <div class="projected-data-strip">
        <div class="projected-data-main">
          <span class="projected-data-label">Projection Snapshot</span>
          <span class="projected-data-value mono">${lastUpdate}</span>
        </div>
        ${sourceChips ? `<div class="projected-data-sources">${sourceChips}</div>` : ''}
        ${fallbackNote}
      </div>
    `;
  }

  function renderProjectedSeedStrip(seedContext) {
    if (!seedContext || !Array.isArray(seedContext.seedRows) || seedContext.seedRows.length === 0) {
      return '';
    }
    return `
      <div class="conf-seed-strip">
        ${seedContext.seedRows.map((row) => `
          <span class="conf-seed-pill ${row.seed.startsWith('WC') ? 'is-wildcard' : ''}">
            <span class="mono">${row.seed}</span>
            <span>${row.team}</span>
          </span>
        `).join('')}
      </div>
    `;
  }

  function pickSeriesWinner(matchup) {
    if (!matchup) return null;
    return Number(matchup.teamAWinProb) >= 50 ? matchup.teamA : matchup.teamB;
  }

  function selectMatchingMatchup(matchups, teamA, teamB) {
    if (!Array.isArray(matchups) || !matchups.length) return null;
    if (teamA && teamB) {
      const wanted = new Set([teamA, teamB]);
      const exact = matchups.find((m) => new Set([m.teamA, m.teamB]).size === 2
        && wanted.has(m.teamA)
        && wanted.has(m.teamB));
      if (exact) return exact;
    }
    return matchups[0];
  }

  function extractDefaultR2Selected(round2Slots) {
    if (!Array.isArray(round2Slots)) return [null, null];
    const bySlot = {};
    round2Slots.forEach((slotData, idx) => {
      const slot = Number.isInteger(slotData?.slot) ? slotData.slot : idx;
      const first = Array.isArray(slotData?.matchups) ? (slotData.matchups[0] || null) : null;
      bySlot[slot] = first;
    });
    return [bySlot[0] || null, bySlot[1] || null];
  }

  function buildProjectedSeedContexts(projected, teams, teamMap) {
    return {
      East: buildConferenceSeedContext('East', projected, teams, teamMap),
      West: buildConferenceSeedContext('West', projected, teams, teamMap),
    };
  }

  function buildConferenceSeedContext(confName, projected, teams, teamMap) {
    const sourceRows = Array.isArray(projected?.projectedSeeds?.[confName])
      ? projected.projectedSeeds[confName]
      : [];
    const fromProjected = sourceRows
      .filter((row) => row && row.team)
      .slice(0, 8)
      .map((row) => ({
        team: row.team,
        projectedPts: Number.isFinite(Number(row.projectedPts)) ? Number(row.projectedPts) : null,
      }));

    if (fromProjected.length >= 8) {
      return buildSeedContextFromRows(fromProjected, teamMap, 'projected-seeds');
    }

    const fromTeams = (teams || [])
      .filter((team) => team.conference === confName)
      .sort((a, b) => Number(b.playoffProbability || 0) - Number(a.playoffProbability || 0))
      .slice(0, 8)
      .map((team) => ({ team: team.code, projectedPts: null }));
    return buildSeedContextFromRows(fromTeams, teamMap, 'teams-fallback');
  }

  function buildSeedContextFromRows(rawRows, teamMap, source) {
    const seen = new Set();
    const rows = rawRows
      .filter((row) => row && row.team && !seen.has(row.team) && seen.add(row.team))
      .slice(0, 8);
    if (rows.length === 0) {
      return { source, seedRows: [], teamSeeds: {}, projectedPts: {}, expectedRound1: [] };
    }

    const projectedPts = {};
    rows.forEach((row) => {
      projectedPts[row.team] = row.projectedPts;
    });

    const divisions = {};
    rows.forEach((row) => {
      const division = teamMap[row.team]?.division || '';
      if (!division) return;
      if (!divisions[division]) divisions[division] = [];
      divisions[division].push(row);
    });

    const divisionNames = Object.keys(divisions).sort();
    if (divisionNames.length !== 2) {
      return buildGenericSeedContext(rows, teamMap, projectedPts, source);
    }

    const divAName = divisionNames[0];
    const divBName = divisionNames[1];
    const divA = divisions[divAName].slice().sort((a, b) => compareSeedRows(a, b, teamMap));
    const divB = divisions[divBName].slice().sort((a, b) => compareSeedRows(a, b, teamMap));
    const divATop3 = divA.slice(0, 3);
    const divBTop3 = divB.slice(0, 3);
    if (divATop3.length < 3 || divBTop3.length < 3) {
      return buildGenericSeedContext(rows, teamMap, projectedPts, source);
    }

    const wildcardPool = divA.slice(3).concat(divB.slice(3)).sort((a, b) => compareSeedRows(a, b, teamMap));
    const wc1 = wildcardPool[0] || null;
    const wc2 = wildcardPool[1] || null;
    if (!wc1 || !wc2) {
      return buildGenericSeedContext(rows, teamMap, projectedPts, source);
    }

    const aIsSeed1 = compareSeedRows(divATop3[0], divBTop3[0], teamMap) <= 0;
    const seed1Top3 = aIsSeed1 ? divATop3 : divBTop3;
    const seed2Top3 = aIsSeed1 ? divBTop3 : divATop3;

    const prefixMap = {
      Atlantic: 'A',
      Metropolitan: 'M',
      Central: 'C',
      Pacific: 'P',
    };
    const teamSeeds = {};
    [divATop3, divBTop3].forEach((divRows) => {
      const division = teamMap[divRows[0]?.team]?.division || '';
      const prefix = prefixMap[division] || (division[0] || 'D').toUpperCase();
      divRows.forEach((row, idx) => {
        teamSeeds[row.team] = `${prefix}${idx + 1}`;
      });
    });
    teamSeeds[wc1.team] = 'WC1';
    teamSeeds[wc2.team] = 'WC2';

    const expectedRound1 = [
      {
        higher: seed1Top3[0].team,
        lower: wc2.team,
        higherSeed: teamSeeds[seed1Top3[0].team],
        lowerSeed: teamSeeds[wc2.team],
      },
      {
        higher: seed1Top3[1].team,
        lower: seed1Top3[2].team,
        higherSeed: teamSeeds[seed1Top3[1].team],
        lowerSeed: teamSeeds[seed1Top3[2].team],
      },
      {
        higher: seed2Top3[0].team,
        lower: wc1.team,
        higherSeed: teamSeeds[seed2Top3[0].team],
        lowerSeed: teamSeeds[wc1.team],
      },
      {
        higher: seed2Top3[1].team,
        lower: seed2Top3[2].team,
        higherSeed: teamSeeds[seed2Top3[1].team],
        lowerSeed: teamSeeds[seed2Top3[2].team],
      },
    ];

    const seedRows = [
      { seed: teamSeeds[seed1Top3[0].team], team: seed1Top3[0].team, projectedPts: projectedPts[seed1Top3[0].team] },
      { seed: teamSeeds[seed1Top3[1].team], team: seed1Top3[1].team, projectedPts: projectedPts[seed1Top3[1].team] },
      { seed: teamSeeds[seed1Top3[2].team], team: seed1Top3[2].team, projectedPts: projectedPts[seed1Top3[2].team] },
      { seed: teamSeeds[seed2Top3[0].team], team: seed2Top3[0].team, projectedPts: projectedPts[seed2Top3[0].team] },
      { seed: teamSeeds[seed2Top3[1].team], team: seed2Top3[1].team, projectedPts: projectedPts[seed2Top3[1].team] },
      { seed: teamSeeds[seed2Top3[2].team], team: seed2Top3[2].team, projectedPts: projectedPts[seed2Top3[2].team] },
      { seed: 'WC1', team: wc1.team, projectedPts: projectedPts[wc1.team] },
      { seed: 'WC2', team: wc2.team, projectedPts: projectedPts[wc2.team] },
    ];

    return { source, seedRows, teamSeeds, projectedPts, expectedRound1 };
  }

  function buildGenericSeedContext(rows, teamMap, projectedPts, source) {
    const ordered = rows.slice().sort((a, b) => compareSeedRows(a, b, teamMap));
    const teamSeeds = {};
    ordered.forEach((row, idx) => {
      teamSeeds[row.team] = `S${idx + 1}`;
    });
    const seedRows = ordered.map((row, idx) => ({
      seed: `S${idx + 1}`,
      team: row.team,
      projectedPts: projectedPts[row.team],
    }));
    const expectedRound1 = ordered.length >= 8 ? [
      { higher: ordered[0].team, lower: ordered[7].team },
      { higher: ordered[1].team, lower: ordered[6].team },
      { higher: ordered[2].team, lower: ordered[5].team },
      { higher: ordered[3].team, lower: ordered[4].team },
    ] : [];
    return { source, seedRows, teamSeeds, projectedPts, expectedRound1 };
  }

  function compareSeedRows(a, b, teamMap) {
    const aPts = Number(a?.projectedPts);
    const bPts = Number(b?.projectedPts);
    const aHasPts = Number.isFinite(aPts);
    const bHasPts = Number.isFinite(bPts);
    if (aHasPts && bHasPts && aPts !== bPts) return bPts - aPts;
    if (aHasPts !== bHasPts) return aHasPts ? -1 : 1;

    const aPlayoff = Number(teamMap[a?.team]?.playoffProbability || 0);
    const bPlayoff = Number(teamMap[b?.team]?.playoffProbability || 0);
    if (aPlayoff !== bPlayoff) return bPlayoff - aPlayoff;
    return String(a?.team || '').localeCompare(String(b?.team || ''));
  }

  function auditRound1SeedAlignment(round1, seedContext) {
    const expected = Array.isArray(seedContext?.expectedRound1) ? seedContext.expectedRound1 : [];
    if (!expected.length || !Array.isArray(round1) || round1.length === 0) {
      return { mismatchCount: 0, mismatchKeys: new Set() };
    }
    const expectedKeys = new Set(expected.map((matchup) => matchupKey(matchup.higher, matchup.lower)));
    const mismatchKeys = new Set();
    round1.forEach((matchup) => {
      const key = matchupKey(matchup.higher, matchup.lower);
      if (!expectedKeys.has(key)) mismatchKeys.add(key);
    });
    return { mismatchCount: mismatchKeys.size, mismatchKeys };
  }

  function buildRound2SlotMap(round2Slots) {
    const slotMap = { 0: [], 1: [] };
    if (!Array.isArray(round2Slots)) return slotMap;
    round2Slots.forEach((slotData, idx) => {
      const slot = Number.isInteger(slotData?.slot) ? slotData.slot : idx;
      if (slot !== 0 && slot !== 1) return;
      slotMap[slot] = Array.isArray(slotData?.matchups) ? slotData.matchups : [];
    });
    return slotMap;
  }

  function orderRound1BySlots(round1, slotMap) {
    if (!Array.isArray(round1) || round1.length !== 4) return Array.isArray(round1) ? round1 : [];
    const slot0Teams = new Set();
    const slot1Teams = new Set();
    (slotMap[0] || []).forEach((matchup) => {
      slot0Teams.add(matchup.teamA);
      slot0Teams.add(matchup.teamB);
    });
    (slotMap[1] || []).forEach((matchup) => {
      slot1Teams.add(matchup.teamA);
      slot1Teams.add(matchup.teamB);
    });
    if (slot0Teams.size === 0 || slot1Teams.size === 0) return round1;

    const grouped = { 0: [], 1: [], unknown: [] };
    round1.forEach((matchup, idx) => {
      const score0 = (slot0Teams.has(matchup.higher) ? 1 : 0) + (slot0Teams.has(matchup.lower) ? 1 : 0);
      const score1 = (slot1Teams.has(matchup.higher) ? 1 : 0) + (slot1Teams.has(matchup.lower) ? 1 : 0);
      if (score0 > score1) grouped[0].push({ idx, matchup });
      else if (score1 > score0) grouped[1].push({ idx, matchup });
      else grouped.unknown.push({ idx, matchup });
    });

    if (grouped[0].length === 2 && grouped[1].length === 2 && grouped.unknown.length === 0) {
      grouped[0].sort((a, b) => a.idx - b.idx);
      grouped[1].sort((a, b) => a.idx - b.idx);
      return grouped[0].concat(grouped[1]).map((entry) => entry.matchup);
    }
    return round1;
  }

  function matchupKey(teamA, teamB) {
    return [String(teamA || ''), String(teamB || '')].sort().join('__');
  }

  function buildCoherentPath(projected, preferredPath = null) {
    const out = { East: null, West: null, cupFinalSelected: null, champion: null };
    if (!projected || typeof projected !== 'object') return out;

    ['East', 'West'].forEach((confName) => {
      const conf = projected[confName] || {};
      const r1Raw = Array.isArray(conf.round1) ? conf.round1 : [];
      const r2 = Array.isArray(conf.round2) ? conf.round2 : [];
      const cf = Array.isArray(conf.confFinal) ? conf.confFinal : [];
      const slotMap = buildRound2SlotMap(r2);
      const r1 = orderRound1BySlots(r1Raw, slotMap);

      const r1Winners = r1.map((m) => Number(m.higherWinProb) >= 50 ? m.higher : m.lower);

      const slot0 = selectMatchingMatchup(slotMap[0] || [], r1Winners[0], r1Winners[1]);
      const slot1 = selectMatchingMatchup(slotMap[1] || [], r1Winners[2], r1Winners[3]);
      const r2Winners = [pickSeriesWinner(slot0), pickSeriesWinner(slot1)];
      const cfSelected = selectMatchingMatchup(cf, r2Winners[0], r2Winners[1]);
      const confChampion = pickSeriesWinner(cfSelected);

      out[confName] = {
        round1Ordered: r1,
        round1Winners: r1Winners,
        round2Selected: [slot0, slot1],
        round2Winners: r2Winners,
        confFinalSelected: cfSelected,
        confChampion,
      };
    });

    const cupFinal = Array.isArray(projected.cupFinal) ? projected.cupFinal : [];
    const eastChamp = out.East?.confChampion || null;
    const westChamp = out.West?.confChampion || null;
    const preferredCupFinal = preferredPath?.cupFinalSelected || null;
    out.cupFinalSelected = selectMatchingMatchup(cupFinal, eastChamp, westChamp)
      || selectMatchingMatchup(cupFinal, preferredCupFinal?.teamA, preferredCupFinal?.teamB)
      || preferredCupFinal
      || cupFinal[0]
      || null;
    if (out.cupFinalSelected) {
      const team = Number(out.cupFinalSelected.teamAWinProb) >= 50
        ? out.cupFinalSelected.teamA
        : out.cupFinalSelected.teamB;
      const probability = Math.max(
        Number(out.cupFinalSelected.teamAWinProb) || 0,
        100 - (Number(out.cupFinalSelected.teamAWinProb) || 0),
      );
      out.champion = { team, probability: Number(probability.toFixed(1)), source: 'coherent_path' };
    }
    return out;
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
