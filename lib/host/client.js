// 与服务通信的 HTTP 客户端
export function makeClient(port) {
  const base = `http://127.0.0.1:${port}`

  async function call(path, { method = 'GET', body, signal, timeoutMs = 300000 } = {}) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeoutMs)
    const onAbort = () => controller.abort()
    if (signal) signal.addEventListener('abort', onAbort, { once: true })

    try {
      const res = await fetch(base + path, {
        method,
        headers: body ? { 'content-type': 'application/json' } : undefined,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      })
      const text = await res.text()
      let data
      try {
        data = text ? JSON.parse(text) : null
      } catch {
        throw new Error(`服务返回非 JSON (${res.status}): ${text.slice(0, 200)}`)
      }
      if (!res.ok) throw new Error(data?.summary || data?.error || `服务错误 ${res.status}`)
      return data
    } finally {
      clearTimeout(timer)
      if (signal) signal.removeEventListener('abort', onAbort)
    }
  }

  return { base, call }
}
