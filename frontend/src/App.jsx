import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { AlertTriangle, CalendarDays, Cloud, RefreshCw, Target, Wind } from "lucide-react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const rawUrl = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? "" : "http://localhost:8000");
const API_URL = rawUrl.replace(/^["']|["']$/g, "").replace(/\/+$/, "").trim();

function formatNumber(value, suffix = "") {
  return value == null ? "—" : `${Number(value).toLocaleString(undefined, { maximumFractionDigits: 1 })}${suffix}`;
}

function MetricCard({ icon: Icon, label, value, detail }) {
  return (
    <article className="metric-card">
      <div className="metric-icon"><Icon size={18} /></div>
      <div><p>{label}</p><strong>{value}</strong><span>{detail}</span></div>
    </article>
  );
}

export default function App() {
  const [dashboard, setDashboard] = useState(null);
  const [selectedDay, setSelectedDay] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    setLoading(true);
    setError("");
    try {
      const response = await axios.get(`${API_URL}/api/dashboard`);
      setDashboard(response.data);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to load Elexon data. Check that the API is running.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadDashboard(); }, []);

  const days = useMemo(() => {
    if (!dashboard) return [];
    return [...new Set(dashboard.data.map((row) => row.startTime.slice(0, 10)))];
  }, [dashboard]);
  const visibleData = useMemo(
    () => dashboard?.data.filter((row) => selectedDay === "all" || row.startTime.startsWith(selectedDay)) || [],
    [dashboard, selectedDay],
  );

  if (loading) return <main className="page centered"><RefreshCw className="spin" /><p>Loading January 2026 wind intelligence…</p></main>;
  if (error) return <main className="page centered"><AlertTriangle size={32} /><h1>Data unavailable</h1><p>{error}</p><button onClick={loadDashboard}>Try again</button></main>;

  const { metrics, metadata } = dashboard;
  return (
    <main className="page">
      <header className="hero">
        <div className="brand"><div className="brand-mark"><Wind /></div><span>GRID / SIGNAL</span></div>
        <div className="hero-content">
          <p className="eyebrow">DAY-AHEAD PROCUREMENT INTELLIGENCE</p>
          <h1>Know the wind.<br /><em>Buy with confidence.</em></h1>
          <p className="hero-copy">A decision view of the latest available national wind forecast versus actual generation for January 2026.</p>
        </div>
        <div className="hero-meta"><span><CalendarDays size={15} /> {metadata.deliveryWindow}</span><span><Cloud size={15} /> Elexon BMRS</span></div>
      </header>

      <section className="content">
        <div className="section-heading"><div><p className="eyebrow">PERFORMANCE SNAPSHOT</p><h2>Forecast accuracy</h2></div><button className="refresh" onClick={loadDashboard}><RefreshCw size={16} /> Refresh data</button></div>
        <div className="metrics">
          <MetricCard icon={Target} label="Mean absolute error" value={`${formatNumber(metrics.mae)} MW`} detail="Lower is better" />
          <MetricCard icon={Wind} label="RMSE" value={`${formatNumber(metrics.rmse)} MW`} detail="Penalizes large misses" />
          <MetricCard icon={Cloud} label="Forecast bias" value={`${formatNumber(metrics.bias)} MW`} detail={metrics.bias > 0 ? "Tends to over-forecast" : "Tends to under-forecast"} />
          <MetricCard icon={CalendarDays} label="Matched intervals" value={formatNumber(metrics.matchedIntervals)} detail="Hourly aligned observations" />
        </div>

        <div className="section-heading chart-heading"><div><p className="eyebrow">DELIVERY PROFILE</p><h2>Actual vs selected forecast</h2></div><select value={selectedDay} onChange={(event) => setSelectedDay(event.target.value)} aria-label="Filter by delivery day"><option value="all">All January</option>{days.map((day) => <option key={day} value={day}>{day}</option>)}</select></div>
        <section className="chart-card">
          <ResponsiveContainer width="100%" height={380}>
            <LineChart data={visibleData} margin={{ top: 12, right: 20, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#dbe2e8" vertical={false} />
              <XAxis dataKey="startTime" tickFormatter={(value) => value.slice(5, 16).replace("T", " ")} minTickGap={42} />
              <YAxis tickFormatter={(value) => `${Math.round(value / 1000)}k`} />
              <Tooltip labelFormatter={(value) => new Date(value).toLocaleString()} formatter={(value) => [`${Number(value).toLocaleString()} MW`]} />
              <Legend />
              <Line type="monotone" dataKey="actual" name="Actual generation" stroke="#122b3a" strokeWidth={2.5} dot={false} />
              <Line type="monotone" dataKey="forecast" name="Day-ahead forecast" stroke="#e47645" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </section>

        <section className="lower-grid">
          <div className="table-card"><div className="card-title"><div><p className="eyebrow">DECISION DETAIL</p><h2>Largest forecast misses</h2></div></div><div className="table-wrap"><table><thead><tr><th>Delivery</th><th>Actual</th><th>Forecast</th><th>Error</th></tr></thead><tbody>{[...visibleData].sort((a, b) => b.absoluteError - a.absoluteError).slice(0, 6).map((row) => <tr key={row.startTime}><td>{new Date(row.startTime).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</td><td>{formatNumber(row.actual)} MW</td><td>{formatNumber(row.forecast)} MW</td><td className={row.error > 0 ? "positive" : "negative"}>{row.error > 0 ? "+" : ""}{formatNumber(row.error)} MW</td></tr>)}</tbody></table></div></div>
          <aside className="method-card"><p className="eyebrow">METHOD NOTE</p><h2>The decision lens</h2><p>{metadata.selectionRule}. {metadata.analysisResolution}. This makes the comparison representative of the information available when a day-ahead purchase decision is made.</p><div className="source-list"><span>Actual source <b>{metadata.actualDataset} / WIND</b></span><span>Forecast source <b>{metadata.forecastDataset}</b></span><span>Forecast observations <b>{metadata.forecastRecords.toLocaleString()}</b></span></div></aside>
        </section>
      </section>
      <footer>GRID / SIGNAL <span>Prototype decision support · Data from Elexon BMRS</span></footer>
    </main>
  );
}
