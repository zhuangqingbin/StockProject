/**
 * Stock BI - A股数据可视化平台
 * v2.1: 支持实时更新、板块/行业涨跌分离、Top N 筛选、股票详情弹窗
 */

const API_BASE = '/api/market';
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_URL = `${WS_PROTOCOL}//${window.location.host}/ws/market`;

// 全局状态
const state = {
    currentDate: null,
    summary: null,
    charts: {},
    currentView: 'distribution',
    topN: 10,
    order: 'desc',
    ws: null,
    wsReconnectTimer: null,
    wsConnected: false,
    rankingData: [],  // 缓存排名数据供点击使用
    industryData: [],  // 缓存行业数据供点击使用
    currentIndustry: null,  // 当前选中的行业
    industryOrder: 'desc'  // 行业股票排序方向
};

// DOM 元素
const elements = {
    loadingOverlay: document.getElementById('loadingOverlay'),
    currentDate: document.getElementById('currentDate'),
    refreshBtn: document.getElementById('refreshBtn'),
    mainChart: document.getElementById('mainChart'),
    northChart: document.getElementById('northChart'),
    amountChart: document.getElementById('amountChart'),
    chatMessages: document.getElementById('chatMessages'),
    chatInput: document.getElementById('chatInput'),
    chatSend: document.getElementById('chatSend'),
    topNSelect: document.getElementById('topNSelect'),
    orderToggle: document.getElementById('orderToggle'),
    wsDot: document.getElementById('wsDot'),
    wsText: document.getElementById('wsText'),
    updateBanner: document.getElementById('updateBanner'),
    stockModal: document.getElementById('stockModal'),
    toast: document.getElementById('toast')
};

// ================== WebSocket 连接 ==================

function connectWebSocket() {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        return;
    }
    
    updateWsStatus('connecting');
    
    try {
        state.ws = new WebSocket(WS_URL);
        
        state.ws.onopen = () => {
            console.log('📡 WebSocket 已连接');
            state.wsConnected = true;
            updateWsStatus('connected');
            
            // 清除重连定时器
            if (state.wsReconnectTimer) {
                clearTimeout(state.wsReconnectTimer);
                state.wsReconnectTimer = null;
            }
        };
        
        state.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleWsMessage(data);
            } catch (e) {
                console.error('解析 WebSocket 消息失败:', e);
            }
        };
        
        state.ws.onclose = () => {
            console.log('📡 WebSocket 已断开');
            state.wsConnected = false;
            updateWsStatus('disconnected');
            scheduleReconnect();
        };
        
        state.ws.onerror = (error) => {
            console.error('WebSocket 错误:', error);
            state.wsConnected = false;
            updateWsStatus('disconnected');
        };
    } catch (e) {
        console.error('WebSocket 连接失败:', e);
        updateWsStatus('disconnected');
        scheduleReconnect();
    }
}

function scheduleReconnect() {
    if (state.wsReconnectTimer) return;
    
    state.wsReconnectTimer = setTimeout(() => {
        state.wsReconnectTimer = null;
        console.log('📡 尝试重新连接 WebSocket...');
        connectWebSocket();
    }, 5000);
}

function updateWsStatus(status) {
    const dot = elements.wsDot;
    const text = elements.wsText;
    
    dot.className = 'ws-dot ' + status;
    
    switch (status) {
        case 'connected':
            text.textContent = '已连接';
            break;
        case 'disconnected':
            text.textContent = '未连接';
            break;
        case 'connecting':
            text.textContent = '连接中...';
            break;
    }
}

function handleWsMessage(data) {
    console.log('📨 收到消息:', data.type);
    
    switch (data.type) {
        case 'connected':
            console.log('服务器确认连接, 最新交易日:', data.trade_date);
            break;
            
        case 'data_updated':
            console.log('数据更新通知:', data.trade_date);
            showUpdateBanner(data.trade_date);
            break;
            
        case 'pong':
            // 心跳响应
            break;
    }
}

function showUpdateBanner(tradeDate) {
    elements.updateBanner.classList.add('show');
    
    // 5秒后自动隐藏
    setTimeout(() => {
        elements.updateBanner.classList.remove('show');
    }, 10000);
}

// ================== Toast 通知 ==================

function showToast(message, icon = '✓') {
    document.getElementById('toastIcon').textContent = icon;
    document.getElementById('toastText').textContent = message;
    elements.toast.classList.add('show');
    
    setTimeout(() => {
        elements.toast.classList.remove('show');
    }, 3000);
}

// ================== 工具函数 ==================

function showLoading(show = true) {
    elements.loadingOverlay.style.display = show ? 'flex' : 'none';
}

function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined) return '--';
    return Number(num).toFixed(decimals);
}

function formatPercent(num) {
    if (num === null || num === undefined) return '--';
    const val = Number(num).toFixed(2);
    return num >= 0 ? `+${val}%` : `${val}%`;
}

function getChangeClass(num) {
    if (num > 0) return 'up';
    if (num < 0) return 'down';
    return 'flat';
}

function autoResizeChatInput() {
    if (!elements.chatInput) return;

    elements.chatInput.style.height = 'auto';
    const nextHeight = Math.min(elements.chatInput.scrollHeight, 180);
    elements.chatInput.style.height = `${Math.max(nextHeight, 58)}px`;
}

function syncChartStageAccent(view = state.currentView) {
    const stage = document.querySelector('.chart-container--main');
    if (!stage) return;

    stage.dataset.view = view;
    stage.dataset.order = state.order;
}

// ================== API 调用 ==================

async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        return null;
    }
}

// ================== 数据加载 ==================

async function loadAllData() {
    showLoading(true);
    const startTime = Date.now();
    
    try {
        const [summary, northTrend, amountTrend] = await Promise.all([
            fetchAPI('/summary'),
            fetchAPI('/north-money-trend?days=30'),
            fetchAPI('/amount-trend?days=30')
        ]);
        
        if (!summary) {
            showLoading(false);
            addMessage('assistant', '⚠️ 无法加载数据，请检查后端服务是否启动。');
            return;
        }
        
        state.summary = summary;
        state.currentDate = summary.trade_date;
        
        // 检查数据一致性
        checkDataConsistency(summary.data_consistency);
        
        // 更新 UI
        updateDateDisplay(summary.trade_date_fmt);
        updateIndices(summary.index_data);
        updateOverviewCards(summary);
        updateHeroBriefing(summary);
        updateMainChart(state.currentView);
        updateNorthChart(northTrend);
        updateAmountChart(amountTrend);
        
        const elapsed = Date.now() - startTime;
        console.log(`✅ 数据加载完成，耗时 ${elapsed}ms`);
    } catch (error) {
        console.error('加载数据失败:', error);
        addMessage('assistant', '⚠️ 加载数据失败，请刷新重试。');
    }
    
    showLoading(false);
}

// ================== 数据一致性检查 ==================

function checkDataConsistency(consistency) {
    if (!consistency) return;
    
    const warningBanner = document.getElementById('consistencyWarning');
    
    if (!consistency.consistent && consistency.warnings && consistency.warnings.length > 0) {
        // 数据不一致，显示警告
        const warningText = consistency.warnings.join('；');
        console.warn('⚠️ 数据日期不一致:', warningText);
        
        if (warningBanner) {
            document.getElementById('consistencyText').textContent = warningText;
            warningBanner.classList.add('show');
        } else {
            // 如果没有警告横幅元素，用 toast 提示
            showToast(`数据日期不一致: ${consistency.warnings[0]}`, '⚠️');
        }
    } else {
        // 数据一致，隐藏警告
        if (warningBanner) {
            warningBanner.classList.remove('show');
        }
    }
}

// ================== UI 更新 ==================

function updateDateDisplay(dateStr) {
    if (!dateStr) return;
    const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
    const date = new Date(dateStr);
    const weekday = weekdays[date.getDay()];
    elements.currentDate.textContent = `📅 ${dateStr} (周${weekday})`;
}

function updateIndices(indices) {
    if (!indices || !indices.length) return;
    
    const indexMap = {
        '000001.SH': 'idx-sh',
        '399001.SZ': 'idx-sz',
        '399006.SZ': 'idx-cyb',
        '000688.SH': 'idx-kc'
    };
    
    indices.forEach(idx => {
        const elemId = indexMap[idx.ts_code];
        if (!elemId) return;
        
        const elem = document.getElementById(elemId);
        if (!elem) return;
        
        const valueEl = elem.querySelector('.index-value');
        const chgEl = elem.querySelector('.index-chg');
        
        valueEl.textContent = formatNumber(idx.close, 2);
        chgEl.textContent = formatPercent(idx.pct_chg);
        chgEl.className = `index-chg ${getChangeClass(idx.pct_chg)}`;
        elem.className = `index-item ${getChangeClass(idx.pct_chg)}`;
    });
}

function updateOverviewCards(summary) {
    const total = summary.total_stocks || 1;
    
    document.getElementById('upCount').textContent = summary.up_count || 0;
    document.getElementById('upRatio').textContent = `${((summary.up_count / total) * 100).toFixed(1)}%`;
    
    document.getElementById('downCount').textContent = summary.down_count || 0;
    document.getElementById('downRatio').textContent = `${((summary.down_count / total) * 100).toFixed(1)}%`;
    
    document.getElementById('totalAmount').textContent = formatNumber(summary.total_amount, 0);
    document.getElementById('limitUp').textContent = summary.limit_up || 0;
    document.getElementById('limitDown').textContent = summary.limit_down || 0;
    
    const northEl = document.getElementById('northMoney');
    if (summary.north_money && summary.north_money.north_total !== undefined) {
        const north = summary.north_money.north_total;
        northEl.textContent = formatNumber(north / 100, 1);
        northEl.className = `card__value ${getChangeClass(north)}`;
    } else {
        northEl.textContent = '--';
    }
}

function updateHeroBriefing(summary) {
    if (!summary) return;

    const total = summary.total_stocks || 0;
    const upCount = summary.up_count || 0;
    const downCount = summary.down_count || 0;
    const breadth = total > 0 ? ((upCount / total) * 100).toFixed(1) : '--';
    const northTotal = summary.north_money?.north_total;
    const leadIndustry = (summary.industry_ranking || [])[0];
    const tone = upCount >= downCount ? '偏强' : '承压';
    const flowText = northTotal == null
        ? '暂无北向数据'
        : `${northTotal >= 0 ? '净流入' : '净流出'} ${(Math.abs(northTotal) / 100).toFixed(1)} 亿`;
    const focusText = leadIndustry
        ? `${leadIndustry.name} ${formatPercent(leadIndustry.pct_chg)}`
        : '等待行业数据';

    const heroBrief = document.getElementById('heroBrief');
    const heroBreadth = document.getElementById('heroBreadth');
    const heroFlow = document.getElementById('heroFlow');
    const heroFocus = document.getElementById('heroFocus');

    if (heroBrief) {
        heroBrief.textContent =
            `${summary.trade_date_fmt} 盘面${tone}，全市场约 ${breadth}% 个股上涨，` +
            `${upCount} 家上涨、${downCount} 家下跌，当前资金面 ${flowText}。`;
    }

    if (heroBreadth) {
        heroBreadth.textContent = total > 0 ? `${breadth}% 上涨` : '--';
    }

    if (heroFlow) {
        heroFlow.textContent = flowText;
        heroFlow.className = `hero-meta-card__value ${northTotal == null ? '' : getChangeClass(northTotal)}`.trim();
    }

    if (heroFocus) {
        heroFocus.textContent = focusText;
        heroFocus.className = `hero-meta-card__value ${leadIndustry ? getChangeClass(leadIndustry.pct_chg) : ''}`.trim();
    }
}

// ================== 图表渲染 ==================

function initChart(containerId) {
    if (!state.charts[containerId]) {
        const container = document.getElementById(containerId);
        if (container) {
            state.charts[containerId] = echarts.init(container, 'dark');
        }
    }
    return state.charts[containerId];
}

function updateMainChart(view) {
    state.currentView = view;
    const chart = initChart('mainChart');
    if (!chart || !state.summary) return;
    
    let option;
    let title = '市场概览';
    switch (view) {
        case 'distribution':
            option = getDistributionOption(state.summary.pct_distribution);
            title = '涨跌分布';
            break;
        case 'industry':
            option = getIndustryTreemapOption(state.summary.industry_ranking);
            title = '行业热力图';
            break;
        case 'ranking':
            option = getRankingTreemapOption(state.order === 'desc' ? state.summary.top_gainers : state.summary.top_losers);
            title = state.order === 'desc' ? '涨幅热力图' : '跌幅热力图';
            break;
        default:
            option = getDistributionOption(state.summary.pct_distribution);
    }
    
    chart.setOption(option, true);
    syncChartStageAccent(view);
    const chartTitle = document.getElementById('mainChartTitle');
    if (chartTitle) {
        chartTitle.textContent = title;
    }
    
    // 绑定点击事件
    chart.off('click');
    if (view === 'ranking') {
        chart.on('click', (params) => {
            // Treemap 点击
            if (params.data && params.data.ts_code) {
                openStockModal(params.data.ts_code);
            }
        });
    }
    // 行业 Treemap 点击
    else if (view === 'industry') {
        chart.on('click', (params) => {
            if (params.data && params.data.industry) {
                openIndustryModal(params.data.industry);
            }
        });
    }
    
    // 更新按钮状态
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });
    
    // 控制控件显示 - Treemap 也需要 TopN 选择器
    const showTopN = ['industry', 'ranking'].includes(view);
    elements.topNSelect.style.display = showTopN ? 'block' : 'none';
    elements.orderToggle.style.display = view === 'ranking' ? 'flex' : 'none';
}

function getDistributionOption(data) {
    if (!data || !data.length) return {};
    
    const xData = data.map(d => `${d.range_start}%~${d.range_end}%`);
    const yData = data.map(d => d.count);
    const colors = data.map(d => {
        if (d.range_start >= 0) return '#ef5350';
        return '#26a69a';
    });
    
    return {
        backgroundColor: 'transparent',
        title: { text: '涨跌幅分布', left: 'center', textStyle: { color: '#e0e0e0', fontSize: 14 } },
        tooltip: { trigger: 'axis', formatter: '{b}: {c}只' },
        grid: { left: 50, right: 20, top: 50, bottom: 40 },
        xAxis: {
            type: 'category',
            data: xData,
            axisLabel: { color: '#999', fontSize: 10, rotate: 45 },
            axisLine: { lineStyle: { color: '#333' } }
        },
        yAxis: {
            type: 'value',
            axisLabel: { color: '#999' },
            splitLine: { lineStyle: { color: '#333' } }
        },
        series: [{
            type: 'bar',
            data: yData.map((val, i) => ({ value: val, itemStyle: { color: colors[i] } })),
            barWidth: '60%'
        }]
    };
}

// 已移除板块视图，改用行业热力图

// 行业热力图 Treemap（方块大小=近5日平均涨幅，颜色=当日涨跌）
function getIndustryTreemapOption(data) {
    if (!data || !data.length) return {};
    
    // 根据 TopN 筛选
    const topData = data.slice(0, state.topN);
    
    // 缓存行业数据
    state.industryData = topData;
    
    // 计算颜色：当日涨跌幅映射到红绿色
    const getColor = (pctChg) => {
        if (pctChg >= 3) return '#c0392b';
        if (pctChg >= 2) return '#e74c3c';
        if (pctChg >= 1) return '#ef5350';
        if (pctChg >= 0.5) return '#ff7675';
        if (pctChg > 0) return '#fab1a0';
        if (pctChg === 0) return '#636e72';
        if (pctChg > -0.5) return '#81ecec';
        if (pctChg > -1) return '#00cec9';
        if (pctChg > -2) return '#26a69a';
        if (pctChg > -3) return '#00b894';
        return '#00695c';
    };
    
    // 构建 Treemap 数据（方块大小用近5日平均涨幅的绝对值+基数）
    const treemapData = topData.map(d => {
        const avg5 = d.avg5_pct_chg || d.pct_chg || 0;
        // 使用绝对值+1确保都有正值作为面积
        const value = Math.abs(avg5) + 1;
        return {
            name: d.name,
            value: value,
            industry: d.name,
            pct_chg: d.pct_chg,
            avg5_pct_chg: avg5,
            up_count: d.up_count || 0,
            down_count: d.down_count || 0,
            stock_count: d.stock_count || 0,
            itemStyle: { color: getColor(d.pct_chg) }
        };
    });
    
    return {
        backgroundColor: 'transparent',
        title: { 
            text: `行业热力图 Top${state.topN}（方块大小=近5日强度，颜色=今日涨跌，点击查看个股）`, 
            left: 'center', 
            textStyle: { color: '#e0e0e0', fontSize: 13 } 
        },
        tooltip: {
            formatter: p => {
                const d = p.data;
                const sign = d.pct_chg >= 0 ? '+' : '';
                const sign5 = d.avg5_pct_chg >= 0 ? '+' : '';
                return `<b style="font-size:14px">${d.name}</b><br/>
                        今日涨跌: <b style="color:${d.pct_chg >= 0 ? '#ef5350' : '#26a69a'}">${sign}${d.pct_chg.toFixed(2)}%</b><br/>
                        近5日均涨: ${sign5}${d.avg5_pct_chg.toFixed(2)}%<br/>
                        <span style="color:#26a69a">↑${d.up_count}</span> / <span style="color:#ef5350">↓${d.down_count}</span> (共${d.stock_count}只)<br/>
                        <span style="color:#58a6ff">点击查看个股 →</span>`;
            }
        },
        series: [{
            type: 'treemap',
            width: '95%',
            height: '85%',
            top: 45,
            roam: false,
            nodeClick: false,  // 禁用默认点击行为，用自定义
            breadcrumb: { show: false },
            label: {
                show: true,
                formatter: p => {
                    const sign = p.data.pct_chg >= 0 ? '+' : '';
                    return `{name|${p.data.name}}\n{pct|${sign}${p.data.pct_chg.toFixed(2)}%}`;
                },
                rich: {
                    name: { fontSize: 12, color: '#fff', fontWeight: 'bold', lineHeight: 18 },
                    pct: { fontSize: 11, color: '#fff', lineHeight: 16 }
                }
            },
            itemStyle: {
                borderColor: '#1a1a2e',
                borderWidth: 2,
                gapWidth: 2
            },
            emphasis: {
                itemStyle: { borderColor: '#58a6ff', borderWidth: 3 }
            },
            data: treemapData
        }]
    };
}

// 股票排行热力图 Treemap
function getRankingTreemapOption(data) {
    if (!data || !data.length) return {};
    
    // 根据 TopN 筛选
    const topData = data.slice(0, state.topN);
    state.rankingData = topData;
    
    const titlePrefix = state.order === 'desc' ? '涨幅' : '跌幅';
    
    // 颜色映射
    const getColor = (pctChg) => {
        if (pctChg >= 9.9) return '#8b0000';  // 涨停深红
        if (pctChg >= 5) return '#c0392b';
        if (pctChg >= 3) return '#e74c3c';
        if (pctChg >= 1) return '#ef5350';
        if (pctChg > 0) return '#ff7675';
        if (pctChg === 0) return '#636e72';
        if (pctChg > -1) return '#81ecec';
        if (pctChg > -3) return '#26a69a';
        if (pctChg > -5) return '#00b894';
        if (pctChg > -9.9) return '#00695c';
        return '#004d40';  // 跌停深绿
    };
    
    // 方块大小用成交额
    const treemapData = topData.map(d => ({
        name: d.name || d.ts_code.split('.')[0],
        value: Math.max(d.amount / 10000, 0.1),  // 成交额(亿)
        ts_code: d.ts_code,
        pct_chg: d.pct_chg,
        close: d.close,
        amount: d.amount,
        itemStyle: { color: getColor(d.pct_chg) }
    }));
    
    return {
        backgroundColor: 'transparent',
        title: { 
            text: `${titlePrefix}排行 Top${state.topN}（方块大小=成交额，颜色=涨跌幅，点击查看K线）`, 
            left: 'center', 
            textStyle: { color: '#e0e0e0', fontSize: 13 } 
        },
        tooltip: {
            formatter: p => {
                const d = p.data;
                const sign = d.pct_chg >= 0 ? '+' : '';
                const amountStr = d.amount >= 10000 ? (d.amount / 10000).toFixed(2) + '亿' : d.amount.toFixed(0) + '万';
                return `<b style="font-size:14px">${d.name}</b> (${d.ts_code})<br/>
                        涨跌幅: <b style="color:${d.pct_chg >= 0 ? '#ef5350' : '#26a69a'}">${sign}${d.pct_chg.toFixed(2)}%</b><br/>
                        收盘价: ¥${d.close.toFixed(2)}<br/>
                        成交额: ${amountStr}<br/>
                        <span style="color:#58a6ff">点击查看K线 →</span>`;
            }
        },
        series: [{
            type: 'treemap',
            width: '95%',
            height: '85%',
            top: 45,
            roam: false,
            nodeClick: false,
            breadcrumb: { show: false },
            label: {
                show: true,
                formatter: p => {
                    const sign = p.data.pct_chg >= 0 ? '+' : '';
                    return `{name|${p.data.name}}\n{pct|${sign}${p.data.pct_chg.toFixed(2)}%}`;
                },
                rich: {
                    name: { fontSize: 11, color: '#fff', fontWeight: 'bold', lineHeight: 16 },
                    pct: { fontSize: 10, color: '#fff', lineHeight: 14 }
                }
            },
            itemStyle: {
                borderColor: '#1a1a2e',
                borderWidth: 2,
                gapWidth: 2
            },
            emphasis: {
                itemStyle: { borderColor: '#58a6ff', borderWidth: 3 }
            },
            data: treemapData
        }]
    };
}

function updateNorthChart(data) {
    const chart = initChart('northChart');
    if (!chart || !data || !data.length) return;
    
    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'axis',
            formatter: params => {
                const p = params[0];
                return `${p.name}<br/>北向资金: ${(p.value / 100).toFixed(2)}亿`;
            }
        },
        grid: { left: 50, right: 20, top: 20, bottom: 30 },
        xAxis: {
            type: 'category',
            data: data.map(d => d.trade_date.slice(5)),
            axisLabel: { color: '#999', fontSize: 10 },
            axisLine: { lineStyle: { color: '#333' } }
        },
        yAxis: {
            type: 'value',
            axisLabel: { color: '#999', formatter: v => (v / 100).toFixed(0) },
            splitLine: { lineStyle: { color: '#333' } }
        },
        series: [{
            type: 'bar',
            data: data.map(d => ({
                value: d.north_total,
                itemStyle: { color: d.north_total >= 0 ? '#ef5350' : '#26a69a' }
            })),
            barWidth: '60%'
        }]
    };
    
    chart.setOption(option, true);
}

function updateAmountChart(data) {
    const chart = initChart('amountChart');
    if (!chart || !data || !data.length) return;
    
    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'axis',
            formatter: params => `${params[0].name}<br/>成交额: ${params[0].value}亿`
        },
        grid: { left: 50, right: 20, top: 20, bottom: 30 },
        xAxis: {
            type: 'category',
            data: data.map(d => d.trade_date.slice(5)),
            axisLabel: { color: '#999', fontSize: 10 },
            axisLine: { lineStyle: { color: '#333' } }
        },
        yAxis: {
            type: 'value',
            axisLabel: { color: '#999' },
            splitLine: { lineStyle: { color: '#333' } }
        },
        series: [{
            type: 'line',
            data: data.map(d => d.total_amount),
            smooth: true,
            symbol: 'none',
            lineStyle: { color: '#5c6bc0', width: 2 },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: 'rgba(92, 107, 192, 0.3)' },
                    { offset: 1, color: 'rgba(92, 107, 192, 0.05)' }
                ])
            }
        }]
    };
    
    chart.setOption(option, true);
}

// ================== 行业详情弹窗（K线图 + 股票列表）==================

async function openIndustryModal(industryName) {
    if (!industryName) return;
    
    state.currentIndustry = industryName;
    state.industryOrder = 'desc';
    state.industryView = 'kline';  // 默认显示K线图
    
    // 显示弹窗
    const modal = document.getElementById('industryModal');
    modal.style.display = 'flex';
    
    // 设置标题
    document.getElementById('industryModalName').textContent = industryName + ' 行业';
    document.getElementById('industryModalStats').innerHTML = '<span style="color:#999">加载中...</span>';
    
    // 重置视图切换按钮
    document.querySelectorAll('#industryViewToggle .toggle-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === 'kline');
    });
    
    // 显示K线视图
    document.getElementById('industryKlineView').style.display = 'block';
    document.getElementById('industryStocksView').style.display = 'none';
    
    // 重置排序按钮
    document.querySelectorAll('#industryOrderToggle .toggle-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.order === 'desc');
    });
    
    // 加载行业详情（K线数据）
    await loadIndustryDetail();
}

async function loadIndustryDetail() {
    // 先显示加载状态
    const chartEl = document.getElementById('industryKlineChart');
    chartEl.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#999">加载中...</div>';
    
    try {
        const url = `/industry-detail/${encodeURIComponent(state.currentIndustry)}?kline_limit=60`;
        console.log('请求行业详情:', url);
        const data = await fetchAPI(url);
        console.log('行业详情响应:', data);
        
        if (!data) {
            document.getElementById('industryModalStats').innerHTML = '<span style="color:#ef5350">加载失败</span>';
            chartEl.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#ef5350">API请求失败</div>';
            return;
        }
        
        // 更新统计信息
        const stats = data.stats || {};
        document.getElementById('industryModalStats').innerHTML = `
            共 <b>${stats.stock_count || 0}</b> 只 |
            <span class="up">↑${stats.up_count || 0}</span> |
            <span class="down">↓${stats.down_count || 0}</span>
        `;
        
        // 更新今日数据卡片
        const today = data.today || {};
        const avgPct = stats.avg_pct_chg || today.pct_chg || 0;
        const pctChg = today.pct_chg || avgPct;
        const pctSign = pctChg >= 0 ? '+' : '';
        const pctClass = pctChg >= 0 ? 'up' : 'down';
        
        document.getElementById('industryTodayPct').innerHTML = `<span class="${pctClass}">${pctSign}${pctChg.toFixed(2)}%</span>`;
        document.getElementById('industryTodayClose').textContent = today.close ? today.close.toFixed(2) : '--';
        document.getElementById('industryTodayAmount').textContent = today.amount ? today.amount.toFixed(2) + '亿' : (stats.total_amount ? stats.total_amount.toFixed(2) + '亿' : '--');
        document.getElementById('industryTodayPE').textContent = today.pe ? today.pe.toFixed(1) : '--';
        document.getElementById('industryUpDown').innerHTML = `<span class="up">${stats.up_count || 0}</span>/<span class="down">${stats.down_count || 0}</span>`;
        
        // 渲染K线图
        if (data.kline && data.kline.length > 0) {
            setTimeout(() => {
                renderIndustryKline(data.kline, data.index_name || state.currentIndustry);
            }, 50);  // 稍等DOM更新
        } else {
            // 没有K线数据时显示提示
            chartEl.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#999;flex-direction:column"><div>暂无行业指数K线数据</div><div style="font-size:12px;margin-top:8px">可点击下方按钮查看成分股</div></div>';
        }
        
    } catch (err) {
        console.error('加载行业详情失败:', err);
        document.getElementById('industryModalStats').innerHTML = '<span style="color:#ef5350">加载失败</span>';
        chartEl.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#ef5350">${err.message || '加载失败'}</div>`;
    }
}

function renderIndustryKline(klineData, title) {
    const chartEl = document.getElementById('industryKlineChart');
    if (!chartEl) {
        console.error('找不到 industryKlineChart 元素');
        return;
    }
    
    console.log('渲染行业K线图:', title, 'K线数据条数:', klineData.length);
    
    chartEl.innerHTML = '';  // 清空内容
    
    // 确保容器有尺寸
    if (chartEl.offsetWidth === 0 || chartEl.offsetHeight === 0) {
        console.warn('K线图容器尺寸为0，延迟渲染');
        setTimeout(() => renderIndustryKline(klineData, title), 100);
        return;
    }
    
    const chart = echarts.init(chartEl);
    
    const dates = klineData.map(d => d.date);
    const ohlc = klineData.map(d => [d.open, d.close, d.low, d.high]);
    const volumes = klineData.map(d => d.vol);
    
    const option = {
        backgroundColor: 'transparent',
        title: {
            text: title + ' 指数走势',
            left: 'center',
            textStyle: { color: '#e0e0e0', fontSize: 13 }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross' },
            formatter: params => {
                const idx = params[0].dataIndex;
                const d = klineData[idx];
                const sign = d.pct_chg >= 0 ? '+' : '';
                return `<b>${d.date}</b><br/>
                        开: ${d.open.toFixed(2)}<br/>
                        高: ${d.high.toFixed(2)}<br/>
                        低: ${d.low.toFixed(2)}<br/>
                        收: ${d.close.toFixed(2)}<br/>
                        涨跌: <span style="color:${d.pct_chg >= 0 ? '#ef5350' : '#26a69a'}">${sign}${d.pct_chg.toFixed(2)}%</span>`;
            }
        },
        grid: [
            { left: 60, right: 30, top: 45, height: '55%' },
            { left: 60, right: 30, top: '72%', height: '18%' }
        ],
        xAxis: [
            { type: 'category', data: dates, axisLabel: { color: '#999', fontSize: 10 }, gridIndex: 0 },
            { type: 'category', data: dates, axisLabel: { show: false }, gridIndex: 1 }
        ],
        yAxis: [
            { type: 'value', scale: true, axisLabel: { color: '#999' }, splitLine: { lineStyle: { color: '#333' } }, gridIndex: 0 },
            { type: 'value', scale: true, axisLabel: { color: '#999', fontSize: 10 }, splitLine: { show: false }, gridIndex: 1 }
        ],
        series: [
            {
                name: 'K线',
                type: 'candlestick',
                data: ohlc,
                xAxisIndex: 0,
                yAxisIndex: 0,
                itemStyle: {
                    color: '#ef5350',
                    color0: '#26a69a',
                    borderColor: '#ef5350',
                    borderColor0: '#26a69a'
                }
            },
            {
                name: '成交量',
                type: 'bar',
                data: volumes.map((v, i) => ({
                    value: v,
                    itemStyle: { color: klineData[i].close >= klineData[i].open ? '#ef5350' : '#26a69a', opacity: 0.5 }
                })),
                xAxisIndex: 1,
                yAxisIndex: 1
            }
        ]
    };
    
    chart.setOption(option);
    
    // 保存图表实例以便 resize
    state.industryKlineChart = chart;
}

async function loadIndustryStocks() {
    const tbody = document.getElementById('industryStockBody');
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:20px;color:#999">加载中...</td></tr>';
    
    try {
        const url = `/industry-stocks/${encodeURIComponent(state.currentIndustry)}?order=${state.industryOrder}&limit=200`;
        const data = await fetchAPI(url);
        
        if (!data || !data.stocks) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:20px;color:#999">暂无数据</td></tr>';
            return;
        }
        
        // 更新统计信息
        const statsEl = document.getElementById('industryModalStats');
        statsEl.innerHTML = `
            共 <b>${data.total}</b> 只股票 |
            <span class="up">↑上涨 ${data.up_count}</span> |
            <span class="down">↓下跌 ${data.down_count}</span> |
            平盘 ${data.flat_count}
        `;
        
        // 渲染表格
        renderIndustryStockTable(data.stocks);
        
    } catch (err) {
        console.error('加载行业股票失败:', err);
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:20px;color:#ef5350">加载失败</td></tr>';
    }
}

function renderIndustryStockTable(stocks) {
    const tbody = document.getElementById('industryStockBody');
    
    if (!stocks || !stocks.length) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:20px;color:#999">暂无数据</td></tr>';
        return;
    }
    
    tbody.innerHTML = stocks.map((stock, index) => {
        const pctClass = stock.pct_chg > 0 ? 'pct-up' : (stock.pct_chg < 0 ? 'pct-down' : 'pct-flat');
        const pctSign = stock.pct_chg > 0 ? '+' : '';
        const amountStr = stock.amount >= 1000 ? (stock.amount / 10000).toFixed(2) + '亿' : stock.amount.toFixed(2) + '万';
        const mvStr = stock.total_mv ? (stock.total_mv >= 10000 ? (stock.total_mv / 10000).toFixed(0) + '万亿' : stock.total_mv.toFixed(0) + '亿') : '--';
        const turnoverStr = stock.turnover_rate != null ? stock.turnover_rate.toFixed(2) + '%' : '--';
        const peStr = stock.pe != null ? stock.pe.toFixed(1) : '--';
        
        return `
            <tr data-ts="${stock.ts_code}">
                <td class="col-rank">${index + 1}</td>
                <td class="col-code">${stock.ts_code.split('.')[0]}</td>
                <td class="col-name" title="${stock.name}">${stock.name}</td>
                <td class="col-pct ${pctClass}">${pctSign}${stock.pct_chg.toFixed(2)}%</td>
                <td class="col-close">${stock.close.toFixed(2)}</td>
                <td class="col-amount">${amountStr}</td>
                <td class="col-turnover">${turnoverStr}</td>
                <td class="col-pe">${peStr}</td>
                <td class="col-mv">${mvStr}</td>
            </tr>
        `;
    }).join('');
}

function closeIndustryModal() {
    document.getElementById('industryModal').style.display = 'none';
    state.currentIndustry = null;
}


// ================== 股票详情弹窗 ==================

async function openStockModal(tsCode) {
    showLoading(true);
    
    try {
        const data = await fetchAPI(`/stock/${tsCode}`);
        if (!data) {
            showToast('无法加载股票数据', '⚠️');
            showLoading(false);
            return;
        }
        
        // 填充数据
        const daily = data.daily || {};
        const basic = data.basic || {};
        const company = data.company || {};
        
        document.getElementById('modalStockName').textContent = daily.name || company.name || '--';
        document.getElementById('modalStockCode').textContent = tsCode;
        
        const pctChgEl = document.getElementById('modalPctChg');
        pctChgEl.textContent = formatPercent(daily.pct_chg);
        pctChgEl.className = `info-value ${getChangeClass(daily.pct_chg)}`;
        
        // 今日数据
        document.getElementById('modalOpen').textContent = formatNumber(daily.open, 2);
        document.getElementById('modalHigh').textContent = formatNumber(daily.high, 2);
        document.getElementById('modalLow').textContent = formatNumber(daily.low, 2);
        document.getElementById('modalClose2').textContent = formatNumber(daily.close, 2);
        document.getElementById('modalVol').textContent = `${formatNumber(daily.vol / 10000, 2)}万手`;
        document.getElementById('modalAmount').textContent = `${formatNumber(daily.amount / 10000, 2)}亿`;
        document.getElementById('modalTurnover').textContent = `${formatNumber(basic.turnover_rate, 2)}%`;
        document.getElementById('modalVolRatio').textContent = formatNumber(basic.volume_ratio, 2);
        
        // 公司信息
        document.getElementById('modalIndustry').textContent = company.industry || '--';
        document.getElementById('modalArea').textContent = company.area || '--';
        document.getElementById('modalMarket').textContent = company.market || '--';
        document.getElementById('modalListDate').textContent = company.list_date || '--';
        
        // 估值指标
        document.getElementById('modalPE').textContent = basic.pe ? formatNumber(basic.pe, 2) : '--';
        document.getElementById('modalPETTM').textContent = basic.pe_ttm ? formatNumber(basic.pe_ttm, 2) : '--';
        document.getElementById('modalPB').textContent = basic.pb ? formatNumber(basic.pb, 2) : '--';
        document.getElementById('modalTotalMV').textContent = basic.total_mv ? `${formatNumber(basic.total_mv, 0)}亿` : '--';
        document.getElementById('modalCircMV').textContent = basic.circ_mv ? `${formatNumber(basic.circ_mv, 0)}亿` : '--';
        
        // 显示弹窗（先显示再渲染图表，确保容器尺寸正确）
        elements.stockModal.classList.add('show');
        
        // 短暂延迟后渲染 K 线图（确保容器已显示）
        setTimeout(() => {
            renderModalKline(data.kline);
        }, 50);
        
    } catch (error) {
        console.error('加载股票详情失败:', error);
        showToast('加载失败', '⚠️');
    }
    
    showLoading(false);
}

function renderModalKline(klineData) {
    if (!klineData || !klineData.length) return;
    
    const container = document.getElementById('modalKlineChart');
    let chart = echarts.getInstanceByDom(container);
    if (!chart) {
        chart = echarts.init(container, 'dark');
    }
    
    const dates = klineData.map(d => d.date);
    const values = klineData.map(d => [d.open, d.close, d.low, d.high]);
    const volumes = klineData.map(d => d.vol);
    
    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross' },
            formatter: params => {
                const d = klineData[params[0].dataIndex];
                return `<b>${d.date}</b><br/>
                        开: ${d.open} 高: ${d.high}<br/>
                        低: ${d.low} 收: ${d.close}<br/>
                        涨跌: ${formatPercent(d.pct_chg)}<br/>
                        成交量: ${formatNumber(d.vol / 10000, 2)}万手`;
            }
        },
        grid: [
            { left: 50, right: 20, top: 20, height: '60%' },
            { left: 50, right: 20, top: '75%', height: '15%' }
        ],
        xAxis: [
            {
                type: 'category',
                data: dates,
                axisLabel: { show: false },
                axisLine: { lineStyle: { color: '#333' } },
                gridIndex: 0
            },
            {
                type: 'category',
                data: dates,
                axisLabel: { color: '#999', fontSize: 9 },
                axisLine: { lineStyle: { color: '#333' } },
                gridIndex: 1
            }
        ],
        yAxis: [
            {
                type: 'value',
                scale: true,
                axisLabel: { color: '#999', fontSize: 9 },
                splitLine: { lineStyle: { color: '#333' } },
                gridIndex: 0
            },
            {
                type: 'value',
                scale: true,
                axisLabel: { show: false },
                splitLine: { show: false },
                gridIndex: 1
            }
        ],
        series: [
            {
                type: 'candlestick',
                data: values,
                xAxisIndex: 0,
                yAxisIndex: 0,
                itemStyle: {
                    color: '#ef5350',
                    color0: '#26a69a',
                    borderColor: '#ef5350',
                    borderColor0: '#26a69a'
                }
            },
            {
                type: 'bar',
                data: volumes.map((v, i) => ({
                    value: v,
                    itemStyle: {
                        color: klineData[i].pct_chg >= 0 ? 'rgba(239,83,80,0.5)' : 'rgba(38,166,154,0.5)'
                    }
                })),
                xAxisIndex: 1,
                yAxisIndex: 1
            }
        ]
    };
    
    chart.setOption(option, true);
}

function closeStockModal() {
    elements.stockModal.classList.remove('show');
}

// ================== Chat 功能 ==================

function addMessage(role, content) {
    const messagesContainer = elements.chatMessages;
    const msgDiv = document.createElement('div');
    msgDiv.className = `message message--${role} message--enter`;
    
    if (role === 'assistant') {
        msgDiv.innerHTML = `
            <div class="message__avatar">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                </svg>
            </div>
            <div class="message__content"><div class="message__text">${content}</div></div>
        `;
    } else {
        msgDiv.innerHTML = `
            <div class="message__content"><div class="message__text">${content}</div></div>
        `;
    }
    
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    requestAnimationFrame(() => {
        msgDiv.classList.remove('message--enter');
    });
}

async function handleChatCommand(command) {
    addMessage('user', command);
    
    const cmd = command.toLowerCase();
    let response = '';
    
    if (!state.summary) {
        addMessage('assistant', '⚠️ 数据未加载，请稍候...');
        return;
    }
    
    const s = state.summary;
    
    if (cmd.includes('市场') || cmd.includes('概览') || cmd.includes('怎么样')) {
        const total = s.total_stocks || 0;
        response = `📊 <b>${s.trade_date_fmt} 市场概览</b><br><br>
            上涨: <span class="up">${s.up_count}</span> 家 (${((s.up_count/total)*100).toFixed(1)}%)<br>
            下跌: <span class="down">${s.down_count}</span> 家 (${((s.down_count/total)*100).toFixed(1)}%)<br>
            涨停: ${s.limit_up} 家，跌停: ${s.limit_down} 家<br>
            成交额: <b>${formatNumber(s.total_amount, 0)}</b> 亿元<br>
            平均涨跌幅: ${formatPercent(s.avg_pct_chg)}`;
    }
    else if (cmd.includes('北向') || cmd.includes('资金')) {
        if (s.north_money) {
            const nm = s.north_money;
            response = `💰 <b>${s.trade_date_fmt} 北向资金</b><br><br>
                沪股通: <span class="${getChangeClass(nm.hgt)}">${formatNumber(nm.hgt/100, 2)}</span> 亿<br>
                深股通: <span class="${getChangeClass(nm.sgt)}">${formatNumber(nm.sgt/100, 2)}</span> 亿<br>
                <b>北向合计: <span class="${getChangeClass(nm.north_total)}">${formatNumber(nm.north_total/100, 2)}</span> 亿</b>`;
        } else {
            response = '⚠️ 暂无北向资金数据';
        }
    }
    else if (cmd.includes('涨幅') || (cmd.includes('涨') && cmd.includes('榜'))) {
        const top10 = (s.top_gainers || []).slice(0, 10);
        response = `📈 <b>${s.trade_date_fmt} 涨幅前10</b><br><br>`;
        top10.forEach((item, i) => {
            response += `${i+1}. <span class="cmd-link" data-ts="${item.ts_code}">${item.name}</span> <span class="up">+${item.pct_chg.toFixed(2)}%</span><br>`;
        });
        state.order = 'desc';
        updateMainChart('ranking');
    }
    else if (cmd.includes('跌幅') || (cmd.includes('跌') && cmd.includes('榜'))) {
        const top10 = (s.top_losers || []).slice(0, 10);
        response = `📉 <b>${s.trade_date_fmt} 跌幅前10</b><br><br>`;
        top10.forEach((item, i) => {
            response += `${i+1}. <span class="cmd-link" data-ts="${item.ts_code}">${item.name}</span> <span class="down">${item.pct_chg.toFixed(2)}%</span><br>`;
        });
        state.order = 'asc';
        updateMainChart('ranking');
    }
    else if (cmd.includes('行业') || cmd.includes('板块')) {
        const industries = (s.industry_ranking || []).slice(0, 10);
        if (industries.length > 0) {
            response = `🏭 <b>${s.trade_date_fmt} 行业涨幅排名</b><br><br>`;
            industries.forEach((item, i) => {
                const cls = getChangeClass(item.pct_chg);
                response += `${i+1}. ${item.name} <span class="${cls}">${formatPercent(item.pct_chg)}</span><br>`;
            });
            updateMainChart('industry');
        } else {
            response = '⚠️ 暂无行业数据';
        }
    }
    else if (cmd.includes('龙虎')) {
        if (s.top_list_summary && s.top_list_summary.count > 0) {
            const tl = s.top_list_summary;
            response = `🐉 <b>${s.trade_date_fmt} 龙虎榜汇总</b><br><br>
                上榜股票: <b>${tl.count}</b> 只<br>
                机构买入: ${formatNumber(tl.total_buy, 2)} 亿<br>
                机构卖出: ${formatNumber(tl.total_sell, 2)} 亿<br>
                净买入: <span class="${getChangeClass(tl.total_net)}">${formatNumber(tl.total_net, 2)}</span> 亿`;
        } else {
            response = '⚠️ 暂无龙虎榜数据';
        }
    }
    else if (cmd.includes('涨停') || cmd.includes('跌停')) {
        response = `🔥 <b>${s.trade_date_fmt} 涨跌停统计</b><br><br>
            涨停: <span class="up">${s.limit_up}</span> 家<br>
            跌停: <span class="down">${s.limit_down}</span> 家`;
        if (s.limit_stats) {
            response += `<br>炸板: ${s.limit_stats.zha_ban || 0} 家`;
        }
    }
    else {
        response = `🤔 抱歉，我不太理解你的问题。你可以试试：<br>
            • 市场概览<br>
            • 北向资金<br>
            • 涨幅榜/跌幅榜<br>
            • 行业排名<br>
            • 龙虎榜`;
    }
    
    addMessage('assistant', response);
}

// ================== 事件绑定 ==================

function bindEvents() {
    // 刷新按钮
    elements.refreshBtn.addEventListener('click', () => loadAllData());
    
    // 图表切换
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.addEventListener('click', () => updateMainChart(btn.dataset.view));
    });
    
    // Top N 选择器
    elements.topNSelect.addEventListener('change', (e) => {
        state.topN = parseInt(e.target.value);
        updateMainChart(state.currentView);
    });
    
    // 涨跌榜切换
    document.querySelectorAll('#orderToggle .toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#orderToggle .toggle-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.order = btn.dataset.order;
            updateMainChart(state.currentView);
        });
    });
    
    // 快捷命令
    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', () => handleChatCommand(btn.dataset.cmd));
    });
    
    // 聊天消息中的命令链接和股票链接
    elements.chatMessages.addEventListener('click', e => {
        if (e.target.classList.contains('cmd-link')) {
            if (e.target.dataset.ts) {
                openStockModal(e.target.dataset.ts);
            } else if (e.target.dataset.cmd) {
                handleChatCommand(e.target.dataset.cmd);
            }
        }
    });
    
    // 发送按钮
    elements.chatSend.addEventListener('click', () => {
        const msg = elements.chatInput.value.trim();
        if (msg) {
            handleChatCommand(msg);
            elements.chatInput.value = '';
            autoResizeChatInput();
        }
    });
    
    // Enter 发送
    elements.chatInput.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            elements.chatSend.click();
        }
    });

    elements.chatInput.addEventListener('input', () => {
        autoResizeChatInput();
    });
    
    // 窗口大小变化时重绘图表
    window.addEventListener('resize', () => {
        Object.values(state.charts).forEach(chart => chart && chart.resize());
        
        // 重绘弹窗内的图表
        const modalChart = document.getElementById('modalKlineChart');
        if (modalChart) {
            const chart = echarts.getInstanceByDom(modalChart);
            if (chart) chart.resize();
        }
        
        // 重绘行业K线图
        if (state.industryKlineChart) {
            state.industryKlineChart.resize();
        }
    });
    
    // 股票弹窗关闭
    document.getElementById('modalClose').addEventListener('click', closeStockModal);
    elements.stockModal.addEventListener('click', (e) => {
        if (e.target === elements.stockModal) {
            closeStockModal();
        }
    });
    
    // 行业弹窗关闭
    document.getElementById('industryModalClose').addEventListener('click', closeIndustryModal);
    document.getElementById('industryModal').addEventListener('click', (e) => {
        if (e.target.id === 'industryModal') {
            closeIndustryModal();
        }
    });
    
    // 行业弹窗视图切换（K线图 / 股票列表）
    document.querySelectorAll('#industryViewToggle .toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#industryViewToggle .toggle-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const view = btn.dataset.view;
            state.industryView = view;
            
            document.getElementById('industryKlineView').style.display = view === 'kline' ? 'block' : 'none';
            document.getElementById('industryStocksView').style.display = view === 'stocks' ? 'block' : 'none';
            
            // 切换到股票列表时加载数据
            if (view === 'stocks') {
                loadIndustryStocks();
            }
            // 切换回K线时 resize 图表
            if (view === 'kline' && state.industryKlineChart) {
                setTimeout(() => state.industryKlineChart.resize(), 50);
            }
        });
    });
    
    // "查看成分股列表" 按钮
    document.getElementById('btnViewStocks').addEventListener('click', () => {
        // 切换到股票列表视图
        document.querySelectorAll('#industryViewToggle .toggle-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.view === 'stocks');
        });
        state.industryView = 'stocks';
        document.getElementById('industryKlineView').style.display = 'none';
        document.getElementById('industryStocksView').style.display = 'block';
        loadIndustryStocks();
    });
    
    // 行业弹窗排序切换
    document.querySelectorAll('#industryOrderToggle .toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#industryOrderToggle .toggle-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.industryOrder = btn.dataset.order;
            loadIndustryStocks();
        });
    });
    
    // 行业股票表格点击
    document.getElementById('industryStockBody').addEventListener('click', (e) => {
        const row = e.target.closest('tr');
        if (row && row.dataset.ts) {
            closeIndustryModal();
            openStockModal(row.dataset.ts);
        }
    });
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeStockModal();
            closeIndustryModal();
        }
    });
    
    // 更新横幅
    document.getElementById('refreshNowBtn').addEventListener('click', () => {
        elements.updateBanner.classList.remove('show');
        loadAllData();
        showToast('数据已刷新', '✓');
    });
    
    document.getElementById('dismissBannerBtn').addEventListener('click', () => {
        elements.updateBanner.classList.remove('show');
    });
    
    // 关闭数据一致性警告
    const dismissConsistencyBtn = document.getElementById('dismissConsistencyBtn');
    if (dismissConsistencyBtn) {
        dismissConsistencyBtn.addEventListener('click', () => {
            document.getElementById('consistencyWarning').classList.remove('show');
        });
    }
}

// ================== 初始化 ==================

document.addEventListener('DOMContentLoaded', () => {
    bindEvents();
    autoResizeChatInput();
    loadAllData();
    connectWebSocket();
    
    // 定期发送心跳
    setInterval(() => {
        if (state.ws && state.ws.readyState === WebSocket.OPEN) {
            state.ws.send(JSON.stringify({ type: 'ping' }));
        }
    }, 30000);
});
