import { makeClient } from './host/client.js'
import { registerProxy, rewriteSegments } from './host/proxy.js'
import {
  exposeToModelFlag,
  readPrefixes,
  resolveServiceDir,
  startService,
  waitReady,
} from './host/service.js'
import { registerTool } from './host/tool.js'

export const name = 'hsr-plugin'
export const inject = ['tools']

export function apply(ctx, config = {}) {
  const port = config.port ?? 9778
  const serviceDir = resolveServiceDir(config)
  const client = makeClient(port)

  if (config.autoStart !== false) {
    ctx.effect(() => startService(ctx, { port, serviceDir }))
    waitReady(client).then((ok) => {
      if (!ok) console.log('[hsr] 服务未能在 20s 内就绪，检查 Python 环境')
    })
  }

  // 图片反代：前端通过 /hsr-api 访问本地服务渲染的卡片
  registerProxy(ctx, client)

  // 零上下文模式：只保留 / 命令，不把工具描述塞进模型上下文
  if (config.exposeToModel === false || !exposeToModelFlag(serviceDir)) {
    console.log('[hsr] 零上下文模式: 模型不可见，请用 / 命令')
  } else {
    registerTool(ctx, client, serviceDir)
  }

  // 命令注册（软依赖：只有带交互界面的 profile 才有 commands）
  ctx.inject(['commands'], (cctx) => {
    for (const prefix of readPrefixes(serviceDir)) {
      cctx.commands.register({
        name: prefix,
        description: '直接执行星铁查询命令，不经过模型',
        input: { hint: '<命令> 如 查询 / 练度 / 昔涟遗器' },
        handler: async (invocation) => {
          const command = String(invocation?.input?.text || '').trim()
          const data = await client.call('/api/chat', {
            method: 'POST',
            body: { command },
            signal: invocation?.signal,
          })
          return {
            ok: data?.ok !== false,
            text: data?.summary || '已执行',
            segments: rewriteSegments(data?.segments),
          }
        },
      })
    }
  })
}
