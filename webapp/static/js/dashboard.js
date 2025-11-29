/**
 * Bitcoin Quant Dashboard - Main JavaScript
 * Handles data fetching, chart rendering, and UI updates
 * PAPER TRADING MODE - Shows only real trading data from Nov 23, 2025
 */

// Global state
const state = {
    paperTrading: null,
    scores: null,
    portfolio: null,
    metrics: null,
    processedData: null
};

// Chart instances
const charts = {};

// Auto-refresh interval (60 seconds)
const REFRESH_INTERVAL = 60000;
let refreshTimer = null;

// Utility Functions
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

function formatPercent(value) {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
}

function formatNumber(value, decimals = 2) {
    return value.toFixed(decimals);
}

// API Functions
async function fetchData(endpoint) {
    try {
        const response = await fetch(`/api/${endpoint}`);
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error);
        }
        return data.data;
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        return null;
    }
}

async function loadAllData() {
    console.log('Loading paper trading data...');

    // Fetch all data in parallel
    const [paperTrading, scores, portfolio, metrics, processedData] = await Promise.all([
        fetchData('paper-trading-history'),
        fetchData('current-scores'),
        fetchData('portfolio'),
        fetchData('performance-metrics'),
        fetchData('latest-processed-data')
    ]);

    state.paperTrading = paperTrading;
    state.scores = scores;
    state.portfolio = portfolio;
    state.metrics = metrics;
    state.processedData = processedData;

    console.log('Paper trading data loaded successfully');

    // Update UI
    updateMetrics();
    updateScores();
    updatePortfolio();

    // Destroy existing charts
    if (charts.price) charts.price.destroy();
    if (charts.performance) charts.performance.destroy();
    if (charts.portfolio) charts.portfolio.destroy();
    if (charts.scoreHistory) charts.scoreHistory.destroy();

    // Render charts
    renderPriceChart();
    renderPerformanceChart();
    renderPortfolioChart();
    renderScoreHistoryChart();

    // Start auto-refresh
    if (refreshTimer) clearInterval(refreshTimer);
    refreshTimer = setInterval(loadAllData, REFRESH_INTERVAL);
}

// Update UI Functions
function updateMetrics() {
    if (!state.metrics) return;

    const { strategy_return, bnh_return, sp500_return, alpha, max_drawdown, sharpe_ratio } = state.metrics;

    // Total Return
    document.getElementById('metric-return').textContent = formatPercent(strategy_return);
    document.getElementById('metric-return-sub').textContent = `vs S&P500: ${formatPercent(sp500_return)}`;

    // Alpha
    document.getElementById('metric-alpha').textContent = formatPercent(alpha);
    const alphaBadge = document.getElementById('metric-alpha-badge');
    if (alpha > 0) {
        alphaBadge.textContent = 'OUTPERFORM';
        alphaBadge.style.color = 'var(--accent-green)';
    } else {
        alphaBadge.textContent = 'UNDERPERFORM';
        alphaBadge.style.color = 'var(--accent-red)';
    }

    // Max Drawdown
    document.getElementById('metric-dd').textContent = formatPercent(max_drawdown);

    // Sharpe Ratio
    document.getElementById('metric-sharpe').textContent = formatNumber(sharpe_ratio, 2);
}

function updateScores() {
    if (!state.scores) return;

    const ltScore = parseFloat(state.scores.Long_Term_Score);
    const mtScore = parseFloat(state.scores.Medium_Term_Score);

    // Update controls
    document.getElementById('control-lt').textContent = formatNumber(ltScore, 1);
    document.getElementById('control-mt').textContent = formatNumber(mtScore, 1);

    // Helper to get color and update elements
    const updateScoreVisuals = (score, displayId, barId) => {
        const display = document.getElementById(displayId);
        const bar = document.getElementById(barId);

        display.textContent = formatNumber(score, 2);

        // Determine text color
        let color;
        if (score > 0) color = 'var(--accent-green)';
        else if (score < 0) color = 'var(--accent-red)';
        else color = 'var(--accent-yellow)';

        // Apply color to text
        display.style.color = color;

        // Calculate percentage (0 to 100)
        // -100 -> 0%, 0 -> 50%, 100 -> 100%
        let percent = ((score + 100) / 200) * 100;

        // Clamp percentage
        percent = Math.max(0, Math.min(100, percent));

        // Apply width
        bar.style.width = `${percent}%`;

        // Apply fixed-scale gradient
        // We set the background size inversely proportional to the width
        // so the gradient always spans the full container width (0-100%)
        // regardless of how wide the bar actually is.
        bar.style.backgroundImage = 'linear-gradient(90deg, var(--accent-red), var(--accent-yellow), var(--accent-green))';

        if (percent > 0) {
            bar.style.backgroundSize = `${(100 / percent) * 100}% 100%`;
        } else {
            bar.style.backgroundSize = '100% 100%';
        }
    };

    updateScoreVisuals(ltScore, 'score-lt-display', 'score-lt-bar');
    updateScoreVisuals(mtScore, 'score-mt-display', 'score-mt-bar');

    // Update market phase
    if (state.processedData && state.processedData.market_cycle_phase) {
        const phase = state.processedData.market_cycle_phase;
        const phaseBadge = document.getElementById('metric-phase');
        phaseBadge.textContent = phase;

        if (phase.includes('Accumulation') || phase.includes('Rally')) {
            phaseBadge.style.color = 'var(--accent-green)';
        } else if (phase.includes('Bear') || phase.includes('Distribution')) {
            phaseBadge.style.color = 'var(--accent-red)';
        } else {
            phaseBadge.style.color = 'var(--accent-yellow)';
        }
    }
}

function updatePortfolio() {
    if (!state.portfolio) return;

    const { cash, btc, btc_value, debt, equity, total_trades, trades } = state.portfolio;

    document.getElementById('metric-cash').textContent = formatCurrency(cash);
    document.getElementById('metric-btc').textContent = formatNumber(btc, 8);
    document.getElementById('metric-trades').textContent = total_trades;

    // Update header
    if (state.paperTrading && state.paperTrading.length > 0) {
        const latestPrice = state.paperTrading[state.paperTrading.length - 1].btc_price;
        document.getElementById('header-price').textContent = formatCurrency(latestPrice);
        document.getElementById('header-equity').textContent = formatCurrency(equity);
    }

    if (state.metrics) {
        document.getElementById('header-roi').textContent = formatPercent(state.metrics.strategy_return);
    }

    // Update Trades Table
    updateTradesTable(trades);
}

function updateTradesTable(trades) {
    const tbody = document.getElementById('trades-list');
    if (!tbody || !trades) return;

    tbody.innerHTML = '';

    // Sort trades by date descending and take last 20
    const sortedTrades = [...trades].reverse().slice(0, 20);

    sortedTrades.forEach(trade => {
        const tr = document.createElement('tr');

        // Format date (short)
        const dateObj = new Date(trade.Date);
        const dateStr = dateObj.toLocaleDateString(undefined, { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });

        const sideClass = trade.Side === 'BUY' ? 'trade-buy' : 'trade-sell';

        tr.innerHTML = `
            <td>${dateStr}</td>
            <td class="${sideClass}">${trade.Side}</td>
            <td>${formatCurrency(trade.Price)}</td>
            <td>${formatNumber(trade.BTC_Amount, 6)}</td>
        `;

        tbody.appendChild(tr);
    });
}

// Chart Rendering Functions
function renderPriceChart() {
    if (!state.paperTrading) return;

    const ctx = document.getElementById('priceChart').getContext('2d');

    // Sample data for better performance (take every 7th point for weekly data)
    const sampledData = state.paperTrading.filter((_, i) => i % 7 === 0);

    const data = {
        labels: state.paperTrading.map(d => d.date),
        datasets: [
            {
                label: 'Bitcoin Price',
                data: state.paperTrading.map(d => d.btc_price),
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                borderWidth: 2,
                fill: true,
                yAxisID: 'y',
                tension: 0.4
            },
            {
                label: 'Long-Term Score',
                data: state.paperTrading.map(d => d.lt_score),
                borderColor: '#059669',
                backgroundColor: 'transparent',
                borderWidth: 2,
                yAxisID: 'y1',
                tension: 0.4
            },
            {
                label: 'Medium-Term Score',
                data: state.paperTrading.map(d => d.mt_score),
                borderColor: '#d97706',
                backgroundColor: 'transparent',
                borderWidth: 2,
                yAxisID: 'y1',
                tension: 0.4
            }
        ]
    };

    charts.price = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff',
                        font: {
                            size: 11,
                            family: 'Roboto Mono'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleColor: '#ff6b00',
                    bodyColor: '#ffffff',
                    borderColor: '#ff6b00',
                    borderWidth: 1,
                    titleFont: {
                        family: 'Roboto Mono',
                        size: 11
                    },
                    bodyFont: {
                        family: 'Roboto Mono',
                        size: 10
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day'
                    },
                    grid: {
                        color: '#1a1a1a',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#707070',
                        font: {
                            family: 'Roboto Mono',
                            size: 9
                        }
                    }
                },
                y: {
                    type: 'linear',
                    position: 'left',
                    grid: {
                        color: '#1a1a1a',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#b0b0b0',
                        font: {
                            family: 'Roboto Mono',
                            size: 9
                        },
                        callback: function (value) {
                            return '$' + value.toLocaleString();
                        }
                    },
                    title: {
                        display: true,
                        text: 'Price (USD)',
                        color: '#b0b0b0', // Updated color
                        font: {
                            family: 'Roboto Mono',
                            size: 10
                        }
                    }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    min: -100,
                    max: 100,
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        color: '#707070',
                        font: {
                            family: 'Roboto Mono',
                            size: 9
                        }
                    },
                    title: {
                        display: true,
                        text: 'Score',
                        color: '#707070', // Updated color
                        font: {
                            family: 'Roboto Mono',
                            size: 10
                        }
                    }
                }
            }
        }
    });
}

function renderPerformanceChart() {
    if (!state.paperTrading) return;

    const ctx = document.getElementById('performanceChart').getContext('2d');

    // Calculate cumulative returns from equity
    const initialCapital = 2000;
    const initialPrice = state.paperTrading[0].btc_price;

    const strategyReturns = state.paperTrading.map(d => ((d.equity - initialCapital) / initialCapital) * 100);
    const bnhReturns = state.paperTrading.map(d => ((d.btc_price - initialPrice) / initialPrice) * 100);

    const data = {
        labels: state.paperTrading.map(d => d.date),
        datasets: [
            {
                label: 'Quant Strategy',
                data: strategyReturns,
                borderColor: '#7c3aed',
                backgroundColor: 'rgba(124, 58, 237, 0.15)',
                borderWidth: 2.5,
                fill: true,
                tension: 0.4
            },
            {
                label: 'Buy & Hold',
                data: bnhReturns,
                borderColor: '#64748b',
                backgroundColor: 'rgba(100, 116, 139, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }
        ]
    };

    charts.performance = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff',
                        font: {
                            size: 11,
                            family: 'Roboto Mono'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleColor: '#ff6b00',
                    bodyColor: '#ffffff',
                    borderColor: '#ff6b00',
                    borderWidth: 1,
                    titleFont: { family: 'Roboto Mono', size: 11 },
                    bodyFont: { family: 'Roboto Mono', size: 10 },
                    callbacks: {
                        label: function (context) {
                            return context.dataset.label + ': ' + context.parsed.y.toFixed(2) + '%';
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: { unit: 'month' },
                    grid: { color: '#1a1a1a', drawBorder: false },
                    ticks: {
                        color: '#707070',
                        font: { family: 'Roboto Mono', size: 9 }
                    }
                },
                y: {
                    grid: { color: '#1a1a1a', drawBorder: false },
                    ticks: {
                        color: '#b0b0b0',
                        font: { family: 'Roboto Mono', size: 9 },
                        callback: function (value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

function renderPortfolioChart() {
    if (!state.portfolio) return;

    const ctx = document.getElementById('portfolioChart').getContext('2d');

    const { cash, btc_value, debt } = state.portfolio;

    // Include debt as a separate segment
    const labels = debt > 0 ? ['Cash (USD)', 'Bitcoin', 'Debt'] : ['Cash (USD)', 'Bitcoin'];
    const values = debt > 0 ? [cash, btc_value, debt] : [cash, btc_value];
    const colors = debt > 0 ? [
        'rgba(16, 185, 129, 0.8)',
        'rgba(0, 212, 255, 0.8)',
        'rgba(239, 68, 68, 0.8)'
    ] : [
        'rgba(16, 185, 129, 0.8)',
        'rgba(0, 212, 255, 0.8)'
    ];
    const borderColors = debt > 0 ? ['#10b981', '#00d4ff', '#ef4444'] : ['#10b981', '#00d4ff'];

    const data = {
        labels: labels,
        datasets: [{
            data: values,
            backgroundColor: colors,
            borderColor: borderColors,
            borderWidth: 2
        }]
    };

    charts.portfolio = new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#ffffff',
                        font: { size: 10, family: 'Roboto Mono' },
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleColor: '#ff6b00',
                    bodyColor: '#ffffff',
                    borderColor: '#ff6b00',
                    borderWidth: 1,
                    titleFont: { family: 'Roboto Mono', size: 11 },
                    bodyFont: { family: 'Roboto Mono', size: 10 },
                    callbacks: {
                        label: function (context) {
                            const value = context.parsed;
                            const total = cash + btc_value + (debt || 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return context.label + ': ' + formatCurrency(value) + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });
}

function renderScoreHistoryChart() {
    if (!state.paperTrading) return;

    const ctx = document.getElementById('scoreHistoryChart').getContext('2d');

    const data = {
        labels: state.paperTrading.map(d => d.date),
        datasets: [
            {
                label: 'Long-Term Score',
                data: state.paperTrading.map(d => d.lt_score),
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            },
            {
                label: 'Medium-Term Score',
                data: state.paperTrading.map(d => d.mt_score),
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }
        ]
    };

    charts.scoreHistory = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#f8fafc',
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(10, 14, 39, 0.9)',
                    titleColor: '#f8fafc',
                    bodyColor: '#94a3b8',
                    borderColor: '#10b981',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day'
                    },
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                },
                y: {
                    min: -100,
                    max: 100,
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                }
            }
        }
    });
}

function renderActionsChart() {
    if (!state.metrics || !state.metrics.action_counts) return;

    const ctx = document.getElementById('actionsChart').getContext('2d');

    const actionCounts = state.metrics.action_counts;
    const labels = Object.keys(actionCounts);
    const values = Object.values(actionCounts);

    // Color mapping for different actions
    const colorMap = {
        'WAIT': '#64748b',
        'BUY': '#10b981',
        'SELL': '#ef4444',
        'STRONG_BUY': '#7c3aed',
        'BUY_SCALP': '#00d4ff',
        'ACCUMULATE': '#f59e0b'
    };

    const colors = labels.map(label => colorMap[label] || '#94a3b8');

    const data = {
        labels: labels,
        datasets: [{
            data: values,
            backgroundColor: colors.map(c => c + 'cc'),
            borderColor: colors,
            borderWidth: 2
        }]
    };

    charts.actions = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(10, 14, 39, 0.9)',
                    titleColor: '#f8fafc',
                    bodyColor: '#94a3b8',
                    borderColor: '#00d4ff',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                }
            }
        }
    });
}

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('Bitcoin Quant Dashboard initializing...');
    loadAllData();
});
