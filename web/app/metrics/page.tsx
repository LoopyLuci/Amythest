'use client';

import { useEffect, useState } from 'react';

type Metric = {
  name: string;
  value: number;
  unit: string;
};

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://127.0.0.1:8125/metrics');
      if (res.ok) setMetrics(await res.json());
      else setError(`HTTP ${res.status}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const valueFor = (name: string) => metrics.find((m) => m.name === name)?.value ?? null;

  return (
    <div className="border border-white/10 rounded">
      <div className="px-3 py-2 border-b border-white/10 flex items-center justify-between">
        <div className="text-sm font-semibold">Metrics</div>
        <button onClick={load} className="text-xs border border-white/10 rounded px-2 py-1">{loading ? 'Loading...' : 'Refresh'}</button>
      </div>
      {error && (
        <div className="px-3 py-2 text-xs text-red-200 border-b border-white/10">{error}</div>
      )}
      <div className="p-3 grid gap-3">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <MetricCard label="Modules total" value={valueFor('modules_total')} unit="count" />
          <MetricCard label="Active modules" value={valueFor('modules_active')} unit="count" />
          <MetricCard label="HITL queue depth" value={valueFor('hitl_queue_depth')} unit="count" />
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, unit }: { label: string; value: number | null; unit: string }) {
  return (
    <div className="border border-white/10 rounded p-3">
      <div className="text-xs text-gray-400">{label}</div>
      <div className="text-2xl font-semibold">{value !== null ? `${value} ${unit}` : '--'}</div>
    </div>
  );
}
