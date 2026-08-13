'use client';

import { useEffect, useMemo, useState } from 'react';

type Module = {
  name: string;
  version: string;
  type: string;
  active: boolean;
};

type Status = {
  active_count: number;
  active_modules: Array<Record<string, unknown>>;
};

type HITLItem = {
  id: string;
  action: string;
  description: string;
  decided: boolean;
  decision?: string | null;
};

type Recommendation = {
  name: string;
  version: string;
  score: number;
  reason: string;
};

export default function Page() {
  const [modules, setModules] = useState<Module[]>([]);
  const [status, setStatus] = useState<Status | null>(null);
  const [hitl, setHITL] = useState<HITLItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('python asyncio');
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [recommendationLoading, setRecommendationLoading] = useState(false);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        setError(null);
        const [mRes, sRes, hRes] = await Promise.all([
          fetch('http://127.0.0.1:8125/modules'),
          fetch('http://127.0.0.1:8125/status'),
          fetch('http://127.0.0.1:8125/hitl/queue'),
        ]);
        if (mRes.ok) setModules(await mRes.json());
        if (sRes.ok) setStatus(await sRes.json());
        if (hRes.ok) setHITL(await hRes.json());
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  async function recommend() {
    setRecommendationLoading(true);
    setError(null);
    try {
      const res = await fetch('http://127.0.0.1:8125/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: query, top_k: 5 }),
      });
      if (res.ok) setRecommendations(await res.json());
      else setError(`Recommend failed: ${res.status}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setRecommendationLoading(false);
    }
  }

  const shortcuts = useMemo(
    () => [
      ['1', 'Modules focus'],
      ['2', 'HITL focus'],
      ['j/k', 'Navigate rows'],
      ['a', 'Activate'],
      ['d', 'Deactivate'],
      ['p', 'Pause agent'],
      ['r', 'Resume agent'],
      ['k', 'Kill agent'],
      ['/', 'Command input'],
      ['q', 'Quit'],
    ],
    []
  );

  return (
    <div className="grid gap-4">
      <section className="border border-white/10 rounded p-3">
        <div className="text-sm font-semibold mb-2">Keyboard Shortcuts</div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs">
          {shortcuts.map(([key, label]) => (
            <div key={key} className="border border-white/10 rounded px-2 py-1 flex items-center justify-between">
              <span className="text-gray-300">{label}</span>
              <span className="font-mono text-gray-100">{key}</span>
            </div>
          ))}
        </div>
      </section>

      {error && (
        <section className="border border-red-400/40 rounded p-3 text-xs text-red-200">
          Runtime connection issue: {error}
        </section>
      )}

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="border border-white/10 rounded p-3">
          <div className="text-xs text-gray-400">Active modules</div>
          <div className="text-2xl font-semibold">{status?.active_count ?? '--'}</div>
        </div>
        <div className="border border-white/10 rounded p-3">
          <div className="text-xs text-gray-400">HITL queue</div>
          <div className="text-2xl font-semibold">{hitl.length}</div>
        </div>
        <div className="border border-white/10 rounded p-3">
          <div className="text-xs text-gray-400">Runtime</div>
          <div className="text-2xl font-semibold">{status ? 'online' : 'offline'}</div>
        </div>
      </section>

      <section className="border border-white/10 rounded">
        <div className="px-3 py-2 border-b border-white/10 text-sm font-semibold">Module Recommendations</div>
        <div className="p-3 flex flex-col gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="bg-black/30 border border-white/10 rounded px-2 py-1 text-sm"
            placeholder="Task description..."
          />
          <button onClick={recommend} className="text-xs border border-white/10 rounded px-2 py-1 w-fit">
            {recommendationLoading ? 'Recommending...' : 'Recommend modules'}
          </button>
          <div className="text-xs text-gray-300">
            {recommendations.length ? (
              <table className="w-full text-left">
                <thead>
                  <tr className="text-gray-400">
                    <th className="px-2 py-1">Name</th>
                    <th className="px-2 py-1">Version</th>
                    <th className="px-2 py-1">Score</th>
                    <th className="px-2 py-1">Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {recommendations.map((r) => (
                    <tr key={`${r.name}-${r.version}`} className="border-t border-white/5">
                      <td className="px-2 py-1">{r.name}</td>
                      <td className="px-2 py-1">{r.version}</td>
                      <td className="px-2 py-1">{r.score.toFixed(2)}</td>
                      <td className="px-2 py-1">{r.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              'No recommendations yet.'
            )}
          </div>
        </div>
      </section>

      <section className="border border-white/10 rounded">
        <div className="px-3 py-2 border-b border-white/10 text-sm font-semibold">
          Active Composition
        </div>
        <div className="p-3 text-xs font-mono text-gray-300">
          {status ? JSON.stringify(status.active_modules) : 'No active modules'}
        </div>
      </section>
    </div>
  );
}
