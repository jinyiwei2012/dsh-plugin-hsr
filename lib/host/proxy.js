// /hsr-api 反向代理：把前端对本地服务的请求（尤其图片）转发过去
import { PROXY_PREFIX } from './consts.js'

export function registerProxy(ctx, client) {
  ctx.inject(['webServer'], (wctx) => {
    wctx.effect(() =>
      wctx.webServer.register({
        kind: 'prefix',
        path: PROXY_PREFIX,
        handler: async (req, res) => {
          const rest = req.url.slice(PROXY_PREFIX.length)
          const target = client.base + rest
          try {
            const chunks = []
            for await (const chunk of req) chunks.push(chunk)
            const upstream = await fetch(target, {
              method: req.method,
              headers: req.headers['content-type']
                ? { 'content-type': req.headers['content-type'] }
                : undefined,
              body: chunks.length ? Buffer.concat(chunks) : undefined,
            })
            const buf = Buffer.from(await upstream.arrayBuffer())
            res.writeHead(upstream.status, {
              'content-type': upstream.headers.get('content-type') || 'application/octet-stream',
              'cache-control': 'public, max-age=86400',
            })
            res.end(buf)
          } catch (e) {
            res.writeHead(502, { 'content-type': 'application/json' })
            res.end(JSON.stringify({ ok: false, summary: `代理失败: ${String(e?.message || e)}` }))
          }
        },
      }),
    )
  })
}

/** 把服务返回的相对图片地址改写成前端可访问的代理地址 */
export function rewriteSegments(segments) {
  return (segments || []).map((seg) => {
    if (!seg || typeof seg !== 'object') return seg
    if (seg.type === 'node') return { ...seg, items: rewriteSegments(seg.items) }
    if (typeof seg.url === 'string' && seg.url.startsWith('/api/')) {
      return { ...seg, url: PROXY_PREFIX + seg.url }
    }
    return seg
  })
}
