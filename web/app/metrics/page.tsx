'use client';

import { useEffect, useMemo, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

type Metric = { name: string; value: number; unit: string; ts: number };

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://127.0.0.1:8125/metrics');
      if (res.ok) {
        const data = await res.json();
        const ts = Date.now();
        setMetrics((prev) => [...prev.slice(-59), ...data.map((m: any) => ({ ...m, ts }))]);
      } else setError(`HTTP ${res.status}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);
  useEffect(() => { const id = setInterval(load, 2000); return () => clearInterval(id); }, []);

  const rows = useMemo(() => metrics.map((m) => ({ ...m, time: new Date(m.ts).toLocaleTimeString() })), [metrics]);

  return (
    <div className="border border-white/10 rounded">
      <div className="px-3 py-2 border-b border-white/10 flex items-center justify-between">
        <div className="text-sm font-semibold">Metrics</div>
        <button onClick={load} className="text-xs border border-white/10 rounded px-2 py-1">{loading ? 'Loading...' : 'Refresh'}</button>
      </div>
      {error && <div className="px-3 py-2 text-xs text-red-200 border-b border-white/10">{error}</div>}
      <div className="p-3 grid gap-4">
        <Chart title="Modules total" dataKey="modules_total" rows={rows} color="#8884d8" />
        <Chart title="Active modules" dataKey="modules_active" rows={rows} color="#82ca9d" />
        <Chart title="HITL queue depth" dataKey="hitl_queue_depth" rows={rows} color="#ffc658" />
      </div>
    </div>
  );
}

function Chart({ title, dataKey, rows, color }: { title: string; dataKey: string; rows: any[]; color: string }) {
  return (
    <div className="border border-white/10 rounded">
      <div className="px-3 py-2 text-xs text-gray-400">{title}</div>
      <div className="px-2 pb-2 h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Area type="monotone" dataKey={dataKey} stroke={color} fill={color} fillOpacity="0.25" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
