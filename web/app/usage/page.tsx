'use client';

import { useEffect, useState } from 'react';

type UsageRate = {
  module_name: string;
  module_version: string;
  helpful_rate: number | null;
};

export default function UsagePage() {
  const [moduleName, setModuleName] = useState('python-3.12-knowledge');
  const [moduleVersion, setModuleVersion] = useState('1.0.0');
  const [record, setRecord] = useState({ task_category: 'qa', module_name: moduleName, module_version: moduleVersion, active: true, helpful: true });
  const [rate, setRate] = useState<UsageRate | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadRate() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://127.0.0.1:8125/usage/rate?module_name=${encodeURIComponent(moduleName)}&module_version=${encodeURIComponent(moduleVersion)}`);
      if (res.ok) setRate(await res.json());
      else setError(`HTTP ${res.status}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadRate(); }, [moduleName, moduleVersion]);

  async function postRecord() {
    setError(null);
    const res = await fetch('http://127.0.0.1:8125/usage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(record),
    });
    if (!res.ok) setError(`Usage record failed: ${res.status}`);
    loadRate();
  }

  return (
    <div className="border border-white/10 rounded">
      <div className="px-3 py-2 border-b border-white/10 flex items-center justify-between">
        <div className="text-sm font-semibold">Usage</div>
      </div>
      {error && (
        <div className="px-3 py-2 text-xs text-red-200 border-b border-white/10">{error}</div>
      )}
      <div className="p-3 grid gap-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <div>
            <div className="text-xs text-gray-400 mb-1">Module name</div>
            <input value={moduleName} onChange={(e) => setModuleName(e.target.value)} className="bg-black/30 border border-white/10 rounded px-2 py-1 text-sm w-full" />
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-1">Module version</div>
            <input value={moduleVersion} onChange={(e) => setModuleVersion(e.target.value)} className="bg-black/30 border border-white/10 rounded px-2 py-1 text-sm w-full" />
          </div>
        </div>

        <div className="border border-white/10 rounded p-3">
          <div className="text-xs text-gray-400 mb-2">Record usage</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <input value={record.task_category} onChange={(e) => setRecord({ ...record, task_category: e.target.value })} className="bg-black/30 border border-white/10 rounded px-2 py-1 text-sm" placeholder="task_category" />
            <select value={record.helpful ? 'true' : 'false'} onChange={(e) => setRecord({ ...record, helpful: e.target.value === 'true' })} className="bg-black/30 border border-white/10 rounded px-2 py-1 text-sm">
              <option value="true">helpful=true</option>
              <option value="false">helpful=false</option>
            </select>
          </div>
          <button onClick={postRecord} className="mt-2 text-xs border border-white/10 rounded px-2 py-1">Record</button>
        </div>

        <div className="border border-white/10 rounded p-3">
          <div className="text-xs text-gray-400 mb-2">Helpfulness rate</div>
          <div className="text-lg font-semibold">
            {loading ? 'Loading...' : rate?.helpful_rate !== null && rate?.helpful_rate !== undefined ? `${(rate.helpful_rate * 100).toFixed(1)}%` : 'No data'}
          </div>
          <button onClick={loadRate} className="mt-2 text-xs border border-white/10 rounded px-2 py-1">Refresh</button>
        </div>
      </div>
    </div>
  );
}
