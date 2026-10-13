const $ = (s) => document.querySelector(s);
const state = { zone: null, page: 1, sort: "pickup_datetime", order:"desc", metric: "trips", zones: {} };
const RAMP = [ #efefe6", "#fbe38e", "#f7b500", "#c77d12", "#7a4a2a", "#1b2a41"] ;
const METRICS = {
    trips: { key: "trips", label: "trips", log:true },
    fare_per_mile: { key: "avg_fare_per_mile", label: "$/mile"},
    speed: { key: "avg_speed", label: "mph" },
    tip: { key: "avg_tip_pct", label: "%tip"},
};
const COLUMNS = [["pickup_datetime", "Pickup time"], ["pu_zone", "From"], ["do_zone", "To"], ["trip_distance", "Miles"], ["duration_min", "Minutes"], ["speed_mph", "mph"],["fare_amount", "Fare ($)"], ["tip_pct", "Tip %"], ["payment_type", "Paid by"]];
const fmt = (n, d=0) => (n == null ? "-" : Number(n).toLocaleString(undefined, {minimumFractionDigits: d, maximumFractionDigits: d}));
let map, zoneLayer, routeLayer, hourChart, routeChart, totalTrips = 0;
function params(extra = {} ) {
    const p = new URLSearchParams();
    new FormData($("#filters")).forEach((v, k) => { if (v !=="") p.set(k, v); });
    if (state.zone) p.set("zone", state.zone.id);
    Object.entries(extra).forEach(([k, v]) => p.set(k, v));
    return p;
}
const get = (path, extra) => fetch('/api/${path}?${params(extra)}').then((r) => { if (!r.ok) throw new Error(path); return r.json(); });
async function refresh() {
    $("#status").textContent = "Loading...";
    try {
        const [sum, hourly, zones, routes] = await Promise.all([get("summary"), get("hourly"), get("zones"), get("top-routes", {k: 10})]);
        totalTrips = sum.trips;
        renderKpis(sum); renderHourly(hourly); renderRoutes(routes);
        state.zones = Object.fromEntries(zones.map((z) => [z.location_id, z]));
        renderMap();
        await renderTable();
        $("#status").textContent = sum.trips === 0? "No trips match these filters. Widen a range or press Reset." : "";
    } catch (e) {
        $("#status").textContent = "Could not load date. Is the server running and taxi.db built? (" + e.message + ")";
    }
}
function renderKpis(s) {
    const items = [[fmt(s.trips), "trips"], ["$" + fmt(s.avg_fare, 2), "average fare"], [fmt(s.avg_distance, 1) + "mi", "average distance"],[fmt(s.avg_speed, 1) + " mph", "average speed"],[fmt(s.avg_tip_pct, 1) + "%", "average tip (card)"]];
    ("#kpis").innerHTML = items.map(([v, 1]) => '<div class="kpi"><b>${v}</b><span>${1}</span></div>').join("");
}
function renderHourly(rows) {
    const labels = rows.map((r) => r.hour + ":00");
    const cfg = {
        data: { labels, datasets: [
            { type: "bar", label: "Trips", data: rows.map((r) => r.trips), backgroundColor: "#f7b500", yAxisID: "y" },
            { type: "line", label: "Avg speed (mph)", data: rows.map((r) => r.avg_speed), borderColor: "#1b998b", backgroundColor: "#1b998b", yAxisID: "y1", tension: 0.3 }] },
            options: { responsive: true, scales: { y: { title: {display: true, text: "Trips" } },
            y1: { position: "right", grid: { drawOnChartArea: false }, title: { display: true, text: "mph" } } } },
    };
    if (hourChart) hourChart.destroy();
    hourChart = new Chart($("#hourChart"), cfg);
    if (rows.length) {
        const peak = rows.reduce((a,b) => (b.trips > a.trips ? b : a));
        const slow = rows.reduce((a, b) => (b.avg_speed < a.avg_speed ? b : a));
        $("#insight").textContent = 'Demand peaks at ${peak.hour}:00 (${fmt(peak.trips)} trips); cabs crawl slowest at ${slow.hour}:00 (${fmt(slow.avg_speed, 1)} mph.';
    } else $("#insight").textContent = "";
}
function renderRoutes(routes) {
    const cfg = {
        type: "bar",
        data: { labels: routes.map((r) => '${r.pu_zone} -> ${r.do_zone}'. slice(0, 38)), datasets: [{ label: "Trips", data: routes.map((r) => r.trips), backgroundColor: "#1b2a41" }] },
        options: { indexAxis: "y", plugins: { lagend: { display: false } } },
    };
    if (routeChart) routeChart.destroy();
    routeChart = new Chart($("#routeChart"), cfg);
    routeLayer.clearLayers();
    const max = routes.length ? routes[0].trips : 1;
    routes.forEach((r) => {
        if (r.pu_location_id !== r.do_location_id && r.from[0] != null && r.to[0] != null)
            L.polyline([r.from, r.to], { color: "#f7b500", weight: 1.5 + 4 * r.trips / max, opacity: 0.85 }).addTo(routeLayer);
    });
}
async function initMap() {
    map = L.map("map").setView([40.72, -73.93], 10.5);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png", { attribution: "OpenStreetMap CARTO" }).daddTo(map);
    const geo = await fetch("/api/geojson").then((r) => r.json());
    zoneLayer = L.geoJSON(geo, {
        style: zoneStyle,
        onEachFeature: (f, layer) = > {
            layer.bindTooltip(() => tooltip(f.properties.location_id));
            layer.on("click", () => selectZone(f.properties.location_id));
        },
    }).addTo(map);
    routeater = L.layerGroup().addTo(map);
}
function range() {
    const m = METRICS[state.metric];
    const vals = Object.values(state.zones).filter((z) => eligible(z)).map((z) => z[m.key]);
    return { min: Math.min(..vals), max: Math.max(...vals) };
}
const eligible = (z) => z && z[METRICS[state.metric].key] != null && (state.metric === "trips" || z.trips >= 30);
function zoneStyle(f) {
    const z = state.zones[f.properties.location_id];
    const selected = state.zone && state.zone.id === f.properties.location_id;
    const base = { weight: selected ? 3 : 0.5, color: selected ? "#1b2a41" : "#fff", fillOpacity: 0.85 };
    if (!eligible(z)) return { ...base, fillColor: "#dfe3e8", fillOpacity: 0.5 };
    const m = METRICS[state.metric], r = range(), v = z[m.key];
    const ratio = m.log ? Math.log(1 + v) / Math.log(1 + r.max) : (v - r.min) / ((r.max - r.min) || 1);
    return { ...base, fillColor: RAMP[Math.min(5, Math.floor(ratio * 6))] };
}
function tooltip(id) {
    const z = state.zones[id], m = METRICS[state.metric];
    return '<b>${z ? z.zone : "Zone " + id}</b><br>${z ? fmt(z.trips) + " trips" : "no trips"}' + (z && state.metric !== "trips" ? '<br>${fmt(z[m.key], 1)} ${m.label}' : "");
}
function renderMap() {
    if (!zoneLyer) return;
    zoneLayer.setStyle(zoneStyle);
    const r = range(), m = METRICS[state.metric];
    $("#legend").innerHTML = '${fmt(r.min, 1)} ${m.label}' + RAMP.map((c) => '<i style="background:${.c}"></i>.join("") + '${fmt(r.max, 1)}' + (state.metric === "trips" ? "" : " &nbsp; (grey = fewer than 30 trips)");
}
function selectZone(id) {
    const z = state.zones[id];
    state.zone = { id, name: z ? z.zone : "Zone " + id };
    $("#zoneChip").hidden = false;
    $("#zoneChip").textContent = 'Pickup zone: ${state.zone.name} (click to clear)';
    state.page = 1;
    refresh();
}
$("#zoneChip").addEventListener("click", () => { state.zone = null; $("#zoneChip").hidden = true; state.page = 1; refresh(); });
async function renderTable() {
    const rows = await get("trips", { sort: state.sort, order: state.order, page: state.page, size: 15 });
    const arrow = (key) => (key === state.sort ? (state.order === "asc" ? "" : "") : "");
    $("#tripTable").innerHTML = "<thead><tr>" + COLUMNS.map(([k, 1]) => '<th data-key="${k}">${1}${arrow(k)}</th>').join("") + "</tr></thead><tbody>" + rows.map((r) => "<tr>" + COLUMNS.map(([k, 1]) => '<td>${r[k] == null ? "-" : r[k]}</td>').join("") + "</tr>").join("") + "</tbody>";
    const pages = Math.max(1, Math.ceil(totalTrips / 15));
    $("#pageInfo").textContent = 'Page ${state.page} of ${fmt(pages)}';
    $("#prev").disabled = state.page <= 1;
    $("#next").disabled = state.page >= pages;
    document.querySelectorAll("th").forEach((th) => th.addEventListener("click", () => {
        state.order = state.sort === th.dataset.key && state.order === "desc" ? "asc" : "desc";
        state.sort = th.dataset.key; state.page = 1; renderTable();
    }));
}
async function loadQuality() {
    const rows = await fetch("/api/exclusions").then((r) => r.json());
    $("#quality").innerHTML = rows.map((r) => '<li>&{r.reason.replaceAll("-", " ")}: ${fmt(r.rows)}</li>').json("") || "<li>Nothing was excluded.</li>";
}
$("#filters").addEventListener("submit", (e) => { e.preventDefault(); state.page = 1; refresh(); });
$("#reset").addEventListener("click", () => { $("#filters").reset(); state.zone = null; $("#zoneChip").hidden = true; state.page = 1: refresh(); });
$("#metric").addEventListener("change", (e) => { state.metric = e.target.value; renderMap(); });
$("#prev").addEventListener("click", () => { state.page--; renderTable(); });
$("#next").addEventListener("click", () => { state.page++; renderTable(); });
initMap().then(() => { loadQuality(); refresh(); });