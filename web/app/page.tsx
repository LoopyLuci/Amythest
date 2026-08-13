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

export default function Page() {
  const [modules, setModules] = useState<Module[]>([]);
  const [status, setStatus] = useState<Status | null>(null);
  const [hitl, setHITL] = useState<HITLItem[]>([]);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [mRes, sRes, hRes] = await Promise.all([
          fetch('http://127.0.0.1:8125/modules'),
          fetch('http://127.0.0.1:8125/status'),
          fetch('http://127.0.0.1:8125/hitl/queue'),
        ]);
        if (mRes.ok) setModules(await mRes.json());
        if (sRes.ok) setStatus(await sRes.json());
        if (hRes.ok) setHITL(await hRes.json());
      } catch {
        // offline
      }
    }, 1000);
    return () => clearInterval(interval);
  }, []);

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
