/**
 * Bitcoin Quant Intelligence Deck
 * Advanced, math-centered dashboard with rich 2D/3D visual analytics.
 */

const state = {
    paperTrading: [],
    scores: null,
    portfolio: null,
    metrics: null,
    processedData: null,
    derived: null,
};

const charts = {
    price: null,
    performance: null,
    scoreHistory: null,
    portfolio: null,
};

const REFRESH_INTERVAL = 90000;
let refreshTimer = null;

const chartTheme = {
    grid: 'rgba(126, 149, 184, 0.18)',
    ticks: '#9ab2d4',
    title: '#b7c7de',
    tooltipBg: 'rgba(6, 11, 22, 0.94)',
    tooltipText: '#f4f8ff',
    tooltipTitle: '#3ad8ff',
    tooltipBorder: '#39567a',
    mono: 'IBM Plex Mono',
};

function numberOr(value, fallback = 0) {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
}

function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    }).format(numberOr(value));
}

function formatPercent(value, decimals = 2) {
    const n = numberOr(value);
    const sign = n >= 0 ? '+' : '';
    return `${sign}${n.toFixed(decimals)}%`;
}

function formatSigned(value, decimals = 3) {
    const n = numberOr(value);
    const sign = n >= 0 ? '+' : '';
    return `${sign}${n.toFixed(decimals)}`;
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = value;
}

function lastValid(values) {
    for (let i = values.length - 1; i >= 0; i -= 1) {
        if (Number.isFinite(values[i])) return values[i];
    }
    return 0;
}

function paintDirectionalValue(element, value) {
    if (!element) return;
    element.classList.remove('value-positive', 'value-negative', 'value-neutral');
    const n = numberOr(value);
    if (n > 0) {
        element.classList.add('value-positive');
    } else if (n < 0) {
        element.classList.add('value-negative');
    } else {
        element.classList.add('value-neutral');
    }
}

async function fetchData(endpoint) {
    try {
        const response = await fetch(`/api/${endpoint}`);
        const payload = await response.json();
        if (!payload.success) {
            throw new Error(payload.error || `Failed endpoint: ${endpoint}`);
        }
        return payload.data;
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        return null;
    }
}

function normalizePaperTrading(rows) {
    if (!Array.isArray(rows)) return [];
    return rows
        .map((row) => ({
            date: row.date,
            equity: numberOr(row.equity),
            roi: numberOr(row.roi),
            alpha: numberOr(row.alpha),
            cash: numberOr(row.cash),
            btc_value: numberOr(row.btc_value),
            btc_amount: numberOr(row.btc_amount),
            debt: numberOr(row.debt),
            btc_price: numberOr(row.btc_price),
            lt_score: numberOr(row.lt_score),
            mt_score: numberOr(row.mt_score),
        }))
        .filter((row) => row.date)
        .sort((a, b) => new Date(a.date) - new Date(b.date));
}

function rollingMean(values, windowSize) {
    const out = new Array(values.length).fill(null);
    for (let i = 0; i < values.length; i += 1) {
        if (i + 1 < windowSize) continue;
        const window = values.slice(i + 1 - windowSize, i + 1).filter(Number.isFinite);
        if (window.length < windowSize) continue;
        const sum = window.reduce((acc, v) => acc + v, 0);
        out[i] = sum / windowSize;
    }
    return out;
}

function rollingStd(values, windowSize) {
    const out = new Array(values.length).fill(null);
    const means = rollingMean(values, windowSize);
    for (let i = 0; i < values.length; i += 1) {
        if (!Number.isFinite(means[i])) continue;
        const window = values.slice(i + 1 - windowSize, i + 1).filter(Number.isFinite);
        if (window.length < windowSize) continue;
        const variance = window.reduce((acc, v) => acc + (v - means[i]) ** 2, 0) / windowSize;
        out[i] = Math.sqrt(Math.max(variance, 0));
    }
    return out;
}

function computeDrawdown(equitySeries) {
    const out = [];
    let runningPeak = numberOr(equitySeries[0], 1);
    for (let i = 0; i < equitySeries.length; i += 1) {
        const equity = Math.max(numberOr(equitySeries[i], 0), 1e-9);
        runningPeak = Math.max(runningPeak, equity);
        out.push(((equity / runningPeak) - 1) * 100);
    }
    return out;
}

function buildDerivedSeries(rows) {
    const equity = rows.map((row) => row.equity);
    const prices = rows.map((row) => row.btc_price);
    const lt = rows.map((row) => row.lt_score);
    const mt = rows.map((row) => row.mt_score);

    const dailyReturns = [0];
    for (let i = 1; i < equity.length; i += 1) {
        const prev = Math.max(numberOr(equity[i - 1], 0), 1e-9);
        dailyReturns.push((equity[i] / prev) - 1);
    }

    const strategyCum = [];
    const firstEquity = Math.max(numberOr(equity[0], 0), 1e-9);
    for (let i = 0; i < equity.length; i += 1) {
        strategyCum.push(((equity[i] / firstEquity) - 1) * 100);
    }

    const bnhCum = [];
    const firstPrice = Math.max(numberOr(prices[0], 0), 1e-9);
    for (let i = 0; i < prices.length; i += 1) {
        bnhCum.push(((prices[i] / firstPrice) - 1) * 100);
    }

    const drawdown = computeDrawdown(equity);
    const vol30 = rollingStd(dailyReturns, 30).map((v) => (Number.isFinite(v) ? v * Math.sqrt(365) * 100 : null));

    const retMean30 = rollingMean(dailyReturns, 30);
    const retStd30 = rollingStd(dailyReturns, 30);
    const sharpe30 = retMean30.map((mean, i) => {
        const std = retStd30[i];
        if (!Number.isFinite(mean) || !Number.isFinite(std) || std <= 1e-12) return null;
        return (mean / std) * Math.sqrt(365);
    });

    const forward7 = new Array(rows.length).fill(null);
    for (let i = 0; i < rows.length - 7; i += 1) {
        if (prices[i] > 0) {
            forward7[i] = ((prices[i + 7] / prices[i]) - 1) * 100;
        }
    }

    const spread = lt.map((v, i) => v - mt[i]);
    const positiveDays = dailyReturns.slice(1).filter((r) => r > 0).length;
    const hitRate = dailyReturns.length > 1 ? (positiveDays / (dailyReturns.length - 1)) * 100 : 0;

    return {
        dates: rows.map((row) => row.date),
        equity,
        prices,
        lt,
        mt,
        spread,
        strategyCum,
        bnhCum,
        dailyReturns,
        drawdown,
        vol30,
        sharpe30,
        forward7,
        hitRate,
    };
}

function solveLinearSystem(matrix, vector) {
    const n = matrix.length;
    const aug = matrix.map((row, i) => [...row, vector[i]]);

    for (let col = 0; col < n; col += 1) {
        let pivot = col;
        for (let row = col + 1; row < n; row += 1) {
            if (Math.abs(aug[row][col]) > Math.abs(aug[pivot][col])) {
                pivot = row;
            }
        }

        if (Math.abs(aug[pivot][col]) < 1e-12) return null;
        if (pivot !== col) {
            const temp = aug[col];
            aug[col] = aug[pivot];
            aug[pivot] = temp;
        }

        const divisor = aug[col][col];
        for (let j = col; j <= n; j += 1) {
            aug[col][j] /= divisor;
        }

        for (let row = 0; row < n; row += 1) {
            if (row === col) continue;
            const factor = aug[row][col];
            for (let j = col; j <= n; j += 1) {
                aug[row][j] -= factor * aug[col][j];
            }
        }
    }

    return aug.map((row) => row[n]);
}

function computeModelCoefficients(rows, derived) {
    const samples = [];
    for (let i = 0; i < rows.length; i += 1) {
        const vol = derived.vol30[i];
        const fwd = derived.forward7[i];
        if (!Number.isFinite(vol) || !Number.isFinite(fwd)) continue;
        samples.push({
            x1: numberOr(rows[i].lt_score) / 100,
            x2: numberOr(rows[i].mt_score) / 100,
            x3: vol / 100,
            y: fwd,
        });
    }

    if (samples.length < 35) {
        return { beta: [0, 0, 0, 0], r2: 0 };
    }

    const m = 4;
    const xtx = Array.from({ length: m }, () => Array(m).fill(0));
    const xty = Array(m).fill(0);

    samples.forEach((sample) => {
        const x = [1, sample.x1, sample.x2, sample.x3];
        for (let i = 0; i < m; i += 1) {
            xty[i] += x[i] * sample.y;
            for (let j = 0; j < m; j += 1) {
                xtx[i][j] += x[i] * x[j];
            }
        }
    });

    const beta = solveLinearSystem(xtx, xty);
    if (!beta) {
        return { beta: [0, 0, 0, 0], r2: 0 };
    }

    const yMean = samples.reduce((acc, s) => acc + s.y, 0) / samples.length;
    let ssRes = 0;
    let ssTot = 0;

    samples.forEach((sample) => {
        const yHat = beta[0] + beta[1] * sample.x1 + beta[2] * sample.x2 + beta[3] * sample.x3;
        ssRes += (sample.y - yHat) ** 2;
        ssTot += (sample.y - yMean) ** 2;
    });

    const r2 = ssTot > 1e-12 ? 1 - (ssRes / ssTot) : 0;
    return { beta, r2: Math.max(Math.min(r2, 1), -1) };
}

function destroyVisuals() {
    Object.keys(charts).forEach((key) => {
        if (charts[key] && typeof charts[key].destroy === 'function') {
            charts[key].destroy();
        }
        charts[key] = null;
    });

    if (window.Plotly) {
        ['signal-surface-3d', 'regime-trajectory-3d'].forEach((id) => {
            const el = document.getElementById(id);
            if (el && el.data) {
                window.Plotly.purge(el);
            }
        });
    }
}

function updateHeader() {
    const rows = state.paperTrading;
    if (!rows.length) return;

    const latest = rows[rows.length - 1];
    const strategyReturn = numberOr(state.metrics?.strategy_return, lastValid(state.derived.strategyCum));
    const alpha = numberOr(state.metrics?.alpha, strategyReturn - numberOr(state.metrics?.bnh_return));

    setText('header-price', formatCurrency(latest.btc_price));
    setText('header-equity', formatCurrency(numberOr(state.portfolio?.equity, latest.equity)));
    setText('header-roi', formatPercent(strategyReturn));
    setText('header-alpha', formatPercent(alpha));

    const roiEl = document.getElementById('header-roi');
    const alphaEl = document.getElementById('header-alpha');
    paintDirectionalValue(roiEl, strategyReturn);
    paintDirectionalValue(alphaEl, alpha);

    const syncTime = new Date();
    const syncLabel = `${syncTime.toLocaleDateString()} ${syncTime.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
    })}`;
    setText('status-last-sync', `sync ${syncLabel}`);
}

function updateMetrics() {
    if (!state.derived) return;

    const strategyReturn = numberOr(state.metrics?.strategy_return, lastValid(state.derived.strategyCum));
    const bnhReturn = numberOr(state.metrics?.bnh_return, lastValid(state.derived.bnhCum));
    const alpha = numberOr(state.metrics?.alpha, strategyReturn - bnhReturn);
    const maxDrawdown = numberOr(state.metrics?.max_drawdown, Math.min(...state.derived.drawdown));
    const sharpe = numberOr(state.metrics?.sharpe_ratio, lastValid(state.derived.sharpe30));
    const rollingVol = lastValid(state.derived.vol30);
    const hitRate = numberOr(state.derived.hitRate);

    setText('metric-return', formatPercent(strategyReturn));
    setText('metric-return-sub', `vs B&H: ${formatPercent(bnhReturn)} | spread: ${formatPercent(strategyReturn - bnhReturn)}`);
    setText('metric-alpha', formatPercent(alpha));
    setText('metric-dd', formatPercent(maxDrawdown));
    setText('metric-sharpe', sharpe.toFixed(2));
    setText('metric-vol', formatPercent(rollingVol));
    setText('metric-hitrate', formatPercent(hitRate));

    const alphaBadge = document.getElementById('metric-alpha-badge');
    if (alphaBadge) {
        if (alpha > 0.5) {
            alphaBadge.textContent = 'dominant alpha regime';
            alphaBadge.className = 'metric-sub value-positive';
        } else if (alpha < -0.5) {
            alphaBadge.textContent = 'benchmark pressure';
            alphaBadge.className = 'metric-sub value-negative';
        } else {
            alphaBadge.textContent = 'neutral alpha zone';
            alphaBadge.className = 'metric-sub value-neutral';
        }
    }

    paintDirectionalValue(document.getElementById('metric-return'), strategyReturn);
    paintDirectionalValue(document.getElementById('metric-alpha'), alpha);
    paintDirectionalValue(document.getElementById('metric-sharpe'), sharpe);
    paintDirectionalValue(document.getElementById('metric-vol'), -rollingVol);
    paintDirectionalValue(document.getElementById('metric-hitrate'), hitRate - 50);

    const phase = state.processedData?.market_cycle_phase || 'n/a';
    setText('metric-regime', phase);
    const regimeEl = document.getElementById('metric-regime');
    if (regimeEl) {
        if (/bull|rally|accumulation/i.test(phase)) {
            regimeEl.className = 'metric-value value-positive';
        } else if (/bear|distribution|risk-off/i.test(phase)) {
            regimeEl.className = 'metric-value value-negative';
        } else {
            regimeEl.className = 'metric-value value-neutral';
        }
    }
}

function updateScores() {
    const lastRow = state.paperTrading[state.paperTrading.length - 1] || null;
    const ltScore = numberOr(state.scores?.Long_Term_Score, numberOr(lastRow?.lt_score, 0));
    const mtScore = numberOr(state.scores?.Medium_Term_Score, numberOr(lastRow?.mt_score, 0));

    const updateScoreVisual = (score, displayId, barId) => {
        const display = document.getElementById(displayId);
        const bar = document.getElementById(barId);
        if (!display || !bar) return;

        const normalized = Math.max(0, Math.min(100, ((score + 100) / 200) * 100));
        display.textContent = score.toFixed(2);
        paintDirectionalValue(display, score);
        bar.style.width = `${normalized}%`;
        bar.style.backgroundImage = 'linear-gradient(90deg, #ff5f71 0%, #ffb347 50%, #7dff89 100%)';

        if (normalized > 0) {
            bar.style.backgroundSize = `${(100 / normalized) * 100}% 100%`;
        } else {
            bar.style.backgroundSize = '100% 100%';
        }
    };

    updateScoreVisual(ltScore, 'score-lt-display', 'score-lt-bar');
    updateScoreVisual(mtScore, 'score-mt-display', 'score-mt-bar');

    setText('control-lt', ltScore.toFixed(1));
    setText('control-mt', mtScore.toFixed(1));
    setText('control-vol', formatPercent(lastValid(state.derived.vol30), 1));
    setText('control-sharpe30', lastValid(state.derived.sharpe30).toFixed(2));
}

function updateModelCard() {
    const model = computeModelCoefficients(state.paperTrading, state.derived);

    setText('model-beta0', formatSigned(model.beta[0], 3));
    setText('model-beta-lt', formatSigned(model.beta[1], 3));
    setText('model-beta-mt', formatSigned(model.beta[2], 3));
    setText('model-beta-vol', formatSigned(Math.abs(model.beta[3]), 3));
    setText('model-r2', numberOr(model.r2).toFixed(3));
}

function updatePortfolio() {
    const lastRow = state.paperTrading[state.paperTrading.length - 1] || null;

    const cash = numberOr(state.portfolio?.cash, numberOr(lastRow?.cash));
    const btc = numberOr(state.portfolio?.btc, numberOr(lastRow?.btc_amount));
    const trades = state.portfolio?.trades || [];

    setText('metric-cash', formatCurrency(cash));
    setText('metric-btc', btc.toFixed(8));
    setText('metric-trades', `${numberOr(state.portfolio?.total_trades, trades.length)}`);

    updateTradesTable(trades);
}

function updateTradesTable(trades) {
    const tbody = document.getElementById('trades-list');
    if (!tbody) return;

    tbody.innerHTML = '';
    if (!Array.isArray(trades) || trades.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = '<td colspan="4">No trades yet</td>';
        tbody.appendChild(tr);
        return;
    }

    const orderedTrades = [...trades].reverse().slice(0, 18);
    orderedTrades.forEach((trade) => {
        const tr = document.createElement('tr');
        const side = (trade.Side || '').toUpperCase();
        const sideClass = side === 'BUY' ? 'trade-buy' : 'trade-sell';
        const dateObj = new Date(trade.Date);
        const dateLabel = Number.isNaN(dateObj.valueOf())
            ? trade.Date
            : dateObj.toLocaleDateString(undefined, {
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
            });

        tr.innerHTML = `
            <td>${dateLabel}</td>
            <td class="${sideClass}">${side || 'N/A'}</td>
            <td>${formatCurrency(numberOr(trade.Price))}</td>
            <td>${numberOr(trade.BTC_Amount).toFixed(6)}</td>
        `;
        tbody.appendChild(tr);
    });
}

function makeBaseTooltip() {
    return {
        backgroundColor: chartTheme.tooltipBg,
        titleColor: chartTheme.tooltipTitle,
        bodyColor: chartTheme.tooltipText,
        borderColor: chartTheme.tooltipBorder,
        borderWidth: 1,
        titleFont: { family: chartTheme.mono, size: 11 },
        bodyFont: { family: chartTheme.mono, size: 10 },
    };
}

function computeScoreAxisBounds(seriesList, options = {}) {
    const { minSpan = 20, padFactor = 0.2, step = 5 } = options;
    const values = seriesList
        .flat()
        .map((value) => numberOr(value, NaN))
        .filter(Number.isFinite);

    if (!values.length) {
        return [-100, 100];
    }

    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const rawSpan = maxValue - minValue;
    const pad = Math.max(2, rawSpan * padFactor);

    let lower = minValue - pad;
    let upper = maxValue + pad;

    if ((upper - lower) < minSpan) {
        const center = (upper + lower) / 2;
        lower = center - (minSpan / 2);
        upper = center + (minSpan / 2);
    }

    lower = Math.max(-100, lower);
    upper = Math.min(100, upper);

    const snappedLower = Math.floor(lower / step) * step;
    const snappedUpper = Math.ceil(upper / step) * step;

    if (snappedLower >= snappedUpper) {
        return [-100, 100];
    }

    return [snappedLower, snappedUpper];
}

function makeScoreTooltip() {
    return {
        ...makeBaseTooltip(),
        callbacks: {
            label(context) {
                const label = context.dataset?.label || '';
                const value = numberOr(context.parsed?.y, context.parsed);

                if (context.dataset?.yAxisID === 'y1' || /score|spread|\bLT\b|\bMT\b/i.test(label)) {
                    return `${label}: ${value.toFixed(4)}`;
                }

                if (/price|envelope/i.test(label)) {
                    return `${label}: ${formatCurrency(value)}`;
                }

                return `${label}: ${value.toFixed(2)}`;
            },
        },
    };
}

function renderPriceChart() {
    const canvas = document.getElementById('priceChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const d = state.derived;
    const rows = state.paperTrading;
    const [scoreMin, scoreMax] = computeScoreAxisBounds([d.lt, d.mt], {
        minSpan: 22,
        padFactor: 0.22,
        step: 5,
    });
    const upperBand = rows.map((row, i) => {
        if (!Number.isFinite(d.vol30[i])) return null;
        return row.btc_price * (1 + (d.vol30[i] / 100) * 0.35);
    });
    const lowerBand = rows.map((row, i) => {
        if (!Number.isFinite(d.vol30[i])) return null;
        return row.btc_price * Math.max(0.1, (1 - (d.vol30[i] / 100) * 0.35));
    });

    charts.price = new Chart(ctx, {
        type: 'line',
        data: {
            labels: d.dates,
            datasets: [
                {
                    label: 'Risk Upper Envelope',
                    data: upperBand,
                    yAxisID: 'y',
                    borderColor: 'rgba(255, 179, 71, 0.35)',
                    pointRadius: 0,
                    borderWidth: 1,
                    tension: 0.25,
                },
                {
                    label: 'Risk Lower Envelope',
                    data: lowerBand,
                    yAxisID: 'y',
                    borderColor: 'rgba(58, 216, 255, 0.28)',
                    backgroundColor: 'rgba(58, 216, 255, 0.08)',
                    pointRadius: 0,
                    borderWidth: 1,
                    fill: '-1',
                    tension: 0.25,
                },
                {
                    label: 'BTC Price',
                    data: d.prices,
                    yAxisID: 'y',
                    borderColor: '#3ad8ff',
                    backgroundColor: 'rgba(58, 216, 255, 0.12)',
                    borderWidth: 2.2,
                    pointRadius: 0,
                    tension: 0.25,
                },
                {
                    label: 'LT Score',
                    data: d.lt,
                    yAxisID: 'y1',
                    borderColor: '#7dff89',
                    pointRadius: 0,
                    borderWidth: 1.9,
                    tension: 0.27,
                },
                {
                    label: 'MT Score',
                    data: d.mt,
                    yAxisID: 'y1',
                    borderColor: '#ffb347',
                    pointRadius: 0,
                    borderWidth: 1.8,
                    tension: 0.27,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    labels: {
                        color: chartTheme.ticks,
                        font: { family: chartTheme.mono, size: 10 },
                    },
                },
                tooltip: makeScoreTooltip(),
            },
            scales: {
                x: {
                    type: 'time',
                    time: { unit: 'month' },
                    grid: { color: chartTheme.grid },
                    ticks: {
                        color: chartTheme.ticks,
                        font: { family: chartTheme.mono, size: 9 },
                    },
                },
                y: {
                    position: 'left',
                    grid: { color: chartTheme.grid },
                    ticks: {
                        color: chartTheme.ticks,
                        font: { family: chartTheme.mono, size: 9 },
                        callback(value) { return `$${Number(value).toLocaleString()}`; },
                    },
                    title: {
                        display: true,
                        text: 'Price USD',
                        color: chartTheme.title,
                        font: { family: chartTheme.mono, size: 10 },
                    },
                },
                y1: {
                    position: 'right',
                    min: scoreMin,
                    max: scoreMax,
                    grid: { drawOnChartArea: false },
                    ticks: {
                        color: chartTheme.ticks,
                        font: { family: chartTheme.mono, size: 9 },
                        callback(value) { return Number(value).toFixed(1); },
                    },
                    title: {
                        display: true,
                        text: 'Scores',
                        color: chartTheme.title,
                        font: { family: chartTheme.mono, size: 10 },
                    },
                },
            },
        },
    });
}

function renderPerformanceChart() {
    const canvas = document.getElementById('performanceChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const d = state.derived;

    charts.performance = new Chart(ctx, {
        data: {
            labels: d.dates,
            datasets: [
                {
                    type: 'line',
                    label: 'Strategy Return %',
                    data: d.strategyCum,
                    yAxisID: 'y',
                    borderColor: '#36f2c5',
                    backgroundColor: 'rgba(54, 242, 197, 0.10)',
                    borderWidth: 2.1,
                    pointRadius: 0,
                    tension: 0.24,
                },
                {
                    type: 'line',
                    label: 'Buy and Hold %',
                    data: d.bnhCum,
                    yAxisID: 'y',
                    borderColor: '#3a89ff',
                    backgroundColor: 'rgba(58, 137, 255, 0.08)',
                    borderWidth: 1.9,
                    pointRadius: 0,
                    tension: 0.24,
                },
                {
                    type: 'bar',
                    label: 'Drawdown %',
                    data: d.drawdown,
                    yAxisID: 'y1',
                    backgroundColor: 'rgba(255, 95, 113, 0.18)',
                    borderColor: 'rgba(255, 95, 113, 0.45)',
                    borderWidth: 0.8,
                    barPercentage: 1,
                    categoryPercentage: 1,
                },
                {
                    type: 'line',
                    label: 'Rolling Sharpe 30D',
                    data: d.sharpe30,
                    yAxisID: 'y2',
                    borderColor: '#ffb347',
                    borderDash: [7, 5],
                    borderWidth: 1.5,
                    pointRadius: 0,
                    tension: 0.2,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    labels: {
                        color: chartTheme.ticks,
                        font: { family: chartTheme.mono, size: 10 },
                    },
                },
                tooltip: makeBaseTooltip(),
            },
            scales: {
                x: {
                    type: 'time',
                    time: { unit: 'month' },
                    grid: { color: chartTheme.grid },
                    ticks: {
                        color: chartTheme.ticks,
                        font: { family: chartTheme.mono, size: 9 },
                    },
                },
                y: {
                    position: 'left',
                    grid: { color: chartTheme.grid },
                    ticks: {
                        color: chartTheme.ticks,
                        font: { family: chartTheme.mono, size: 9 },
                        callback(value) { return `${Number(value).toFixed(0)}%`; },
                    },
                    title: {
                        display: true,
                        text: 'Return %',
                        color: chartTheme.title,
                        font: { family: chartTheme.mono, size: 10 },
                    },
                },
                y1: {
                    position: 'right',
                    min: -85,
                    max: 5,
                    grid: { drawOnChartArea: false },
                    ticks: {
                        color: '#fca5af',
                        font: { family: chartTheme.mono, size: 9 },
                        callback(value) { return `${Number(value).toFixed(0)}%`; },
                    },
                    title: {
                        display: true,
                        text: 'Drawdown %',
                        color: '#fca5af',
                        font: { family: chartTheme.mono, size: 10 },
                    },
                },
                y2: {
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    ticks: {
                        color: '#fdd67b',
                        font: { family: chartTheme.mono, size: 9 },
                    },
                    title: {
                        display: true,
                        text: 'Sharpe 30D',
                        color: '#fdd67b',
                        font: { family: chartTheme.mono, size: 10 },
                    },
                },
            },
        },
    });
}

function renderScoreHistoryChart() {
    const canvas = document.getElementById('scoreHistoryChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const d = state.derived;
    const [scoreMin, scoreMax] = computeScoreAxisBounds([d.lt, d.mt, d.spread], {
        minSpan: 18,
        padFactor: 0.24,
        step: 2,
    });

    charts.scoreHistory = new Chart(ctx, {
        type: 'line',
        data: {
            labels: d.dates,
            datasets: [
                {
                    label: 'LT',
                    data: d.lt,
                    borderColor: '#7dff89',
                    backgroundColor: 'rgba(125, 255, 137, 0.12)',
                    borderWidth: 1.9,
                    pointRadius: 0,
                    tension: 0.28,
                },
                {
                    label: 'MT',
                    data: d.mt,
                    borderColor: '#ffb347',
                    backgroundColor: 'rgba(255, 179, 71, 0.10)',
                    borderWidth: 1.8,
                    pointRadius: 0,
                    tension: 0.28,
                },
                {
                    label: 'Spread LT-MT',
                    data: d.spread,
                    borderColor: '#3ad8ff',
                    borderDash: [6, 4],
                    borderWidth: 1.2,
                    pointRadius: 0,
                    tension: 0.22,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    labels: {
                        color: chartTheme.ticks,
                        font: { family: chartTheme.mono, size: 10 },
                    },
                },
                tooltip: makeScoreTooltip(),
            },
            scales: {
                x: {
                    type: 'time',
                    time: { unit: 'month' },
                    grid: { color: chartTheme.grid },
                    ticks: {
                        color: chartTheme.ticks,
                        font: { family: chartTheme.mono, size: 9 },
                    },
                },
                y: {
                    min: scoreMin,
                    max: scoreMax,
                    grid: { color: chartTheme.grid },
                    ticks: {
                        color: chartTheme.ticks,
                        font: { family: chartTheme.mono, size: 9 },
                        callback(value) { return Number(value).toFixed(2); },
                    },
                },
            },
        },
    });
}

function renderPortfolioChart() {
    const canvas = document.getElementById('portfolioChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const cash = numberOr(state.portfolio?.cash, numberOr(state.paperTrading.at(-1)?.cash));
    const btcValue = numberOr(state.portfolio?.btc_value, numberOr(state.paperTrading.at(-1)?.btc_value));
    const debt = Math.max(0, numberOr(state.portfolio?.debt, numberOr(state.paperTrading.at(-1)?.debt)));

    const labels = debt > 0 ? ['Cash', 'Bitcoin', 'Debt'] : ['Cash', 'Bitcoin'];
    const values = debt > 0 ? [cash, btcValue, debt] : [cash, btcValue];
    const colors = debt > 0
        ? ['rgba(125, 255, 137, 0.86)', 'rgba(58, 216, 255, 0.86)', 'rgba(255, 95, 113, 0.86)']
        : ['rgba(125, 255, 137, 0.86)', 'rgba(58, 216, 255, 0.86)'];

    charts.portfolio = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: '#0f1e35',
                borderWidth: 2,
                hoverOffset: 8,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: chartTheme.ticks,
                        font: { family: chartTheme.mono, size: 10 },
                        padding: 14,
                    },
                },
                tooltip: {
                    ...makeBaseTooltip(),
                    callbacks: {
                        label(context) {
                            const value = numberOr(context.parsed);
                            const total = values.reduce((acc, v) => acc + numberOr(v), 0);
                            const pct = total > 0 ? (value / total) * 100 : 0;
                            return `${context.label}: ${formatCurrency(value)} (${pct.toFixed(1)}%)`;
                        },
                    },
                },
            },
            cutout: '62%',
        },
    });
}

function fillSurfaceGaps(matrix, passes = 6) {
    const h = matrix.length;
    const w = matrix[0].length;

    for (let pass = 0; pass < passes; pass += 1) {
        const next = matrix.map((row) => [...row]);

        for (let y = 0; y < h; y += 1) {
            for (let x = 0; x < w; x += 1) {
                if (Number.isFinite(matrix[y][x])) continue;
                const neighbors = [];

                for (let dy = -1; dy <= 1; dy += 1) {
                    for (let dx = -1; dx <= 1; dx += 1) {
                        if (dx === 0 && dy === 0) continue;
                        const ny = y + dy;
                        const nx = x + dx;
                        if (ny < 0 || ny >= h || nx < 0 || nx >= w) continue;
                        const v = matrix[ny][nx];
                        if (Number.isFinite(v)) neighbors.push(v);
                    }
                }

                if (neighbors.length >= 3) {
                    next[y][x] = neighbors.reduce((acc, v) => acc + v, 0) / neighbors.length;
                }
            }
        }

        for (let y = 0; y < h; y += 1) {
            for (let x = 0; x < w; x += 1) {
                matrix[y][x] = next[y][x];
            }
        }
    }

    for (let y = 0; y < h; y += 1) {
        for (let x = 0; x < w; x += 1) {
            if (!Number.isFinite(matrix[y][x])) {
                matrix[y][x] = 0;
            }
        }
    }
}

function buildSurfaceMatrix(rows, forward7) {
    const axis = [];
    for (let v = -100; v <= 100; v += 10) axis.push(v);

    const size = axis.length;
    const sums = Array.from({ length: size }, () => Array(size).fill(0));
    const counts = Array.from({ length: size }, () => Array(size).fill(0));

    for (let i = 0; i < rows.length; i += 1) {
        const z = forward7[i];
        if (!Number.isFinite(z)) continue;

        const xScore = Math.max(-100, Math.min(100, numberOr(rows[i].lt_score)));
        const yScore = Math.max(-100, Math.min(100, numberOr(rows[i].mt_score)));
        const xIndex = Math.round((xScore + 100) / 10);
        const yIndex = Math.round((yScore + 100) / 10);

        sums[yIndex][xIndex] += z;
        counts[yIndex][xIndex] += 1;
    }

    const matrix = sums.map((row, y) => row.map((sum, x) => {
        const c = counts[y][x];
        return c > 0 ? sum / c : null;
    }));

    fillSurfaceGaps(matrix);
    return { axis, matrix };
}

function renderSignalSurface3D() {
    const container = document.getElementById('signal-surface-3d');
    if (!container || !window.Plotly) return;

    const { axis, matrix } = buildSurfaceMatrix(state.paperTrading, state.derived.forward7);

    const trace = {
        type: 'surface',
        x: axis,
        y: axis,
        z: matrix,
        colorscale: [
            [0, '#ff5f71'],
            [0.5, '#ffb347'],
            [1, '#7dff89'],
        ],
        contours: {
            z: { show: true, usecolormap: true, highlightwidth: 1 },
        },
        colorbar: {
            title: '7d Return %',
            titlefont: { family: chartTheme.mono, color: '#d6e3f7', size: 10 },
            tickfont: { family: chartTheme.mono, color: '#d6e3f7', size: 9 },
            thickness: 8,
            len: 0.7,
        },
    };

    const layout = {
        margin: { l: 0, r: 0, b: 0, t: 12 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        scene: {
            xaxis: {
                title: 'LT Score',
                titlefont: { family: chartTheme.mono, color: '#a8bad8', size: 10 },
                tickfont: { family: chartTheme.mono, color: '#95a9cb', size: 9 },
                gridcolor: 'rgba(149, 169, 203, 0.25)',
                zerolinecolor: 'rgba(149, 169, 203, 0.25)',
            },
            yaxis: {
                title: 'MT Score',
                titlefont: { family: chartTheme.mono, color: '#a8bad8', size: 10 },
                tickfont: { family: chartTheme.mono, color: '#95a9cb', size: 9 },
                gridcolor: 'rgba(149, 169, 203, 0.25)',
                zerolinecolor: 'rgba(149, 169, 203, 0.25)',
            },
            zaxis: {
                title: 'Expected 7D Return %',
                titlefont: { family: chartTheme.mono, color: '#a8bad8', size: 10 },
                tickfont: { family: chartTheme.mono, color: '#95a9cb', size: 9 },
                gridcolor: 'rgba(149, 169, 203, 0.25)',
                zerolinecolor: 'rgba(149, 169, 203, 0.25)',
            },
            camera: {
                eye: { x: 1.55, y: 1.35, z: 0.88 },
            },
        },
    };

    window.Plotly.react(container, [trace], layout, {
        responsive: true,
        displayModeBar: false,
    });
}

function renderRegimeTrajectory3D() {
    const container = document.getElementById('regime-trajectory-3d');
    if (!container || !window.Plotly) return;

    const rows = state.paperTrading;
    const d = state.derived;
    const start = Math.max(0, rows.length - 220);
    const x = [];
    const y = [];
    const z = [];
    const color = [];
    const labels = [];

    for (let i = start; i < rows.length; i += 1) {
        if (!Number.isFinite(d.vol30[i])) continue;
        x.push(rows[i].lt_score);
        y.push(rows[i].mt_score);
        z.push(d.vol30[i]);
        color.push(numberOr(d.forward7[i], 0));
        labels.push(rows[i].date);
    }

    if (x.length < 10) {
        window.Plotly.react(container, [], {
            margin: { l: 0, r: 0, t: 14, b: 0 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            annotations: [{
                text: 'Not enough data for trajectory',
                showarrow: false,
                font: { color: '#9ab2d4', family: chartTheme.mono, size: 11 },
            }],
        }, { responsive: true, displayModeBar: false });
        return;
    }

    const lineTrace = {
        type: 'scatter3d',
        mode: 'lines+markers',
        x,
        y,
        z,
        text: labels,
        hovertemplate: 'Date %{text}<br>LT %{x:.1f}<br>MT %{y:.1f}<br>Vol %{z:.2f}%<br>Fwd7 %{marker.color:.2f}%<extra></extra>',
        marker: {
            size: 3.7,
            color,
            colorscale: [
                [0, '#ff5f71'],
                [0.5, '#ffb347'],
                [1, '#7dff89'],
            ],
            cmin: -12,
            cmax: 12,
            opacity: 0.92,
        },
        line: {
            color: 'rgba(58, 216, 255, 0.52)',
            width: 3,
        },
        name: 'Regime Path',
    };

    const latestTrace = {
        type: 'scatter3d',
        mode: 'markers',
        x: [x[x.length - 1]],
        y: [y[y.length - 1]],
        z: [z[z.length - 1]],
        marker: {
            size: 7,
            color: '#3ad8ff',
            line: { width: 1, color: '#e9f5ff' },
        },
        name: 'Latest',
        hovertemplate: 'Latest state<br>LT %{x:.1f}<br>MT %{y:.1f}<br>Vol %{z:.2f}%<extra></extra>',
    };

    const layout = {
        margin: { l: 0, r: 0, b: 0, t: 12 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        legend: {
            font: { color: '#9ab2d4', family: chartTheme.mono, size: 9 },
            orientation: 'h',
            y: 0.98,
            x: 0,
        },
        scene: {
            xaxis: {
                title: 'LT',
                titlefont: { family: chartTheme.mono, color: '#a8bad8', size: 10 },
                tickfont: { family: chartTheme.mono, color: '#95a9cb', size: 9 },
                gridcolor: 'rgba(149, 169, 203, 0.2)',
            },
            yaxis: {
                title: 'MT',
                titlefont: { family: chartTheme.mono, color: '#a8bad8', size: 10 },
                tickfont: { family: chartTheme.mono, color: '#95a9cb', size: 9 },
                gridcolor: 'rgba(149, 169, 203, 0.2)',
            },
            zaxis: {
                title: 'Vol30 %',
                titlefont: { family: chartTheme.mono, color: '#a8bad8', size: 10 },
                tickfont: { family: chartTheme.mono, color: '#95a9cb', size: 9 },
                gridcolor: 'rgba(149, 169, 203, 0.2)',
            },
            camera: {
                eye: { x: 1.45, y: 1.28, z: 0.78 },
            },
        },
    };

    window.Plotly.react(container, [lineTrace, latestTrace], layout, {
        responsive: true,
        displayModeBar: false,
    });
}

function safePlotlyResize() {
    if (!window.Plotly) return;
    ['signal-surface-3d', 'regime-trajectory-3d'].forEach((id) => {
        const el = document.getElementById(id);
        if (el && el.data) {
            window.Plotly.Plots.resize(el);
        }
    });
}

function applyMathRendering() {
    if (typeof window.renderMathInElement !== 'function') return;
    window.renderMathInElement(document.body, {
        delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$', right: '$', display: false },
        ],
        throwOnError: false,
    });
}

async function loadAllData() {
    console.log('Loading quant deck data...');

    const [paperTrading, scores, portfolio, metrics, processedData] = await Promise.all([
        fetchData('paper-trading-history'),
        fetchData('current-scores'),
        fetchData('portfolio'),
        fetchData('performance-metrics'),
        fetchData('latest-processed-data'),
    ]);

    const normalizedRows = normalizePaperTrading(paperTrading);
    if (!normalizedRows.length) {
        console.warn('No paper trading data available');
        return;
    }

    state.paperTrading = normalizedRows;
    state.scores = scores;
    state.portfolio = portfolio;
    state.metrics = metrics;
    state.processedData = processedData;
    state.derived = buildDerivedSeries(normalizedRows);

    updateHeader();
    updateMetrics();
    updateScores();
    updateModelCard();
    updatePortfolio();

    destroyVisuals();
    renderPriceChart();
    renderPerformanceChart();
    renderScoreHistoryChart();
    renderPortfolioChart();
    renderSignalSurface3D();
    renderRegimeTrajectory3D();
    safePlotlyResize();

    if (refreshTimer) clearInterval(refreshTimer);
    refreshTimer = setInterval(loadAllData, REFRESH_INTERVAL);
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('Bitcoin Quant Intelligence Deck initializing...');
    applyMathRendering();
    loadAllData();
});

window.addEventListener('resize', () => {
    safePlotlyResize();
});
