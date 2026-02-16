/**
 * Mission Control tab - executive launch surface for trust and goal status.
 */
const MissionControl = (() => {
  function render(container, data) {
    const benchmark = data.benchmark?.current || {};
    const vegas = benchmark.vegas || {};
    const core = benchmark.core || {};
    const quality = benchmark.quality || {};
    const releaseCycleBundle = data.releaseCycle || {};
    const releaseCycleStrict = releaseCycleBundle.strict || releaseCycleBundle || {};
    const releaseCycleAdvisory = releaseCycleBundle.advisory || {};
    const dashboardGrade = data.dashboardGrade?.dashboard || {};

    const releaseStatusStrict = String(
      data.meta?.releaseStatusStrict
      || releaseCycleBundle.shipGateStatus
      || releaseCycleStrict.status
      || 'UNKNOWN'
    ).toUpperCase();
    const releaseStatusAdvisory = String(
      data.meta?.releaseStatusAdvisory
      || releaseCycleBundle.localAdvisoryStatus
      || releaseCycleAdvisory.status
      || 'UNKNOWN'
    ).toUpperCase();

    const target = vegas.cup_target || {};
    const edge = vegas.cup_relative_brier_edge;
    const releaseFloorMet = target.release_floor_met === true || target.goal_met === true;
    const strongMet = target.strong_met === true;
    const stretchMet = target.stretch_met === true;
    const moonshotMet = target.moonshot_met === true;
    const goalTier = resolveGoalTier(target, edge);
    const goalTierLabel = renderGoalTierLabel(goalTier);
    const releaseReady = releaseStatusStrict === 'PASS' && releaseFloorMet;
    const modelQualityStatus = classifyModelQuality(core, quality);
    const targetMin = target.relative_brier_improvement_min;
    const targetStrong = target.relative_brier_improvement_strong;
    const targetStretch = target.relative_brier_improvement_stretch;
    const targetMoonshot = target.relative_brier_improvement_moonshot;
    const gap = isFiniteNumber(edge) && isFiniteNumber(targetMin) ? (targetMin - edge) : null;
    const strongGap = isFiniteNumber(edge) && isFiniteNumber(targetStrong) ? (targetStrong - edge) : null;
    const runwayGap = isFiniteNumber(strongGap) ? strongGap : gap;

    const releaseCommands = Array.isArray(releaseCycleStrict.commands) ? releaseCycleStrict.commands : [];
    const releaseBlockingReasons = Array.isArray(releaseCycleStrict.blockingReasons) ? releaseCycleStrict.blockingReasons : [];
    const advisoryWarnings = Array.isArray(releaseCycleAdvisory?.advisories?.dataWarnings)
      ? releaseCycleAdvisory.advisories.dataWarnings
      : [];
    const blockers = releaseCommands.filter((row) => Number(row.returncode) !== 0);

    const blockerReasons = buildBlockerReasons({
      blockers,
      releaseBlockingReasons,
      edge,
      targetMin,
      releaseFloorMet,
      releaseStatusStrict,
      capReasons: dashboardGrade.detail?.cap_reasons || [],
      advisoryWarnings,
    });

    const freshnessRows = buildFreshnessRows(data.meta || {});
    const nextActions = buildNextActions({
      releaseStatusStrict,
      releaseStatusAdvisory,
      releaseReady,
      releaseFloorMet,
      strongMet,
      edge,
      targetMin,
      targetStrong,
      blockers,
      freshnessRows,
      advisoryPolicy: releaseCycleAdvisory.dataValidationPolicy || {},
      advisoryWarnings,
    });

    const releaseTrace = releaseCommands.slice(-6).reverse();
    const sourceTrustLabel = blockers.length === 0 && freshnessRows.every((r) => r.state !== 'stale')
      ? 'Trust: Healthy'
      : 'Trust: Watch';

    container.innerHTML = `
      <section class="mission-hero ${releaseStatusStrict === 'PASS' ? 'mission-pass' : 'mission-fail'}">
        <div class="mission-kicker">Executive Flight Deck</div>
        <h2>Mission Control</h2>
        <p>Single decision surface for release truth, Cup-edge objective, operational readiness, and current risk narrative.</p>
        <div class="mission-badges">
          <span class="mission-badge ${modelQualityStatus === 'PASS' ? 'badge-pass' : 'badge-fail'}">Model Quality: ${modelQualityStatus}</span>
          <span class="mission-badge ${releaseReady ? 'badge-pass' : 'badge-fail'}">Release Ready (Strict): ${releaseReady ? 'YES' : 'NO'}</span>
          <span class="mission-badge ${releaseStatusStrict === 'PASS' ? 'badge-pass' : 'badge-fail'}">Release Cycle (Strict): ${releaseStatusStrict}</span>
          <span class="mission-badge ${releaseStatusAdvisory === 'PASS' ? 'badge-pass' : 'badge-fail'}">Local Advisory Status: ${releaseStatusAdvisory}</span>
          <span class="mission-badge ${releaseFloorMet ? 'badge-pass' : 'badge-fail'}">Cup Release Floor: ${releaseFloorMet ? 'PASS' : 'FAIL'}</span>
          <span class="mission-badge ${(strongMet || stretchMet || moonshotMet) ? 'badge-pass' : 'badge-fail'}">Goal Tier: ${goalTierLabel}</span>
          <span class="mission-badge">${sourceTrustLabel}</span>
          <span class="mission-badge">${formatSeasonCount(vegas.cup_total_seasons)} seasons compared</span>
        </div>
      </section>

      <section class="mission-grid">
        <article class="mission-card">
          <h3>Cup Edge vs Vegas</h3>
          <p class="mission-value ${releaseFloorMet ? 'text-positive' : 'text-negative'}">${formatPct(edge)}</p>
          <p class="mission-meta">Tier: <strong>${goalTierLabel}</strong></p>
          <p class="mission-meta">Release floor: ${formatPct(targetMin)}${isFiniteNumber(gap) ? ` | Gap: ${formatPct(gap)}` : ''}</p>
          <p class="mission-meta">Strong/Stretch/Moonshot: ${formatPct(targetStrong)} / ${formatPct(targetStretch)} / ${formatPct(targetMoonshot)}</p>
          <p class="mission-meta">CI: [${formatPct(vegas.cup_relative_brier_edge_ci_low)}, ${formatPct(vegas.cup_relative_brier_edge_ci_high)}]</p>
        </article>

        <article class="mission-card">
          <h3>Tier Progress Runway</h3>
          <p class="mission-value ${isFiniteNumber(runwayGap) && runwayGap <= 0 ? 'text-positive' : 'text-negative'}">${isFiniteNumber(runwayGap) ? formatPct(runwayGap) : '--'}</p>
          <p class="mission-meta">
            ${isFiniteNumber(targetStrong)
              ? `Gap to strong tier (${formatPct(targetStrong)}).`
              : `Gap to release floor (${formatPct(targetMin)}).`}
          </p>
          <p class="mission-meta">Strong/Stretch/Moonshot pass: <strong>${strongMet ? 'YES' : 'NO'} / ${stretchMet ? 'YES' : 'NO'} / ${moonshotMet ? 'YES' : 'NO'}</strong></p>
          <p class="mission-meta">Positive seasons: <strong>${vegas.cup_positive_seasons ?? '--'}/${vegas.cup_total_seasons ?? '--'}</strong> (${formatPct(vegas.cup_positive_season_ratio)})</p>
        </article>

        <article class="mission-card">
          <h3>Core Reliability</h3>
          <p class="mission-meta">Top-1: <strong>${numberOrDash(core.top1_accuracy_pct, 1)}%</strong></p>
          <p class="mission-meta">Top-5: <strong>${numberOrDash(core.top5_accuracy_pct, 1)}%</strong></p>
          <p class="mission-meta">Playoff F1: <strong>${numberOrDash(core.playoff_f1, 3)}</strong></p>
          <p class="mission-meta">Winner Rank: <strong>${numberOrDash(core.average_winner_rank, 2)}</strong></p>
        </article>

        <article class="mission-card">
          <h3>Market Sustainability</h3>
          <p class="mission-meta">Positive seasons: <strong>${vegas.cup_positive_seasons ?? '--'}/${vegas.cup_total_seasons ?? '--'}</strong></p>
          <p class="mission-meta">Positive ratio: <strong>${formatPct(vegas.cup_positive_season_ratio)}</strong></p>
          <p class="mission-meta">Vegas coverage: <strong>${vegas.available ? 'active' : 'missing'}</strong></p>
          <p class="mission-meta">Playoff Brier delta: <strong>${signed(benchmark.vegas?.model_minus_vegas_brier_playoff, 3)}</strong></p>
          <p class="mission-meta">Dashboard grade: <strong>${dashboardGrade.grade || '--'} (${dashboardGrade.numeric ?? '--'})</strong></p>
        </article>
      </section>

      <section class="mission-deck">
        <article class="mission-panel">
          <h3>Data Trust Panel</h3>
          <div class="mission-trust-list">
            ${freshnessRows.map((row) => `
              <div class="mission-trust-row">
                <span class="mission-trust-label">${escapeHtml(row.label)}</span>
                <span class="mission-trust-age ${row.state === 'fresh' ? 'text-positive' : row.state === 'stale' ? 'text-negative' : ''}">
                  ${escapeHtml(row.display)}
                </span>
              </div>
            `).join('')}
          </div>
        </article>

        <article class="mission-panel">
          <h3>Release Decision Trace (Strict)</h3>
          <div class="mission-trace-list">
            ${releaseTrace.length > 0 ? releaseTrace.map((row) => `
              <div class="mission-trace-row">
                <span class="mission-trace-status ${Number(row.returncode) === 0 ? 'trace-pass' : 'trace-fail'}">
                  ${Number(row.returncode) === 0 ? 'PASS' : 'FAIL'}
                </span>
                <code>${escapeHtml(commandLabel(row.cmd || 'unknown'))}</code>
              </div>
            `).join('') : '<p class="mission-meta">No strict release trace available.</p>'}
          </div>
          <p class="mission-meta">Strict blocking checks: <strong>${blockers.length}</strong></p>
        </article>

        <article class="mission-panel">
          <h3>Why Blocked Right Now</h3>
          <div class="mission-trust-list">
            ${blockerReasons.length ? blockerReasons.map((row) => `
              <div class="mission-trust-row">
                <span class="mission-trust-label">${escapeHtml(row.label)}</span>
                <span class="mission-trust-age ${row.state === 'fail' ? 'text-negative' : row.state === 'pass' ? 'text-positive' : ''}">${escapeHtml(row.detail)}</span>
              </div>
            `).join('') : '<p class="mission-meta text-positive">No active blockers detected.</p>'}
          </div>
        </article>
      </section>

      <section class="section">
        <h3>Immediate Actions</h3>
        <div class="mission-trust-list">
          ${nextActions.length ? nextActions.map((row) => `
            <div class="mission-trust-row">
              <span class="mission-trust-label">${escapeHtml(row.owner)} · ${escapeHtml(row.priority)}</span>
              <span class="mission-trust-age">${escapeHtml(row.action)}</span>
            </div>
          `).join('') : '<p class="mission-meta text-positive">No immediate actions required.</p>'}
        </div>
      </section>

      <section class="section">
        <h3>Execution Waves</h3>
        <div class="info-card mission-actions">
          <p><strong>Wave 1:</strong> move from release-floor pass to strong tier while preserving non-regression and positive-season ratio floor.</p>
          <p><strong>Wave 2:</strong> enforce strict freshness, strict release contract, and no silent pipeline failures.</p>
          <p><strong>Wave 3:</strong> maintain premium trust UX with explicit release trace and source SLA visibility.</p>
          <p><strong>Wave 4:</strong> productize prevention patterns into reusable skills for future projects.</p>
        </div>
      </section>
    `;
  }

  function commandLabel(cmd) {
    const text = String(cmd || '').trim();
    if (!text) return 'unknown';
    const pieces = text.split(/\s+/);
    return pieces.length > 6 ? `${pieces.slice(0, 6).join(' ')} ...` : text;
  }

  function classifyModelQuality(core, quality) {
    const top1 = Number(core.top1_accuracy_pct || 0);
    const top5 = Number(core.top5_accuracy_pct || 0);
    const f1 = Number(core.playoff_f1 || 0);
    const rank = Number(core.average_winner_rank || 999);
    const brierCup = Number(quality.brier_cup || 1);
    const ece = Number(quality.calibration_error || 1);
    const passesCore = top1 >= 12 && top5 >= 45 && f1 >= 0.9 && rank <= 8;
    const passesQuality = brierCup <= 0.06 && ece <= 0.20;
    return passesCore && passesQuality ? 'PASS' : 'WATCH';
  }

  function buildBlockerReasons({ blockers, releaseBlockingReasons, edge, targetMin, releaseFloorMet, releaseStatusStrict, capReasons, advisoryWarnings }) {
    const reasons = [];

    if (releaseStatusStrict !== 'PASS') {
      reasons.push({ label: 'Release cycle (strict)', detail: `Status is ${releaseStatusStrict}`, state: 'fail' });
    }

    if (!releaseFloorMet && isFiniteNumber(edge) && isFiniteNumber(targetMin)) {
      reasons.push({
        label: 'Cup-vs-Vegas release floor',
        detail: `Edge shortfall ${formatPct(targetMin - edge)} (current ${formatPct(edge)} vs floor ${formatPct(targetMin)})`,
        state: 'fail',
      });
    }

    const commandReasons = blockers.slice(0, 3).map((row) => {
      const structured = releaseBlockingReasons.find((item) => String(item.cmd || '').trim() === String(row.cmd || '').trim());
      const text = `${row.stdout || ''}\n${row.stderr || ''}`;
      const failLine = text.split('\n').find((line) => line.trim().startsWith('FAIL:'));
      const detail = structured?.reason || (failLine ? failLine.replace(/^FAIL:\s*/, '') : 'Command failed without explicit FAIL line');
      return {
        label: commandLabel(row.cmd || 'unknown'),
        detail,
        state: 'fail',
      };
    });
    reasons.push(...commandReasons);

    if (Array.isArray(capReasons) && capReasons.length > 0) {
      reasons.push({
        label: 'Dashboard grade cap',
        detail: capReasons.join(', '),
        state: 'fail',
      });
    }

    if (Array.isArray(advisoryWarnings) && advisoryWarnings.length > 0) {
      advisoryWarnings.slice(0, 2).forEach((warning) => {
        reasons.push({
          label: 'Advisory freshness',
          detail: String(warning).replace(/^⚠️\s*/, '').trim(),
          state: 'warn',
        });
      });
    }

    return reasons;
  }

  function buildNextActions({
    releaseStatusStrict,
    releaseStatusAdvisory,
    releaseReady,
    releaseFloorMet,
    strongMet,
    edge,
    targetMin,
    targetStrong,
    blockers,
    freshnessRows,
    advisoryPolicy,
    advisoryWarnings,
  }) {
    const actions = [];
    const staleSources = freshnessRows.filter((row) => row.state === 'stale');
    const allowWarnings = advisoryPolicy?.allowWarnings === true;

    if (releaseStatusStrict !== 'PASS') {
      actions.push({
        owner: 'Release Sheriff',
        priority: 'P0',
        action: 'Run `python3 scripts/run_phase7_release_cycle.py --mode strict` and clear strict blockers before promotion.',
      });
    }

    if (releaseStatusAdvisory !== 'PASS') {
      actions.push({
        owner: 'Release Sheriff',
        priority: 'P1',
        action: 'Run `python3 scripts/run_phase7_release_cycle.py --mode advisory` to refresh local advisory telemetry.',
      });
    }

    if (!releaseFloorMet && isFiniteNumber(edge) && isFiniteNumber(targetMin)) {
      actions.push({
        owner: 'Model Lead',
        priority: 'P0',
        action: `Close release-floor gap (${formatPct(targetMin - edge)}) with non-regression constrained tuning.`,
      });
    }

    if (releaseFloorMet && !strongMet && isFiniteNumber(edge) && isFiniteNumber(targetStrong)) {
      actions.push({
        owner: 'Model Lead',
        priority: 'P1',
        action: `Strong-tier still pending: close ${formatPct(targetStrong - edge)} to reach ${formatPct(targetStrong)}.`,
      });
    }

    if (staleSources.length) {
      actions.push({
        owner: 'Data Ops',
        priority: releaseStatusStrict === 'PASS' ? 'P1' : 'P0',
        action: `Refresh stale sources (${staleSources.map((s) => s.label).join(', ')}) and re-run strict validation.`,
      });
    }

    if (allowWarnings && Array.isArray(advisoryWarnings) && advisoryWarnings.length > 0) {
      actions.push({
        owner: 'Release Sheriff',
        priority: 'P1',
        action: 'Advisory mode is non-blocking; do not treat advisory PASS as ship-gate proof.',
      });
    }

    if (releaseReady && blockers.length === 0) {
      actions.push({
        owner: 'Program Lead',
        priority: 'P2',
        action: 'Ship-gate truth is healthy. Proceed with dashboard polish and probability-quality uplift lane.',
      });
    }

    return actions.slice(0, 5);
  }

  function buildFreshnessRows(meta) {
    const sources = meta.sourceFreshness || meta.freshness || {};
    const generated = meta.generated || meta.lastUpdate || null;
    return [
      freshnessEntry('NHL API', sources.nhl || sources.nhl_standings || generated, 24),
      freshnessEntry('MoneyPuck', sources.moneypuck || sources.moneypuck_stats || generated, 24),
      freshnessEntry('Natural Stat Trick', sources.nst || sources.nst_stats || generated, 24),
      freshnessEntry('Model Output', generated, 36),
    ];
  }

  function freshnessEntry(label, raw, freshnessSlaHours) {
    const date = parseDate(raw);
    if (!date) {
      return { label, state: 'unknown', display: '--' };
    }
    const ageHours = (Date.now() - date.getTime()) / (1000 * 60 * 60);
    const state = ageHours <= freshnessSlaHours ? 'fresh' : 'stale';
    return {
      label,
      state,
      display: `${Math.floor(ageHours)}h old`,
    };
  }

  function parseDate(raw) {
    if (!raw) return null;
    const date = new Date(raw);
    if (Number.isNaN(date.getTime())) return null;
    return date;
  }

  function isFiniteNumber(value) {
    return typeof value === 'number' && Number.isFinite(value);
  }

  function formatPct(value) {
    if (!isFiniteNumber(value)) return '--';
    return `${(value * 100).toFixed(1)}%`;
  }

  function numberOrDash(value, decimals = 2) {
    if (!isFiniteNumber(value)) return '--';
    return value.toFixed(decimals);
  }

  function signed(value, decimals = 3) {
    if (!isFiniteNumber(value)) return '--';
    const num = value.toFixed(decimals);
    return value >= 0 ? `+${num}` : num;
  }

  function formatSeasonCount(value) {
    if (!isFiniteNumber(value)) return '--';
    return `${value}`;
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

  function escapeHtml(input) {
    return String(input)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  return { render };
})();
