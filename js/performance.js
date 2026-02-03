/**
 * Model Performance Tab - Backtest results and validation metrics
 */
const Performance = (() => {
  function render(container, data) {
    const backtest = data.backtest || {};
    const seasons = backtest.seasons || [];
    const summary = backtest.summary || {};

    container.innerHTML = `
      <div class="tab-header">
        <h2>Model Performance</h2>
        <p class="tab-subtitle">Leave-one-season-out backtesting across ${summary.totalSeasons || 0} historical seasons.</p>
      </div>

      ${renderSummaryCards(summary)}

      <div class="section">
        <h3>Season-by-Season Results</h3>
        ${seasons.length > 0 ? renderSeasonTable(seasons) : '<p class="muted">No backtest data available. Run the backtest manually to generate.</p>'}
      </div>

      <div class="section">
        <h3>How to Read This</h3>
        <div class="info-card">
          <p>The model is trained on all seasons <em>except</em> the tested one, then predicts that season blind.</p>
          <p>NHL playoff prediction is inherently hard. A random model picks the Cup winner ~3% of the time (1 in 32).
             Getting the winner in the top 5 at ~33% is well above chance (which would be ~16%).</p>
          <p>The most useful signal is relative rankings, not raw probabilities.</p>
        </div>
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
          <div class="stat-card-value">~3%</div>
          <div class="stat-card-label">Random baseline</div>
        </div>
      </div>
    `;
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
