/**
 * Model Performance Tab - Backtest results and validation metrics
 */
const Performance = (() => {
  function render(container, data) {
    const backtest = data.backtest || {};
    const benchmark = data.benchmark || null;
    const releaseCycle = data.releaseCycle || null;
    const edgeResearch = data.edgeResearch || {};
    const seasons = backtest.seasons || [];
    const summary = backtest.summary || {};

    container.innerHTML = `
      <div class="tab-header">
        <h2>Model Performance</h2>
        <p class="tab-subtitle">Leave-one-season-out backtesting across ${summary.totalSeasons || 0} historical seasons.</p>
      </div>

      ${renderExecutiveScorecard(benchmark, releaseCycle, data.meta || {})}

      ${renderGoalRunwaySection(benchmark, edgeResearch)}

      ${renderSummaryCards(summary)}

      ${renderBenchmarkSection(benchmark)}

      <div class="section">
        <h3>Season-by-Season Results</h3>
        ${seasons.length > 0 ? renderSeasonTable(seasons) : '<p class="muted">No backtest data available. Run the backtest manually to generate.</p>'}
      </div>

      <div class="section">
        <h3>How to Read This</h3>
        <div class="info-card">
          <p>The model is trained on all seasons <em>except</em> the tested one, then predicts that season blind.</p>
          <p>Core objective metrics are Cup Top-1, Cup Top-5, Playoff F1, and average winner rank.</p>
          <p>Probability quality metrics (Brier, log loss, calibration error) must stay stable or improve as ranking accuracy improves.</p>
          <p>Vegas comparison becomes active automatically once historical market files are available.</p>
        </div>
      </div>
    `;
  }

  function renderExecutiveScorecard(benchmark, releaseCycle, meta) {
    const current = benchmark?.current || null;
    if (!current) {
      return `
        <div class="section">
          <h3>Executive Scorecard</h3>
          <div class="info-card">
            <p>Benchmark scorecard unavailable in this environment.</p>
          </div>
        </div>
      `;
    }

    const vegas = current.vegas || {};
    const cupTarget = vegas.cup_target || {};
    const releaseFloorMet = cupTarget.release_floor_met === true || cupTarget.goal_met === true;
    const strongMet = cupTarget.strong_met === true;
    const relativeEdge = vegas.cup_relative_brier_edge;
    const ciLow = vegas.cup_relative_brier_edge_ci_low;
    const ciHigh = vegas.cup_relative_brier_edge_ci_high;
    const goalTier = resolveGoalTier(cupTarget, relativeEdge);
    const goalTierLabel = renderGoalTierLabel(goalTier);
    const positiveRatio = vegas.cup_positive_season_ratio;
    const positiveSeasons = vegas.cup_positive_seasons;
    const totalSeasons = vegas.cup_total_seasons;
    const releaseStatus = releaseCycle?.status || meta.releaseStatus || 'UNKNOWN';
    const core = current.core || {};
    const quality = current.quality || {};
    const modelQualityPass = (
      Number(core.top1_accuracy_pct || 0) >= 12 &&
      Number(core.top5_accuracy_pct || 0) >= 45 &&
      Number(core.playoff_f1 || 0) >= 0.9 &&
      Number(core.average_winner_rank || 999) <= 8 &&
      Number(quality.brier_cup || 1) <= 0.06
    );
    const releaseReady = releaseStatus === 'PASS' && releaseFloorMet;
    const benchmarkAgeDays = getAgeDays(current.timestamp);
    const modelAgeDays = getAgeDays(meta.generated);
    const alerts = [];

    if (!releaseFloorMet) {
      alerts.push('Cup-vs-Vegas release-floor target is not yet passing.');
    }
    if (releaseFloorMet && !strongMet) {
      alerts.push('Cup target is currently at release-floor tier; strong tier is still pending.');
    }
    if (releaseStatus !== 'PASS') {
      alerts.push(`Release cycle status is ${releaseStatus}.`);
    }
    if (modelAgeDays != null && modelAgeDays > 2) {
      alerts.push(`Model output is stale (${Math.floor(modelAgeDays)} day(s) old).`);
    }
    if (benchmarkAgeDays != null && benchmarkAgeDays > 2) {
      alerts.push(`Benchmark scorecard is stale (${Math.floor(benchmarkAgeDays)} day(s) old).`);
    }

    return `
      <div class="section">
        <h3>Executive Scorecard</h3>
        <div class="scorecard-grid">
          <div class="info-card">
            <p><strong>Top-Level Status</strong></p>
            <p class="${modelQualityPass ? 'text-positive' : 'text-negative'} mono">Model Quality: ${modelQualityPass ? 'PASS' : 'WATCH'}</p>
            <p class="${releaseReady ? 'text-positive' : 'text-negative'} mono">Release Ready: ${releaseReady ? 'YES' : 'NO'}</p>
            <p>Release cycle: ${releaseStatus}</p>
            <p>Cup release floor: ${releaseFloorMet ? 'PASS' : 'FAIL'}</p>
            <p>Goal tier: ${goalTierLabel}</p>
          </div>
          <div class="info-card">
            <p><strong>Cup Relative Brier Edge vs Vegas</strong></p>
            <p class="${releaseFloorMet ? 'text-positive' : 'text-negative'} mono">${formatPct(relativeEdge)}</p>
            <p>Targets (floor/strong/stretch/moonshot): ${formatPct(cupTarget.relative_brier_improvement_min)} / ${formatPct(cupTarget.relative_brier_improvement_strong)} / ${formatPct(cupTarget.relative_brier_improvement_stretch)} / ${formatPct(cupTarget.relative_brier_improvement_moonshot)}</p>
            <p>CI (${((cupTarget.confidence_level || 0.95) * 100).toFixed(0)}%): [${formatPct(ciLow)}, ${formatPct(ciHigh)}]</p>
            <p>Positive seasons: ${positiveSeasons ?? '--'}/${totalSeasons ?? '--'} (${formatPct(positiveRatio)})</p>
          </div>
          <div class="info-card">
            <p><strong>Release Gate</strong></p>
            <p class="${releaseStatus === 'PASS' ? 'text-positive' : 'text-negative'} mono">${releaseStatus}</p>
            <p>Benchmark timestamp: ${formatTimestamp(current.timestamp)}</p>
            <p>Model timestamp: ${formatTimestamp(meta.generated)}</p>
            <p>Vegas coverage: ${vegas.available ? `active (${(vegas.seasons_available || []).length} seasons)` : 'unavailable'}</p>
          </div>
        </div>
        ${alerts.length ? `
          <div class="info-card mt-md">
            <p><strong>Active Alerts</strong></p>
            ${alerts.map(a => `<p class="text-warning">${a}</p>`).join('')}
          </div>
        ` : `
          <div class="info-card mt-md">
            <p class="text-positive"><strong>No active release alerts.</strong></p>
          </div>
        `}
      </div>
    `;
  }

  function renderSummaryCards(summary) {
    if (!summary.totalSeasons) {
      return '<div class="stat-cards"><div class="stat-card"><div class="stat-card-value">--</div><div class="stat-card-label">No backtest data</div></div></div>';
    }

    const topPickPct = summary.topPickAccuracy || 0;
    const top5Pct = summary.top5Accuracy || 0;

    return `
      <div class="stat-cards">
        <div class="stat-card">
          <div class="stat-card-value">${summary.totalSeasons}</div>
          <div class="stat-card-label">Seasons tested</div>
        </div>
        <div class="stat-card">
          <div class="stat-card-value">${summary.topPickCorrect}/${summary.totalSeasons}</div>
          <div class="stat-card-label">Top pick correct (${topPickPct}%)</div>
        </div>
        <div class="stat-card ${top5Pct >= 30 ? 'card-positive' : ''}">
          <div class="stat-card-value">${summary.winnerInTop5}/${summary.totalSeasons}</div>
          <div class="stat-card-label">Winner in top 5 (${top5Pct}%)</div>
        </div>
        <div class="stat-card">
          <div class="stat-card-value">${summary.averagePlayoffF1?.toFixed(3) ?? '--'}</div>
          <div class="stat-card-label">Playoff F1</div>
        </div>
        <div class="stat-card">
          <div class="stat-card-value">${summary.averageWinnerRank?.toFixed(2) ?? '--'}</div>
          <div class="stat-card-label">Avg winner rank (lower better)</div>
        </div>
      </div>
    `;
  }

  function renderGoalRunwaySection(benchmark, edgeResearch) {
    const current = benchmark?.current || null;
    if (!current) {
      return '';
    }

    const vegas = current.vegas || {};
    const cupTarget = vegas.cup_target || {};
    const edge = vegas.cup_relative_brier_edge;
    const ciLow = vegas.cup_relative_brier_edge_ci_low;
    const ratio = vegas.cup_positive_season_ratio;

    const targetEdge = isFiniteNumber(cupTarget.relative_brier_improvement_min) ? cupTarget.relative_brier_improvement_min : null;
    const targetStrong = isFiniteNumber(cupTarget.relative_brier_improvement_strong) ? cupTarget.relative_brier_improvement_strong : null;
    const targetStretch = isFiniteNumber(cupTarget.relative_brier_improvement_stretch) ? cupTarget.relative_brier_improvement_stretch : null;
    const targetMoonshot = isFiniteNumber(cupTarget.relative_brier_improvement_moonshot) ? cupTarget.relative_brier_improvement_moonshot : null;
    const targetCiLow = isFiniteNumber(cupTarget.ci_lower_bound_min) ? cupTarget.ci_lower_bound_min : 0.0;
    const targetRatio = isFiniteNumber(cupTarget.min_positive_season_ratio) ? cupTarget.min_positive_season_ratio : 0.60;

    const edgeGap = isFiniteNumber(edge) && isFiniteNumber(targetEdge) ? targetEdge - edge : null;
    const strongGap = isFiniteNumber(edge) && isFiniteNumber(targetStrong) ? targetStrong - edge : null;
    const stretchGap = isFiniteNumber(edge) && isFiniteNumber(targetStretch) ? targetStretch - edge : null;
    const moonshotGap = isFiniteNumber(edge) && isFiniteNumber(targetMoonshot) ? targetMoonshot - edge : null;
    const ciGap = isFiniteNumber(ciLow) ? targetCiLow - ciLow : null;
    const ratioGap = isFiniteNumber(ratio) ? targetRatio - ratio : null;

    const phase11 = edgeResearch?.phase11?.summary || null;
    const phase12 = edgeResearch?.phase12?.summary || null;
    const phase13 = edgeResearch?.phase13?.summary || null;

    return `
      <div class="section">
        <h3>Tiered Goal Runway</h3>
        <div class="scorecard-grid">
          <div class="info-card">
            <p><strong>Gap to Release Floor</strong></p>
            <p class="${gapClass(edgeGap)} mono">${gapText(edgeGap)}</p>
            <p>Current edge: ${formatPct(edge)}</p>
            <p>Floor: ${formatPct(targetEdge)}</p>
          </div>
          <div class="info-card">
            <p><strong>Gap to Strong Tier</strong></p>
            <p class="${gapClass(strongGap)} mono">${gapText(strongGap)}</p>
            <p>Current edge: ${formatPct(edge)}</p>
            <p>Strong: ${formatPct(targetStrong)}</p>
          </div>
          <div class="info-card">
            <p><strong>Gap to Stretch Tier</strong></p>
            <p class="${gapClass(stretchGap)} mono">${gapText(stretchGap)}</p>
            <p>Current edge: ${formatPct(edge)}</p>
            <p>Stretch: ${formatPct(targetStretch)}</p>
          </div>
          <div class="info-card">
            <p><strong>Gap to Moonshot Tier</strong></p>
            <p class="${gapClass(moonshotGap)} mono">${gapText(moonshotGap)}</p>
            <p>Current edge: ${formatPct(edge)}</p>
            <p>Moonshot: ${formatPct(targetMoonshot)}</p>
          </div>
          <div class="info-card">
            <p><strong>Gap to CI-Low > 0</strong></p>
            <p class="${gapClass(ciGap)} mono">${gapText(ciGap)}</p>
            <p>Current CI low: ${formatPct(ciLow)}</p>
            <p>Floor: ${formatPct(targetCiLow)}</p>
          </div>
          <div class="info-card">
            <p><strong>Gap to Positive-Season Ratio Floor</strong></p>
            <p class="${gapClass(ratioGap)} mono">${gapText(ratioGap)}</p>
            <p>Current ratio: ${formatPct(ratio)}</p>
            <p>Floor: ${formatPct(targetRatio)}</p>
          </div>
        </div>
        <div class="info-card mt-md">
          <p><strong>Research Lane Snapshot</strong></p>
          <p>Phase 11 best eligible edge: ${formatPct(phase11?.bestEligibleEdge)} (${phase11?.bestEligibleName || '--'})</p>
          <p>Phase 12 closest-to-goal candidate: ${phase12?.closestGoalName || '--'}</p>
          <p>Phase 12 undeniable candidates: ${phase12?.undeniableCount ?? '--'}</p>
          <p>Phase 13 closest feasible candidate: ${phase13?.closestFeasibleName || '--'}</p>
          <p>Phase 13 prefilter pass count: ${phase13?.positiveRatioPrefilterPassCount ?? '--'}</p>
          <p>Phase 13 undeniable candidates: ${phase13?.undeniableCount ?? '--'}</p>
        </div>
      </div>
    `;
  }

  function renderBenchmarkSection(benchmark) {
    const current = benchmark?.current;
    if (!current) {
      return `
        <div class="section">
          <h3>Proof Scorecard</h3>
          <div class="info-card">
            <p>Benchmark snapshot file not available in this environment.</p>
          </div>
        </div>
      `;
    }

    const previous = benchmark.previous || null;
    const core = current.core || {};
    const checkpoint = current.checkpoint || {};
    const quality = current.quality || {};
    const vegas = current.vegas || {};

    return `
      <div class="section">
        <h3>Proof Scorecard (Current vs Previous)</h3>
        <table class="data-table compact">
          <thead>
            <tr>
              <th>Core Metric</th>
              <th>Current</th>
              <th>Previous</th>
              <th>Delta</th>
            </tr>
          </thead>
          <tbody>
            ${renderMetricRow('Cup Top-1 Accuracy (%)', core.top1_accuracy_pct, previous?.core?.top1_accuracy_pct, false, 1)}
            ${renderMetricRow('Cup Top-5 Accuracy (%)', core.top5_accuracy_pct, previous?.core?.top5_accuracy_pct, false, 1)}
            ${renderMetricRow('Average Winner Rank', core.average_winner_rank, previous?.core?.average_winner_rank, true, 2)}
            ${renderMetricRow('Playoff F1', core.playoff_f1, previous?.core?.playoff_f1, false, 3)}
          </tbody>
        </table>
      </div>

      <div class="section">
        <h3>Checkpoint Playoff Field Accuracy (F1)</h3>
        <table class="data-table compact">
          <thead>
            <tr>
              <th>Checkpoint</th>
              <th>Current</th>
              <th>Previous</th>
              <th>Delta</th>
            </tr>
          </thead>
          <tbody>
            ${renderMetricRow('Games 0 (G0)', checkpoint.g0_playoff_f1, previous?.checkpoint?.g0_playoff_f1, false, 3)}
            ${renderMetricRow('Games 20 (G20)', checkpoint.g20_playoff_f1, previous?.checkpoint?.g20_playoff_f1, false, 3)}
            ${renderMetricRow('Games 40 (G40)', checkpoint.g40_playoff_f1, previous?.checkpoint?.g40_playoff_f1, false, 3)}
            ${renderMetricRow('Games 60 (G60)', checkpoint.g60_playoff_f1, previous?.checkpoint?.g60_playoff_f1, false, 3)}
          </tbody>
        </table>
      </div>

      <div class="section">
        <h3>Probability Quality</h3>
        <table class="data-table compact">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Current</th>
              <th>Previous</th>
              <th>Delta</th>
            </tr>
          </thead>
          <tbody>
            ${renderQualityRow('Brier Playoff', quality.brier_playoff, previous?.quality?.brier_playoff, true)}
            ${renderQualityRow('Brier Cup', quality.brier_cup, previous?.quality?.brier_cup, true)}
            ${renderQualityRow('Log Loss Playoff', quality.log_loss_playoff, previous?.quality?.log_loss_playoff, true)}
            ${renderQualityRow('Calibration Error', quality.calibration_error, previous?.quality?.calibration_error, true)}
          </tbody>
        </table>
        <div class="info-card mt-md">
          <p><strong>Vegas status:</strong> ${vegas.available ? 'Active' : 'Unavailable (historical files missing)'}</p>
          <p>Seasons available: ${(vegas.seasons_available || []).length}</p>
          <p>Seasons missing: ${(vegas.seasons_missing || []).length}</p>
          <p>Cup relative Brier edge: ${formatPct(vegas.cup_relative_brier_edge)}</p>
          <p>Cup goal tier: <span class="${(vegas.cup_target?.goal_met || vegas.cup_target?.release_floor_met) ? 'text-positive' : 'text-negative'}">${renderGoalTierLabel(resolveGoalTier(vegas.cup_target || {}, vegas.cup_relative_brier_edge))}</span></p>
        </div>
      </div>
    `;
  }

  function renderMetricRow(label, current, previous, lowerIsBetter, decimals) {
    const currentDisplay = numberOrDash(current, decimals);
    const previousDisplay = numberOrDash(previous, decimals);
    if (!isFiniteNumber(current) || !isFiniteNumber(previous)) {
      return `
        <tr>
          <td>${label}</td>
          <td class="mono">${currentDisplay}</td>
          <td class="mono">${previousDisplay}</td>
          <td class="mono">--</td>
        </tr>
      `;
    }

    const delta = current - previous;
    const improved = lowerIsBetter ? delta <= 0 : delta >= 0;
    const cls = improved ? 'text-positive' : 'text-negative';
    const deltaText = `${delta >= 0 ? '+' : ''}${delta.toFixed(decimals)}`;

    return `
      <tr>
        <td>${label}</td>
        <td class="mono">${currentDisplay}</td>
        <td class="mono">${previousDisplay}</td>
        <td class="mono ${cls}">${deltaText}</td>
      </tr>
    `;
  }

  function renderQualityRow(label, current, previous, lowerIsBetter) {
    const currentDisplay = numberOrDash(current, 3);
    const previousDisplay = numberOrDash(previous, 3);
    if (!isFiniteNumber(current) || !isFiniteNumber(previous)) {
      return `
        <tr>
          <td>${label}</td>
          <td class="mono">${currentDisplay}</td>
          <td class="mono">${previousDisplay}</td>
          <td class="mono">--</td>
        </tr>
      `;
    }

    const delta = current - previous;
    const improved = lowerIsBetter ? delta <= 0 : delta >= 0;
    const cls = improved ? 'text-positive' : 'text-negative';
    const deltaText = `${delta >= 0 ? '+' : ''}${delta.toFixed(3)}`;

    return `
      <tr>
        <td>${label}</td>
        <td class="mono">${currentDisplay}</td>
        <td class="mono">${previousDisplay}</td>
        <td class="mono ${cls}">${deltaText}</td>
      </tr>
    `;
  }

  function isFiniteNumber(value) {
    return typeof value === 'number' && Number.isFinite(value);
  }

  function numberOrDash(value, decimals) {
    return isFiniteNumber(value) ? value.toFixed(decimals) : '--';
  }

  function formatPct(value) {
    return isFiniteNumber(value) ? `${(value * 100).toFixed(2)}%` : '--';
  }

  function resolveGoalTier(target, edge) {
    if (typeof target.goal_tier === 'string' && target.goal_tier.trim()) {
      return target.goal_tier.trim();
    }

    if (target.moonshot_met === true) return 'moonshot';
    if (target.stretch_met === true) return 'stretch';
    if (target.strong_met === true) return 'strong';
    if (target.release_floor_met === true || target.goal_met === true) return 'release_floor';

    if (!isFiniteNumber(edge)) return 'blocked';
    if (isFiniteNumber(target.relative_brier_improvement_moonshot) && edge >= target.relative_brier_improvement_moonshot) return 'moonshot';
    if (isFiniteNumber(target.relative_brier_improvement_stretch) && edge >= target.relative_brier_improvement_stretch) return 'stretch';
    if (isFiniteNumber(target.relative_brier_improvement_strong) && edge >= target.relative_brier_improvement_strong) return 'strong';
    if (isFiniteNumber(target.relative_brier_improvement_min) && edge >= target.relative_brier_improvement_min) return 'release_floor';
    return 'blocked';
  }

  function renderGoalTierLabel(tier) {
    const value = String(tier || '').toLowerCase();
    if (value === 'moonshot') return 'MOONSHOT';
    if (value === 'stretch') return 'STRETCH';
    if (value === 'strong') return 'STRONG';
    if (value === 'release_floor') return 'RELEASE FLOOR';
    return 'BLOCKED';
  }

  function gapClass(value) {
    if (!isFiniteNumber(value)) return '';
    return value <= 0 ? 'text-positive' : 'text-negative';
  }

  function gapText(value) {
    if (!isFiniteNumber(value)) return '--';
    return `${value <= 0 ? '' : '+'}${(value * 100).toFixed(2)}%`;
  }

  function getAgeDays(value) {
    if (!value) return null;
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return null;
    return (Date.now() - parsed.getTime()) / (1000 * 60 * 60 * 24);
  }

  function formatTimestamp(value) {
    if (!value) return '--';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return String(value);
    return parsed.toLocaleString();
  }

  function renderSeasonTable(seasons) {
    return `
      <table class="data-table compact">
        <thead>
          <tr>
            <th>Season</th>
            <th>Model #1</th>
            <th>Model Top 5</th>
            <th>Actual Winner</th>
            <th>In Top 5?</th>
            <th>Winner Prob</th>
          </tr>
        </thead>
        <tbody>
          ${seasons.map(s => {
            const correct = s.topPickCorrect;
            const inTop5 = s.winnerInTop5;
            return `
              <tr>
                <td class="mono">${s.season - 1}-${String(s.season).slice(2)}</td>
                <td class="team-code ${correct ? 'text-positive' : ''}">${s.modelTopPick}</td>
                <td class="muted">${s.modelTop5.join(', ')}</td>
                <td class="team-code bold">${s.actualWinner}</td>
                <td>${inTop5 ? '<span class="check-mark">Yes</span>' : '<span class="x-mark">No</span>'}</td>
                <td class="mono">${s.modelProbForWinner}%</td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    `;
  }

  return { render };
})();
