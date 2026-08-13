'use client';

import { useEffect, useState } from 'react';

type HITLItem = {
  id: string;
  action: string;
  description: string;
  decided: boolean;
  decision?: string | null;
};

export default function HITLPage() {
  const [items, setItems] = useState<HITLItem[]>([]);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    const res = await fetch('http://127.0.0.1:8125/hitl/queue');
    if (res.ok) setItems(await res.json());
    setLoading(false);
  }

  useEffect(() => { load(); }, []);

  async function approve(id: string) {
    await fetch(`http://127.0.0.1:8125/hitl/${encodeURIComponent(id)}/approve`, { method: 'POST' });
    load();
  }

  async function reject(id: string) {
    await fetch(`http://127.0.0.1:8125/hitl/${encodeURIComponent(id)}/reject`, { method: 'POST' });
    load();
  }

  return (
    <div className="border border-white/10 rounded">
      <div className="px-3 py-2 border-b border-white/10 flex items-center justify-between">
        <div className="text-sm font-semibold">HITL Queue</div>
        <button onClick={load} className="text-xs border border-white/10 rounded px-2 py-1">{loading ? 'Loading...' : 'Refresh'}</button>
      </div>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="text-gray-400">
            <th className="px-3 py-2">ID</th>
            <th className="px-3 py-2">Action</th>
            <th className="px-3 py-2">Description</th>
            <th className="px-3 py-2">Decision</th>
            <th className="px-3 py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-t border-white/5">
              <td className="px-3 py-2">{item.id}</td>
              <td className="px-3 py-2">{item.action}</td>
              <td className="px-3 py-2">{item.description}</td>
              <td className="px-3 py-2">{item.decided ? item.decision ?? 'modified' : 'pending'}</td>
              <td className="px-3 py-2">
                <button onClick={() => approve(item.id)} className="mr-2 text-xs border border-white/10 rounded px-2 py-1">Approve</button>
                <button onClick={() => reject(item.id)} className="text-xs border border-white/10 rounded px-2 py-1">Reject</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
