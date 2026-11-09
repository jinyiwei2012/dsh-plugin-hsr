# -*- coding: utf-8 -*-
"""本地 HTTP 服务：向 DSH 插件暴露查询接口。

只监听 127.0.0.1，不对外网开放。依赖仅标准库。

接口
----
GET  /api/health          健康检查
POST /api/chat            执行命令，返回 {ok, title, summary, lines, segments}
GET  /api/accounts        已绑定账号
POST /api/refresh         清缓存后重新拉取

启动::

    python service/hsr/server.py --port 9778
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

_SERVICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SERVICE not in sys.path:
    sys.path.insert(0, _SERVICE)

from hsr import commands  # noqa: E402
from hsr.store import db  # noqa: E402

VERSION = '0.1.0'

MEDIA_DIR = os.path.join(db.DATA_DIR, 'media')


def _json_default(o: Any) -> Any:
    if isinstance(o, set):
        return list(o)
    return str(o)


def _media_path(name: str) -> str | None:
    """把 /api/media/<name> 安全地解析成文件路径。"""
    name = os.path.basename(name)
    if not name or not name.lower().endswith(('.png', '.jpg', '.webp', '.html')):
        return None
    path = os.path.join(MEDIA_DIR, name)
    return path if os.path.isfile(path) else None


class Handler(BaseHTTPRequestHandler):
    """极简 JSON API。"""

    server_version = f'dsh-plugin-hsr/{VERSION}'
    # 抑制逐请求日志噪音
    quiet = True

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        if not self.quiet:
            sys.stderr.write('%s - %s\n' % (self.address_string(), fmt % args))

    # ------------------------------------------------------------ 工具

    def _send(self, code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=_json_default).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: str) -> None:
        """直接吐一个文件（图片）。"""
        ext = os.path.splitext(path)[1].lower()
        ctype = {
            '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp',
            '.html': 'text/html; charset=utf-8',
        }.get(ext, 'application/octet-stream')
        try:
            with open(path, 'rb') as f:
                data = f.read()
        except OSError:
            self._send(404, {'ok': False, 'summary': '文件读取失败'})
            return
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'public, max-age=86400')
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get('Content-Length') or 0)
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    # ------------------------------------------------------------ 路由

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split('?')[0]
        if path == '/api/health':
            from .render import card as card_render

            self._send(200, {
                'ok': True, 'service': 'dsh-plugin-hsr', 'version': VERSION,
                'default_uid': db.get_default_uid(),
                'render': card_render.available(),
            })
        elif path.startswith('/api/media/'):
            target = _media_path(path[len('/api/media/'):])
            if target:
                self._send_file(target)
            else:
                self._send(404, {'ok': False, 'summary': '图片不存在或已过期'})
        elif path == '/api/accounts':
            self._send(200, {
                'ok': True,
                'accounts': [
                    {'uid': a.uid, 'nickname': a.nickname, 'level': a.level,
                     'server': a.server, 'has_cookie': bool(a.cookie)}
                    for a in db.list_accounts()
                ],
            })
        else:
            self._send(404, {'ok': False, 'summary': f'未知路径 {path}'})

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split('?')[0]
        body = self._read_json()

        if path == '/api/chat':
            self._chat(body)
        elif path == '/api/refresh':
            db.save_profile(body.get('uid') or db.get_default_uid(), {})
            self._send(200, {'ok': True, 'summary': '缓存已清空，下次查询会重新拉取'})
        else:
            self._send(404, {'ok': False, 'summary': f'未知路径 {path}'})

    # ------------------------------------------------------------ 业务

    def _chat(self, body: dict[str, Any]) -> None:
        command = str(body.get('command') or '').strip()
        uid = body.get('uid')
        uid = str(uid) if uid else None
        want_image = body.get('render') is not False

        started = time.time()
        try:
            if uid:
                db.set_default_uid(uid)
            result = commands.dispatch(command)
            elapsed = int((time.time() - started) * 1000)
            db.log_command(db.get_default_uid(), command, result.ok, elapsed)

            segments: list[dict[str, Any]] = []
            # 命令自己产出的图片段（如扫码登录的二维码）优先
            preset = result.data.get('segments') if isinstance(result.data, dict) else None
            if preset:
                segments.extend(preset)

            render_error = ''
            if want_image and result.ok and result.blocks and not preset:
                try:
                    png = result.render_png()
                    if png:
                        segments.append({
                            'type': 'image',
                            'url': f'/api/media/{os.path.basename(png)}',
                            'alt': result.card_title or command,
                        })
                except Exception as e:  # 出图失败不影响文字结果
                    render_error = f'{type(e).__name__}: {e}'
                    traceback.print_exc()

            summary = result.text
            if render_error:
                summary += f'\n(出图失败，已返回文字: {render_error})'

            self._send(200, {
                'ok': result.ok,
                'title': result.title,
                'summary': summary,
                'lines': result.lines,
                'segments': segments,
                'elapsed': elapsed,
            })
        except Exception as e:  # noqa: BLE001
            elapsed = int((time.time() - started) * 1000)
            detail = f'{type(e).__name__}: {e}'
            traceback.print_exc()
            self._send(200, {
                'ok': False,
                'title': '执行失败',
                'summary': f'❌ {detail}',
                'lines': [],
                'segments': [],
                'elapsed': elapsed,
            })


def serve(port: int = 9778, host: str = '127.0.0.1') -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f'[hsr] 服务已启动 http://{host}:{port}  (version {VERSION})', flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('[hsr] 收到中断，正在退出', flush=True)
    finally:
        httpd.server_close()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='dsh-plugin-hsr 本地服务')
    ap.add_argument('--port', type=int, default=int(os.environ.get('HSR_PORT', 9778)))
    ap.add_argument('--host', default=os.environ.get('HSR_HOST', '127.0.0.1'))
    ap.add_argument('--verbose', action='store_true', help='打印每个请求')
    args = ap.parse_args(argv)

    Handler.quiet = not args.verbose
    serve(args.port, args.host)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
