// 本地服务托管: 解析目录、挑选解释器、拉起与健康检查
import { spawn } from 'node:child_process'
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

export const PKG_NAME = 'dsh-plugin-hsr'
export const ROOT = join(dirname(fileURLToPath(import.meta.url)), '../..')

/** venv 里的解释器路径（随平台不同） */
export function venvPython(serviceDir) {
  const win = process.platform === 'win32'
  return join(serviceDir, '.venv', win ? 'Scripts' : 'bin', win ? 'python.exe' : 'python')
}

/** 优先用 venv，其次系统 python */
export function servicePython(serviceDir) {
  const venv = venvPython(serviceDir)
  if (existsSync(venv)) return venv
  return process.platform === 'win32' ? 'python' : 'python3'
}

/** 按优先级找 service 目录 */
export function resolveServiceDir(config) {
  const home = process.env.DSH_HOME || join(process.env.HOME || process.env.USERPROFILE || '', '.dsh')
  const profiles = join(home, 'profiles')
  const candidates = [config?.servicePath, process.env.HSR_SERVICE_DIR]

  let names = []
  try {
    names = readdirSync(profiles)
  } catch {
    /* 没有 profiles 目录就跳过 */
  }
  for (const name of names) {
    try {
      const manifest = JSON.parse(readFileSync(join(profiles, name, 'package.json'), 'utf8'))
      const spec = manifest?.dependencies?.[PKG_NAME]
      if (typeof spec === 'string' && spec.startsWith('file:')) {
        candidates.push(join(spec.slice('file:'.length), 'service'))
      }
    } catch {
      /* 忽略损坏的 profile */
    }
    candidates.push(join(profiles, name, 'node_modules', PKG_NAME, 'service'))
  }
  candidates.push(join(ROOT, 'service'))

  const valid = candidates.filter((dir) => dir && existsSync(join(dir, 'hsr', 'server.py')))
  return valid[0] || join(ROOT, 'service')
}

/** 从数据目录读设置（改动需重启生效） */
export function readServiceConfig(serviceDir) {
  try {
    return JSON.parse(readFileSync(join(serviceDir, 'data', 'config.json'), 'utf8'))
  } catch {
    return {}
  }
}

/** 是否把工具暴露给模型 */
export function exposeToModelFlag(serviceDir) {
  return readServiceConfig(serviceDir).expose_to_model !== false
}

/** 命令前缀，逗号分隔 */
export function readPrefixes(serviceDir) {
  const raw = String(readServiceConfig(serviceDir).command_prefix ?? 'sr')
  const list = raw.split(/[,，]/).map((x) => x.trim()).filter(Boolean)
  return list.length ? list : ['sr']
}

const RESTART_EXIT = 75

export function startService(ctx, config) {
  const python = servicePython(config.serviceDir)
  let child
  let stopping = false
  let timer
  let backoff = 500

  const log = (buf, level) => {
    const line = buf.toString().trimEnd()
    if (!line) return
    if (ctx.logger?.[level]) ctx.logger[level](line)
    else console.log(`[hsr] ${line}`)
  }

  const launch = () => {
    if (stopping) return
    child = spawn(python, ['-m', 'hsr.server', '--port', String(config.port)], {
      cwd: config.serviceDir,
      env: { ...process.env, PYTHONUNBUFFERED: '1', PYTHONIOENCODING: 'utf-8' },
      stdio: ['ignore', 'pipe', 'pipe'],
    })
    child.stdout.on('data', (b) => log(b, 'info'))
    child.stderr.on('data', (b) => log(b, 'warn'))
    child.on('error', (e) => {
      console.log(`[hsr] 服务启动失败: ${e?.message || e}（检查 Python 是否在 PATH）`)
    })
    child.on('exit', (code) => {
      child = undefined
      if (stopping) return
      const asked = code === RESTART_EXIT
      const wait = asked ? 400 : backoff
      if (asked) backoff = 500
      else backoff = Math.min(backoff * 2, 10000)
      console.log(`[hsr] 服务退出 code=${code}${asked ? ' (主动重启)' : ''}, ${wait}ms 后拉起`)
      timer = setTimeout(launch, wait)
    })
  }

  launch()

  const stop = () => {
    stopping = true
    if (timer) clearTimeout(timer)
    try {
      child?.kill('SIGTERM')
    } catch {
      /* 已经退出 */
    }
  }
  process.on('exit', stop)
  return () => {
    process.removeListener('exit', stop)
    stop()
  }
}

/** 轮询等待服务就绪 */
export async function waitReady(client, tries = 40) {
  for (let i = 0; i < tries; i++) {
    try {
      await client.call('/api/health', { timeoutMs: 2000 })
      return true
    } catch {
      await new Promise((r) => setTimeout(r, 500))
    }
  }
  return false
}

export function troubleshooting(serviceDir) {
  const python = servicePython(serviceDir)
  return [
    '星铁插件服务未就绪。',
    `服务目录: ${serviceDir}`,
    `解释器: ${python}`,
    '排查步骤:',
    '  1. 确认已安装 Python 3.9+ 并在 PATH 中（命令行执行 python --version）',
    `  2. 手动启动看报错: cd "${serviceDir}" && ${python} -m hsr.server --port 9778`,
    '  3. 如果是刚装好，重启 DSH 桌面端让插件重新拉起服务',
  ].join('\n')
}
