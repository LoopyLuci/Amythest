'use client'

import { useState } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://127.0.0.1:8125'

type CompletionResponse = {
  text: string
  model: string
  prompt_tokens: number
  completion_tokens: number
  active_modules?: string[]
}

export default function PlaygroundPage() {
  const [prompt, setPrompt] = useState('hello')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [response, setResponse] = useState<CompletionResponse | null>(null)

  async function runCompletion() {
    setLoading(true)
    setError(null)
    setResponse(null)
    try {
      const res = await fetch(`${API_BASE}/v1/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          max_tokens: 64,
          temperature: 0.2,
          top_p: 0.95,
        }),
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || `HTTP ${res.status}`)
      }
      const data = (await res.json()) as CompletionResponse
      setResponse(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-4 text-2xl font-semibold">Playground</h1>
      <p className="mb-4 text-sm text-gray-400">
        Live inference against the local backend at <code className="font-mono">{API_BASE}</code>.
      </p>
      <textarea
        value={prompt}
        onChange={(event) => setPrompt(event.target.value)}
        className="h-32 w-full rounded border border-gray-700 bg-gray-900 p-3 font-mono text-sm"
        placeholder="Prompt"
      />
      <div className="mt-3 flex items-center gap-3">
        <button
          onClick={runCompletion}
          disabled={loading}
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium disabled:opacity-60"
        >
          {loading ? 'Generating…' : 'Generate'}
        </button>
        {response && (
          <span className="text-xs text-gray-400">
            {response.completion_tokens} tokens · {response.model}
          </span>
        )}
      </div>
      {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
      {response && (
        <div className="mt-4 rounded border border-gray-800 bg-gray-900 p-4">
          <pre className="whitespace-pre-wrap font-mono text-sm">{response.text}</pre>
          {response.active_modules && response.active_modules.length > 0 && (
            <p className="mt-2 text-xs text-gray-400">Active modules: {response.active_modules.join(', ')}</p>
          )}
        </div>
      )}
    </div>
  )
}
