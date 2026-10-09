let dashboardMap = null;
let countryLayer = null;
let selectedLayer = null;
let availableCountries = [];
let onCountrySelected = null;

const WORLD_GEOJSON_URL = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json";

const countryAliases = {
    "United States of America": "United States",
    "Russian Federation": "Russia",
    "Korea, Republic of": "South Korea",
    "Republic of Korea": "South Korea",
    "Iran, Islamic Republic of": "Iran",
    "Viet Nam": "Vietnam",
    "Syrian Arab Republic": "Syria",
    "Bolivia, Plurinational State of": "Bolivia",
    "Venezuela, Bolivarian Republic of": "Venezuela",
    "Tanzania, United Republic of": "Tanzania",
    "Congo, The Democratic Republic of the": "Democratic Republic of the Congo",
    "Czech Republic": "Czechia",
};

function normalizeCountryName(name) {
    return String(name || "")
        .toLowerCase()
        .replace(/^the\s+/, "")
        .replace(/&/g, "and")
        .replace(/[^a-z0-9]+/g, " ")
        .trim();
}

function matchCountry(rawName) {
    const aliased = countryAliases[rawName] || rawName;
    const normalized = normalizeCountryName(aliased);
    return availableCountries.find((country) => normalizeCountryName(country) === normalized) || null;
}

function defaultStyle(feature) {
    const country = matchCountry(feature.properties.name);
    return {
        color: "#ffffff",
        weight: 0.7,
        fillColor: country ? "#2563EB" : "#CBD5E1",
        fillOpacity: country ? 0.64 : 0.45,
    };
}

function highlightStyle() {
    return {
        color: "#0F172A",
        weight: 1.6,
        fillColor: "#0F766E",
        fillOpacity: 0.82,
    };
}

function bindCountryFeature(feature, layer) {
    const matchedCountry = matchCountry(feature.properties.name);
    const label = matchedCountry || feature.properties.name;

    layer.bindTooltip(label, { sticky: true });
    layer.on({
        mouseover() {
            if (layer !== selectedLayer) {
                layer.setStyle({ weight: 1.2, fillOpacity: 0.76, fillColor: "#2563EB" });
            }
        },
        mouseout() {
            if (layer !== selectedLayer && countryLayer) {
                countryLayer.resetStyle(layer);
            }
        },
        click() {
            if (matchedCountry && onCountrySelected) {
                onCountrySelected(matchedCountry);
            }
        },
    });
}

function highlightMapCountry(countryName) {
    if (!countryLayer) {
        return;
    }

    selectedLayer = null;
    countryLayer.eachLayer((layer) => {
        countryLayer.resetStyle(layer);
        const matchedCountry = matchCountry(layer.feature.properties.name);
        if (matchedCountry === countryName) {
            selectedLayer = layer;
            layer.setStyle(highlightStyle());
            layer.bringToFront();
        }
    });
}

async function initDashboardMap(countries, selectHandler, initialCountry) {
    availableCountries = countries || [];
    onCountrySelected = selectHandler;

    if (dashboardMap) {
        highlightMapCountry(initialCountry);
        dashboardMap.invalidateSize();
        return;
    }

    dashboardMap = L.map("worldMap", {
        worldCopyJump: true,
        minZoom: 2,
        maxZoom: 6,
    }).setView([24, 10], 2);

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 6,
        attribution: "&copy; OpenStreetMap contributors",
    }).addTo(dashboardMap);

    const response = await fetch(WORLD_GEOJSON_URL);
    const geojson = await response.json();

    countryLayer = L.geoJSON(geojson, {
        style: defaultStyle,
        onEachFeature: bindCountryFeature,
    }).addTo(dashboardMap);

    highlightMapCountry(initialCountry);
    setTimeout(() => dashboardMap.invalidateSize(), 150);
}

function resizeDashboardMap() {
    if (dashboardMap) {
        setTimeout(() => dashboardMap.invalidateSize(), 120);
    }
}

window.initDashboardMap = initDashboardMap;
window.highlightMapCountry = highlightMapCountry;
window.resizeDashboardMap = resizeDashboardMap;
