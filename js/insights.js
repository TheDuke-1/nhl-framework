/**
 * Insights Tab - Auto-generated observations and news feed
 */
const Insights = (() => {
  function render(container, data) {
    const teams = data.teams || [];
    const changes = data.recentChanges || [];
    const observations = generateObservations(teams, data);

    container.innerHTML = `
      <div class="tab-header">
        <h2>Insights</h2>
        <p class="tab-subtitle">Auto-generated observations from the latest model run.</p>
      </div>

      ${changes.length > 0 ? renderChanges(changes) : ''}

      <div class="insights-grid">
        ${observations.map(obs => `
          <div class="insight-card ${obs.type}">
            <div class="insight-type">${obs.label}</div>
            <div class="insight-text">${obs.text}</div>
          </div>
        `).join('')}
      </div>
    `;
  }

  function renderChanges(changes) {
    return `
      <div class="section">
        <h3>Recent Changes</h3>
        <div class="changes-list">
          ${changes.map(c => `
            <div class="change-item change-${c.type}">
              <span class="change-team">${c.team}</span>
              <span class="change-message">${c.message}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  function generateObservations(teams, data) {
    const obs = [];

    // Top Cup favorite
    if (teams.length > 0) {
      const fav = teams[0];
      obs.push({
        type: 'highlight',
        label: 'Cup Favorite',
        text: `${fav.name} lead the field with a ${Utils.pct(fav.cupProbability)} Cup probability ` +
              `and ${fav.compositeStrength.toFixed(1)} composite strength.`
      });
    }

    // Biggest underdog in playoffs
    const playoffTeams = teams.filter(t => t.playoffProbability >= 50);
    const underdogInPlayoffs = playoffTeams
      .filter(t => t.tier === 'Bubble' || t.tier === 'Longshot')
      .sort((a, b) => b.cupProbability - a.cupProbability)[0];
    if (underdogInPlayoffs) {
      obs.push({
        type: 'upset',
        label: 'Dark Horse',
        text: `${underdogInPlayoffs.name} are a ${underdogInPlayoffs.tier.toLowerCase()} team ` +
              `that could make noise: ${Utils.pct(underdogInPlayoffs.cupProbability)} Cup odds despite ` +
              `${Utils.pct(underdogInPlayoffs.playoffProbability)} playoff probability.`
      });
    }

    // Most injured team in playoff contention
    const injuredContender = teams
      .filter(t => t.playoffProbability >= 50 && t.totalWarLost > 0)
      .sort((a, b) => b.totalWarLost - a.totalWarLost)[0];
    if (injuredContender && injuredContender.totalWarLost > 3) {
      obs.push({
        type: 'injury',
        label: 'Injury Impact',
        text: `${injuredContender.name} are the most banged-up contender with ` +
              `~${injuredContender.totalWarLost.toFixed(1)} WAR lost to injuries ` +
              `(${(injuredContender.injuries || []).length} players out).`
      });
    }

    // Conference balance
    const eastElite = teams.filter(t => t.conference === 'East' && t.tier === 'Elite').length;
    const westElite = teams.filter(t => t.conference === 'West' && t.tier === 'Elite').length;
    if (Math.abs(eastElite - westElite) >= 2) {
      const stronger = eastElite > westElite ? 'East' : 'West';
      obs.push({
        type: 'analysis',
        label: 'Conference Gap',
        text: `The ${stronger}ern Conference has ${Math.max(eastElite, westElite)} Elite teams vs ` +
              `${Math.min(eastElite, westElite)} in the ${stronger === 'East' ? 'West' : 'East'}.`
      });
    }

    // Tier distribution
    const tiers = {};
    teams.forEach(t => { tiers[t.tier] = (tiers[t.tier] || 0) + 1; });
    obs.push({
      type: 'analysis',
      label: 'Tier Distribution',
      text: `Elite: ${tiers.Elite || 0} | Contender: ${tiers.Contender || 0} | ` +
            `Bubble: ${tiers.Bubble || 0} | Longshot: ${tiers.Longshot || 0}`
    });

    // Biggest gap between adjacent teams
    if (teams.length >= 2) {
      let maxGap = 0, gapIdx = 0;
      for (let i = 0; i < teams.length - 1; i++) {
        const gap = teams[i].cupProbability - teams[i + 1].cupProbability;
        if (gap > maxGap) { maxGap = gap; gapIdx = i; }
      }
      if (maxGap > 2) {
        obs.push({
          type: 'analysis',
          label: 'Separation',
          text: `Biggest gap: ${Utils.pct(maxGap)} between ` +
                `#${gapIdx + 1} ${teams[gapIdx].code} and #${gapIdx + 2} ${teams[gapIdx + 1].code}.`
        });
      }
    }

    // Feature weights insight
    const weights = data.featureWeights || [];
    if (weights.length >= 2) {
      obs.push({
        type: 'model',
        label: 'Key Drivers',
        text: `The model's top factors: ${weights[0].name} (${weights[0].weight.toFixed(1)}%) ` +
              `and ${weights[1].name} (${weights[1].weight.toFixed(1)}%).`
      });
    }

    return obs;
  }

  return { render };
})();
