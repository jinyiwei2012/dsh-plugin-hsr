# -*- coding: utf-8 -*-
"""命令行查询工具（不依赖 DSH，可直接跑）。

用法::

    python service/tools/query.py 查询
    python service/tools/query.py 练度
    python service/tools/query.py 昔涟面板
    python service/tools/query.py 昔涟遗器
"""

from __future__ import annotations

import os
import sys

_SERVICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _SERVICE)

from hsr.commands import dispatch  # noqa: E402


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    command = ' '.join(argv)
    try:
        res = dispatch(command)
    except Exception as e:  # noqa: BLE001
        print(f'❌ 执行失败：{type(e).__name__}: {e}')
        return 1
    if res.title:
        print(res.title)
    for line in res.lines:
        print(line)
    return 0 if res.ok else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
