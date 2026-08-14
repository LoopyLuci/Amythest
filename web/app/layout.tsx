import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Amythest Dashboard',
  description: 'Amythest modular model runtime',
};

async function fetchStatus() {
  const res = await fetch('http://127.0.0.1:8125/status', { cache: 'no-store' });
  if (!res.ok) return null;
  return res.json();
}

async function fetchModules() {
  const res = await fetch('http://127.0.0.1:8125/modules', { cache: 'no-store' });
  if (!res.ok) return [];
  return res.json();
}

async function fetchHITL() {
  const res = await fetch('http://127.0.0.1:8125/hitl/queue', { cache: 'no-store' });
  if (!res.ok) return [];
  return res.json();
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const status = await fetchStatus();
  const modules = await fetchModules();
  const hitl = await fetchHITL();

  return (
    <html lang="en">
      <body className="min-h-screen bg-[#0b0f1a] text-gray-200">
        <header className="border-b border-white/10 px-4 py-3 flex items-center justify-between">
          <div className="font-semibold tracking-wide">Amythest Dashboard</div>
          <div className="text-xs text-gray-400 flex gap-2 items-center">
            {status ? `Active modules: ${status.active_count}` : 'Runtime offline'}
            <a href="/" className="px-2 py-1 border border-white/10 rounded text-xs">Dashboard</a>
            <a href="/modules" className="px-2 py-1 border border-white/10 rounded text-xs">Modules</a>
            <a href="/hitl" className="px-2 py-1 border border-white/10 rounded text-xs">HITL</a>
            <a href="/usage" className="px-2 py-1 border border-white/10 rounded text-xs">Usage</a>
            <a href="/metrics" className="px-2 py-1 border border-white/10 rounded text-xs">Metrics</a>
          </div>
        </header>
        <main className="p-4 grid gap-4">
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
            <div className="px-3 py-2 border-b border-white/10 text-sm font-semibold">Modules</div>
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-gray-400">
                  <th className="px-3 py-2">Name</th>
                  <th className="px-3 py-2">Version</th>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Active</th>
                </tr>
              </thead>
              <tbody>
                {modules.map((m: any) => (
                  <tr key={`${m.name}-${m.version}`} className="border-t border-white/5">
                    <td className="px-3 py-2">{m.name}</td>
                    <td className="px-3 py-2">{m.version}</td>
                    <td className="px-3 py-2">{m.type}</td>
                    <td className="px-3 py-2">{m.active ? '✓' : '✗'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="border border-white/10 rounded">
            <div className="px-3 py-2 border-b border-white/10 text-sm font-semibold">HITL Queue</div>
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-gray-400">
                  <th className="px-3 py-2">ID</th>
                  <th className="px-3 py-2">Action</th>
                  <th className="px-3 py-2">Description</th>
                  <th className="px-3 py-2">Decided</th>
                </tr>
              </thead>
              <tbody>
                {hitl.map((item: any) => (
                  <tr key={item.id} className="border-t border-white/5">
                    <td className="px-3 py-2">{item.id}</td>
                    <td className="px-3 py-2">{item.action}</td>
                    <td className="px-3 py-2">{item.description}</td>
                    <td className="px-3 py-2">{item.decided ? item.decision : 'pending'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          {children}
        </main>
      </body>
    </html>
  );
}
