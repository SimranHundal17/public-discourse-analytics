const charts = {};
const palette = ["#2563EB", "#0F766E", "#64748B", "#D97706", "#2563EB", "#0F766E", "#64748B"];
const donutPalette = ["#2563EB", "#0F766E", "#64748B", "#D97706", "#15803D", "#2563EB", "#0F766E", "#94A3B8", "#B45309", "#475569", "#2563EB", "#0F766E", "#64748B", "#D97706", "#15803D"];
const colors = {
    grid: "rgba(15,23,42,0.08)",
    ticks: "#0F172A",
    text: "#0F172A",
    muted: "#475569",
    blue: "#2563EB",
    deepBlue: "#2563EB",
    sky: "#2563EB",
    teal: "#0F766E",
    softTeal: "#0F766E",
    orange: "#EA580C",
    amber: "#D97706",
    green: "#0F766E",
    slate: "#64748B",
};

const api = {
    countries: "/api/countries",
    publicKpis: "/api/public/kpis",
    publicTopic: "/api/public/discourse-by-topic",
    publicShare: "/api/public/share-by-topic",
    redditMonthlyTrend: "/api/public/monthly-reddit-trend",
    institutionalKpis: "/api/institutional/kpis",
    governmentTopic: "/api/institutional/government-expenditure-by-topic",
    institutionTopic: "/api/institutional/metrics-by-topic",
    topGovernmentCountries: "/api/institutional/top-expenditure-countries",
    topInstitutionCountries: "/api/institutional/top-metric-countries",
    countryExpenditure: "/api/country-expenditure",
    countryInstitutional: "/api/country-institutional",
    shareComparison: "/api/alignment/share-comparison",
    priorityGap: "/api/alignment/priority-gap",
    insights: "/api/alignment/insights",
};

let selectedCountry = "Germany";
let defaultCountry = "Germany";
let countryNames = [];

Chart.defaults.color = colors.muted;
Chart.defaults.borderColor = colors.grid;
Chart.defaults.font.family = "Inter, system-ui, sans-serif";

function numberFormat(value, digits = 2) {
    return new Intl.NumberFormat("en-US", { maximumFractionDigits: digits }).format(Number(value || 0));
}

function percentFormat(value) {
    return `${numberFormat(value, 2)}%`;
}

function showError(message) {
    const banner = document.getElementById("dashboardError");
    banner.textContent = message;
    banner.classList.remove("hidden");
}

function clearError() {
    const banner = document.getElementById("dashboardError");
    banner.textContent = "";
    banner.classList.add("hidden");
}

function setLoading(isLoading) {
    document.querySelector(".content").classList.toggle("loading", isLoading);
}

async function fetchJson(url) {
    const response = await fetch(url);
    const payload = await response.json();
    if (!payload.success) {
        throw new Error(payload.error || `Request failed: ${url}`);
    }
    return payload.data || [];
}

function withCountry(url) {
    return `${url}?country=${encodeURIComponent(selectedCountry)}`;
}

function renderKpis(containerId, items) {
    const container = document.getElementById(containerId);
    container.innerHTML = items.map((item) => `
        <article class="kpi-card">
            <p class="kpi-label">${item.label}</p>
            <p class="kpi-value">${numberFormat(item.value, 0)}</p>
        </article>
    `).join("");
}

function toggleEmptyState(chartId, emptyId, rows, message) {
    const chartWrap = document.getElementById(chartId).closest(".chart-wrap");
    const empty = document.getElementById(emptyId);
    if (!rows.length) {
        destroyChart(chartId);
        empty.textContent = message;
        empty.classList.remove("hidden");
        chartWrap.classList.add("hidden");
        return true;
    }
    empty.classList.add("hidden");
    chartWrap.classList.remove("hidden");
    return false;
}

function destroyChart(id) {
    if (charts[id]) {
        charts[id].destroy();
        delete charts[id];
    }
}

function renderChart(id, config) {
    destroyChart(id);
    const ctx = document.getElementById(id);
    charts[id] = new Chart(ctx, {
        ...config,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: "index" },
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { boxWidth: 10, color: colors.muted, usePointStyle: true, padding: 18 },
                },
                tooltip: {
                    backgroundColor: "#0F172A",
                    borderColor: "rgba(15, 23, 42, 0.12)",
                    borderWidth: 1,
                    titleColor: "#F8FAFC",
                    bodyColor: "#F8FAFC",
                    padding: 12,
                    callbacks: {
                        label(context) {
                            const label = context.dataset.label || context.label || "";
                            const parsed = context.parsed || {};
                            const value = parsed.y ?? parsed.x ?? context.raw;
                            const suffix = context.dataset.percent ? "%" : "";
                            return `${label}: ${numberFormat(value)}${suffix}`;
                        },
                    },
                },
            },
            scales: config.type === "doughnut" ? undefined : {
                x: { beginAtZero: true, ticks: { color: colors.ticks }, grid: { color: colors.grid } },
                y: { beginAtZero: true, ticks: { color: colors.ticks }, grid: { display: false } },
            },
            ...config.options,
        },
    });
}

function hexToRgba(hex, alpha) {
    const clean = hex.replace("#", "");
    const value = parseInt(clean, 16);
    const red = (value >> 16) & 255;
    const green = (value >> 8) & 255;
    const blue = value & 255;
    return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

function makeBarGradient(color) {
    return (context) => {
        const chart = context.chart;
        const { chartArea, ctx } = chart;
        if (!chartArea) {
            return color;
        }
        const gradient = ctx.createLinearGradient(chartArea.left, 0, chartArea.right, 0);
        gradient.addColorStop(0, hexToRgba(color, 0.82));
        gradient.addColorStop(1, color);
        return gradient;
    };
}

function horizontalBar(id, labels, data, label, color) {
    renderChart(id, {
        type: "bar",
        data: { labels, datasets: [{ label, data, backgroundColor: makeBarGradient(color), borderRadius: 8, borderSkipped: false }] },
        options: {
            indexAxis: "y",
            scales: {
                x: { beginAtZero: true, ticks: { color: colors.ticks }, grid: { color: colors.grid } },
                y: { ticks: { color: colors.ticks }, grid: { display: false } },
            },
        },
    });
}

async function loadCountries() {
    const rows = await fetchJson(api.countries);
    countryNames = rows.map((row) => row.country_name);
    const select = document.getElementById("countrySelect");
    select.innerHTML = countryNames.map((country) => `<option value="${country}">${country}</option>`).join("");
    selectedCountry = await pickDefaultCountry();
    defaultCountry = selectedCountry;
    select.value = selectedCountry;
    window.dashboardCountries = countryNames;
}

async function pickDefaultCountry() {
    const preferredCountries = ["Germany", "France", "Sweden", "Norway", "United States"];
    const candidates = preferredCountries.filter((country) => countryNames.includes(country));
    for (const country of candidates) {
        const [expenditureRows, institutionalRows] = await Promise.all([
            fetchJson(`${api.countryExpenditure}?country=${encodeURIComponent(country)}`),
            fetchJson(`${api.countryInstitutional}?country=${encodeURIComponent(country)}`),
        ]);
        if (expenditureRows.length && institutionalRows.length) {
            return country;
        }
    }
    return candidates[0] || countryNames[0] || "Germany";
}

async function loadPublicDiscourse() {
    const [kpis, topicRows, shareRows, trendRows] = await Promise.all([
        fetchJson(api.publicKpis),
        fetchJson(api.publicTopic),
        fetchJson(api.publicShare),
        fetchJson(api.redditMonthlyTrend),
    ]);

    renderKpis("publicKpis", [
        { label: "Total Reddit Posts", value: kpis.total_reddit_posts },
        { label: "Total News Articles", value: kpis.total_news_articles },
        { label: "Total Public Discourse Records", value: kpis.total_public_discourse_records },
        { label: "Total Topics", value: kpis.total_topics },
    ]);

    horizontalBar(
        "publicTopicBarChart",
        topicRows.map((row) => row.topic_name),
        topicRows.map((row) => row.total_records),
        "Public discourse records",
        colors.blue
    );

    renderChart("publicShareChart", {
        type: "doughnut",
        data: {
            labels: shareRows.map((row) => row.topic_name),
            datasets: [{
                label: "Share",
                data: shareRows.map((row) => row.share),
                backgroundColor: shareRows.map((_, index) => donutPalette[index % donutPalette.length]),
                borderColor: "#FFFFFF",
                borderWidth: 1,
                hoverBorderColor: "#FFFFFF",
                hoverBorderWidth: 2,
            }],
        },
        options: {
            cutout: "62%",
            plugins: {
                tooltip: {
                    callbacks: {
                        label(context) {
                            return `${context.label}: ${percentFormat(context.raw)}`;
                        },
                    },
                },
            },
        },
    });

    renderMonthlyTrend(trendRows);
}

function renderMonthlyTrend(rows) {
    const months = [...new Set(rows.map((row) => row.month_label))].sort();
    const topicTotals = rows.reduce((totals, row) => {
        totals[row.topic_name] = (totals[row.topic_name] || 0) + Number(row.reddit_posts || 0);
        return totals;
    }, {});
    const topics = Object.entries(topicTotals)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 7)
        .map(([topic]) => topic);
    const datasets = topics.map((topic, index) => ({
        label: topic,
        data: months.map((month) => {
            const match = rows.find((row) => row.topic_name === topic && row.month_label === month);
            return match ? match.reddit_posts : 0;
        }),
        borderColor: palette[index % palette.length],
        backgroundColor: palette[index % palette.length],
        borderWidth: 2.4,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.38,
    }));

    renderChart("redditMonthlyTrendChart", {
        type: "line",
        data: { labels: months, datasets },
        options: {
            scales: {
                x: { ticks: { color: colors.ticks, maxRotation: 45, minRotation: 0 }, grid: { display: false } },
                y: { beginAtZero: true, ticks: { color: colors.ticks }, grid: { color: colors.grid } },
            },
        },
    });
}

async function loadInstitutional() {
    const [kpis, govTopic, instTopic, topGov, topInst] = await Promise.all([
        fetchJson(api.institutionalKpis),
        fetchJson(api.governmentTopic),
        fetchJson(api.institutionTopic),
        fetchJson(api.topGovernmentCountries),
        fetchJson(api.topInstitutionCountries),
    ]);

    renderKpis("institutionalKpis", [
        { label: "Total Countries", value: kpis.total_countries },
        { label: "Total Years", value: kpis.total_years },
        { label: "Government Expenditure Records", value: kpis.expenditure_records },
        { label: "Institutional Records", value: kpis.institutional_records },
    ]);

    horizontalBar("governmentTopicChart", govTopic.map((row) => row.topic_name), govTopic.map((row) => row.avg_expenditure), "Total expenditure", colors.teal);
    horizontalBar("institutionTopicChart", instTopic.map((row) => row.topic_name), instTopic.map((row) => row.avg_institutional_value), "Avg. institutional value", colors.deepBlue);
    horizontalBar("topGovernmentCountriesChart", topGov.map((row) => row.country_name), topGov.map((row) => row.total_expenditure), "Total expenditure", colors.teal);
    horizontalBar("topInstitutionCountriesChart", topInst.map((row) => row.country_name), topInst.map((row) => row.avg_institutional_value), "Avg. institutional value", colors.deepBlue);
    await loadCountryDetails();
}

async function loadCountryDetails() {
    document.getElementById("selectedCountryLabel").textContent = `Selected country: ${selectedCountry}`;
    document.getElementById("countrySelect").value = selectedCountry;

    const [expenditureRows, institutionalRows] = await Promise.all([
        fetchJson(withCountry(api.countryExpenditure)),
        fetchJson(withCountry(api.countryInstitutional)),
    ]);

    if (!toggleEmptyState("countryExpenditureChart", "countryExpenditureEmpty", expenditureRows, "No government expenditure data available for this country.")) {
        horizontalBar(
            "countryExpenditureChart",
            expenditureRows.map((row) => row.topic_name),
            expenditureRows.map((row) => row.total_expenditure),
            "Total expenditure",
            colors.teal
        );
    }

    if (!toggleEmptyState("countryInstitutionChart", "countryInstitutionEmpty", institutionalRows, "No institutional metrics available for this country.")) {
        horizontalBar(
            "countryInstitutionChart",
            institutionalRows.map((row) => row.topic_name),
            institutionalRows.map((row) => row.avg_institutional_value),
            "Avg. institutional value",
            colors.deepBlue
        );
    }
}

async function selectCountry(country) {
    if (!country || !countryNames.includes(country)) {
        return;
    }
    selectedCountry = country;
    clearError();
    try {
        await loadCountryDetails();
        if (window.highlightMapCountry) {
            window.highlightMapCountry(country);
        }
    } catch (error) {
        showError(error.message);
    }
}

async function loadAlignment() {
    const [shareRows, gapRows, insights] = await Promise.all([
        fetchJson(api.shareComparison),
        fetchJson(api.priorityGap),
        fetchJson(api.insights),
    ]);

    renderInsights(insights, shareRows);

    renderChart("shareComparisonChart", {
        type: "bar",
        data: {
            labels: shareRows.map((row) => row.topic_name),
            datasets: [
                { label: "Public attention share", data: shareRows.map((row) => row.public_share), backgroundColor: makeBarGradient(colors.blue), borderRadius: 8, borderSkipped: false, percent: true },
                { label: "Government expenditure share", data: shareRows.map((row) => row.government_share), backgroundColor: colors.teal, borderRadius: 8, borderSkipped: false, percent: true },
            ],
        },
        options: {
            scales: {
                x: { ticks: { color: colors.ticks }, grid: { display: false } },
                y: { beginAtZero: true, ticks: { color: colors.ticks, callback: (value) => `${value}%` }, grid: { color: colors.grid } },
            },
        },
    });

    renderChart("priorityGapChart", {
        type: "bar",
        data: {
            labels: gapRows.map((row) => row.topic_name),
            datasets: [{
                label: "Priority gap",
                data: gapRows.map((row) => row.priority_gap),
                backgroundColor: gapRows.map((row) => row.priority_gap >= 0 ? colors.blue : colors.orange),
                borderRadius: 8,
                borderSkipped: false,
                percent: true,
            }],
        },
        options: {
            indexAxis: "y",
            scales: {
                x: { ticks: { color: colors.ticks, callback: (value) => `${value}%` }, grid: { color: colors.grid } },
                y: { ticks: { color: colors.ticks }, grid: { display: false } },
            },
        },
    });
}

function renderInsights(insights, shareRows) {
    const higherPublic = [...shareRows].sort((a, b) => b.public_share - a.public_share).slice(0, 3);
    const higherGovernment = [...shareRows].sort((a, b) => b.government_share - a.government_share).slice(0, 3);
    const biggest = [...shareRows].sort((a, b) => Math.abs(b.priority_gap) - Math.abs(a.priority_gap)).slice(0, 3);

    const topicList = (rows, valueKey, fallback) => rows.length
        ? rows.map((row) => `${row.topic_name} (${percentFormat(Math.abs(row[valueKey]))})`).join(", ")
        : fallback;

    document.getElementById("alignmentInsights").innerHTML = `
        <article class="insight-card">
            <h3>Most Discussed Public Topics</h3>
            <p>${topicList(higherPublic, "public_share", "No public topic shares were found in the current data.")}</p>
        </article>
        <article class="insight-card">
            <h3>Largest Government Priorities</h3>
            <p>${topicList(higherGovernment, "government_share", "No government expenditure shares were found in the current data.")}</p>
        </article>
        <article class="insight-card">
            <h3>Largest Misalignment Gaps</h3>
            <p>${topicList(biggest, "priority_gap", "No alignment gaps were found.")}</p>
        </article>
    `;
}

function setupTabs() {
    document.querySelectorAll(".tab-button").forEach((button) => {
        button.addEventListener("click", () => {
            document.querySelectorAll(".tab-button").forEach((item) => item.classList.remove("active"));
            document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("active"));
            button.classList.add("active");
            document.getElementById(button.dataset.tab).classList.add("active");
            if (button.dataset.tab === "institutional" && window.resizeDashboardMap) {
                window.resizeDashboardMap();
            }
        });
    });
}

function setupCountryControls() {
    document.getElementById("countrySelect").addEventListener("change", (event) => {
        selectCountry(event.target.value);
    });
    document.getElementById("resetCountry").addEventListener("click", () => {
        selectCountry(defaultCountry);
    });
}

async function loadAll() {
    clearError();
    setLoading(true);
    try {
        await loadCountries();
        await Promise.all([loadPublicDiscourse(), loadInstitutional(), loadAlignment()]);
        if (window.initDashboardMap) {
            window.initDashboardMap(countryNames, selectCountry, selectedCountry);
        }
    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    setupTabs();
    setupCountryControls();
    if (window.lucide) {
        window.lucide.createIcons();
    }
    loadAll();
});
