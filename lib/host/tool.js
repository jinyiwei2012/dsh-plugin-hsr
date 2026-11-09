// 模型工具注册
import { defineTool } from '@deepseek-ai/dsh-tools'

import { rewriteSegments } from './proxy.js'
import { troubleshooting } from './service.js'

const DESCRIPTION = [
  '星穹铁道（崩坏：星穹铁道）账号查询与遗器评分。把用户请求转成一条命令传入 command。',
  '命令：',
  '  查询 / 面板          账号概览',
  '  练度                 全角色遗器评分排行',
  '  <角色>面板           单角色面板（等级/星魂/光锥/面板属性）',
  '  <角色>遗器           单角色遗器逐件评分 + 提升建议',
  '  帮助                 命令说明',
  '例：查询 / 练度 / 昔涟面板 / 昔涟遗器',
  '遗器评分基于 miao-plugin 的词条权重表（106 个角色），会指出哪些副词条对该角色完全无效。',
  '数据来自米游社 Cookie（全部角色）或 mihomo 公开接口（仅游戏展柜里的角色）。',
  '结果里的图文卡片会直接展示在界面上；summary 里带有卡片上的全部文字与数值，',
  '要引用具体数字时看它就够了，不需要重复调用同一条命令。',
].join('\n')

export function registerTool(ctx, client, serviceDir) {
  ctx.tools.register(
    defineTool({
      name: 'hsr',
      description: DESCRIPTION,
      parameters: {
        command: {
          type: 'string',
          required: true,
          description: '要执行的命令，例如 "查询"、"练度"、"昔涟遗器"',
        },
        uid: {
          type: 'string',
          description: '游戏 UID；省略则用当前默认绑定的账号',
        },
        with_image: {
          type: 'boolean',
          description: '是否同时渲染一张结果卡片（默认 true）。用户只要文字时可设 false',
        },
      },
      output: {
        schema: {
          type: 'object',
          additionalProperties: true,
          properties: {
            ok: { type: 'boolean', required: true },
            summary: { type: 'string', required: true },
            title: { type: 'string' },
            lines: { type: 'array', items: { type: 'string' } },
            segments: { type: 'array', items: { type: 'object', additionalProperties: true } },
            elapsed: { type: 'number' },
          },
        },
        render: (_args, value) => [
          { type: 'text', text: value?.summary || (value?.ok ? '已执行' : '执行失败') },
        ],
        presentationMeta: (_args, value) => ({
          segments: value?.segments ?? [],
        }),
      },
      timeoutMs: 120000,
      async execute(args, exec) {
        try {
          await client.call('/api/health', { timeoutMs: 4000 })
        } catch {
          return {
            ok: false,
            title: '服务未就绪',
            summary: troubleshooting(serviceDir),
            lines: [],
            segments: [],
          }
        }

        const data = await client.call('/api/chat', {
          method: 'POST',
          body: {
            command: String(args.command || ''),
            uid: args.uid ? String(args.uid) : null,
            render: args.with_image !== false,
          },
          signal: exec?.signal,
        })

        return { ...data, segments: rewriteSegments(data?.segments) }
      },
      presentCall: (args) => ({
        card: 'generic',
        kind: 'other',
        title: `星铁 · ${String(args?.command || '').slice(0, 40)}`,
        rawInput: args,
      }),
    }),
  )
}
