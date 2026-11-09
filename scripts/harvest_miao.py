# -*- coding: utf-8 -*-
"""从 miao-plugin 抓取星铁核心数据，生成 Python 模块。

来源（MIT）:
  https://github.com/yoimiya-kokomi/miao-plugin
    resources/meta-sr/artifact/artis-mark.js   词条权重表
    resources/meta-sr/artifact/calc.js         套装数值
    resources/meta-sr/artifact/meta.json       词条定义

产物写入 service/hsr/data/。
用法: python scripts/harvest_miao.py
"""
from __future__ import annotations

import json
import os
import re
import urllib.request

BASE = 'https://raw.githubusercontent.com/yoimiya-kokomi/miao-plugin/master/'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Accept': '*/*'}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, 'service', 'hsr', 'data')
os.makedirs(OUTDIR, exist_ok=True)


def fetch(path: str, timeout: int = 40) -> str:
    req = urllib.request.Request(BASE + path, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'ignore')


def log(msg: str) -> None:
    print(msg, flush=True)


def balanced_block(src: str, open_idx: int) -> str:
    """从 open_idx 处的 '{' 开始，返回配对完整的块。"""
    depth = 0
    for i in range(open_idx, len(src)):
        c = src[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return src[open_idx:i + 1]
    raise ValueError('括号不配对')


def js_obj_to_py(text: str) -> str:
    """把 JS 对象字面量粗转成 JSON 文本。"""
    # 去掉 // 行注释和 /* */ 块注释（先于引号处理，避免误伤）
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    text = re.sub(r'(?m)^\s*//.*$', '', text)
    text = re.sub(r'\s//[^\n"\']*$', '', text, flags=re.M)
    # 裸键 -> 带引号
    text = re.sub(
        r'([{,]\s*)([A-Za-z_\u4e00-\u9fa5][\w\u4e00-\u9fa5•·.\-]*)\s*:',
        r'\1"\2":',
        text,
    )
    # 单引号字符串 -> 双引号
    text = re.sub(r"'([^']*)'", lambda m: '"' + m.group(1).replace('"', '\\"') + '"', text)
    text = text.replace(': true', ': true').replace(': false', ': false')
    # 尾随逗号
    text = re.sub(r',\s*([}\]])', r'\1', text)
    return text


# ---------------------------------------------------------------- 词条权重表
def harvest_useful_attr() -> int:
    log('[1/3] artis-mark.js -> useful_attr.py')
    src = fetch('resources/meta-sr/artifact/artis-mark.js')
    m = re.search(r'export\s+const\s+usefulAttr\s*=\s*\{', src)
    if not m:
        raise SystemExit('找不到 usefulAttr')
    block = balanced_block(src, src.index('{', m.start()))
    data = json.loads(js_obj_to_py(block))
    data = {k: v for k, v in data.items() if isinstance(v, dict)}
    log(f'    角色数 = {len(data)}')

    lines = [
        '# -*- coding: utf-8 -*-',
        '"""星铁遗器词条权重表。',
        '',
        '自动生成，请勿手工编辑。来源：',
        '  miao-plugin/resources/meta-sr/artifact/artis-mark.js',
        '  https://github.com/yoimiya-kokomi/miao-plugin  (MIT)',
        '',
        '权重含义：0 = 无用，50 = 次要，75 = 有用，100 = 核心。',
        '',
        '字段说明：',
        '  hp      生命值 / 生命%',
        '  atk     攻击力 / 攻击%',
        '  def     防御力 / 防御%',
        '  speed   速度',
        '  cpct    暴击率',
        '  cdmg    暴击伤害',
        '  stance  击破特攻',
        '  heal    治疗量加成',
        '  recharge 能量恢复效率',
        '  effPct  效果命中',
        '  effDef  效果抵抗',
        '  dmg     属性伤害加成',
        '"""',
        '',
        'from __future__ import annotations',
        '',
        'USEFUL_ATTR: dict[str, dict[str, int]] = {',
    ]
    for name in sorted(data):
        v = data[name]
        parts = ', '.join(f'"{k}": {int(v[k])}' for k in v if isinstance(v[k], (int, float)))
        lines.append(f'    "{name}": {{{parts}}},')
    lines += [
        '}',
        '',
        '',
        'def get_useful_attr(char_name: str) -> dict[str, int]:',
        '    """取角色词条权重；未收录返回空 dict。"""',
        '    return USEFUL_ATTR.get(char_name) or {}',
        '',
    ]
    out = os.path.join(OUTDIR, 'useful_attr.py')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    log(f'    写入 {out}')
    return len(data)


# ---------------------------------------------------------------- 套装数值
def harvest_sonata() -> int:
    log('[2/3] calc.js -> sonata_effects.py')
    src = fetch('resources/meta-sr/artifact/calc.js')
    m = re.search(r'export\s+default\s*\{', src)
    if not m:
        raise SystemExit('找不到 default export')
    block = balanced_block(src, src.index('{', m.start()))
    log(f'    套装块 {len(block)} chars')

    # 形如  `套装名: {`  且缩进 2 空格
    names = re.findall(r'^\s{2}([\u4e00-\u9fa5A-Za-z0-9•·.\-]+)\s*:\s*\{', block, re.M)
    log(f'    套装数 = {len(names)}')

    # 解析每套的 2 件 / 4 件数值：attr('key', value) 形式
    # 结构: 套装名: { 2: attr('heal', 10), 4: [...] }
    entries: dict[str, dict[str, object]] = {}
    for name in names:
        pos = block.find(f'\n  {name}: {{')
        if pos < 0:
            pos = block.find(f'{name}: {{')
        if pos < 0:
            continue
        sub = balanced_block(block, block.index('{', pos))
        setinfo: dict[str, object] = {}
        # 2件: attr('x', n)
        m2 = re.search(r'2\s*:\s*attr\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*(-?[\d.]+)\s*\)', sub)
        if m2:
            setinfo['two'] = {m2.group(1): float(m2.group(2))}
        # 4件: attr(...) 或 数组/对象
        m4 = re.search(r'4\s*:\s*attr\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*(-?[\d.]+)\s*\)', sub)
        if m4:
            setinfo['four'] = {m4.group(1): float(m4.group(2))}
        else:
            m4b = re.search(r'4\s*:\s*\[?\s*attr\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*(-?[\d.]+)\s*\)', sub)
            if m4b:
                setinfo['four'] = {m4b.group(1): float(m4b.group(2))}
        if setinfo:
            entries[name] = setinfo

    log(f'    解析出数值的套装 = {len(entries)}')

    lines = [
        '# -*- coding: utf-8 -*-',
        '"""星铁遗器套装数值加成（仅可静态结算的部分）。',
        '',
        '自动生成，请勿手工编辑。来源：',
        '  miao-plugin/resources/meta-sr/artifact/calc.js',
        '  https://github.com/yoimiya-kokomi/miao-plugin  (MIT)',
        '',
        '只收录「常驻无条件」的数值型效果；条件型效果（需命中/入场等触发）',
        '不参与面板计算，因此不在本表中。',
        '"""',
        '',
        'from __future__ import annotations',
        '',
        'SONATA_EFFECTS: dict[str, dict[str, dict[str, float]]] = {',
    ]
    for name in sorted(entries):
        v = entries[name]
        parts = []
        for piece in ('two', 'four'):
            if piece in v:
                d = v[piece]
                kv = ', '.join(f'"{k}": {val}' for k, val in d.items())
                parts.append(f'"{piece}": {{{kv}}}')
        lines.append(f'    "{name}": {{{", ".join(parts)}}},')
    lines += [
        '}',
        '',
        '',
        'def get_sonata_effect(set_name: str, count: int) -> dict[str, float]:',
        '    """返回该套装在 count 件时生效的数值加成。"""',
        '    entry = SONATA_EFFECTS.get(set_name) or {}',
        '    out: dict[str, float] = {}',
        '    if count >= 2:',
        '        out.update(entry.get("two") or {})',
        '    if count >= 4:',
        '        out.update(entry.get("four") or {})',
        '    return out',
        '',
    ]
    out = os.path.join(OUTDIR, 'sonata_effects.py')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    log(f'    写入 {out}')
    return len(entries)


# ---------------------------------------------------------------- 词条定义
def harvest_attr_map() -> int:
    log('[3/3] artifact/meta.json -> artifact_meta.json')
    try:
        meta = json.loads(fetch('resources/meta-sr/artifact/meta.json'))
    except Exception as e:
        log(f'    ERR {e}')
        return 0
    with open(os.path.join(OUTDIR, 'artifact_meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    am = meta.get('attrMap') or {}
    log(f'    attrMap 词条数 = {len(am)}')
    return len(am)


if __name__ == '__main__':
    n1 = harvest_useful_attr()
    n2 = harvest_sonata()
    n3 = harvest_attr_map()
    log('')
    log(f'完成：权重表 {n1} 角色 / 套装 {n2} 套 / 词条 {n3} 条')
    for fn in sorted(os.listdir(OUTDIR)):
        p = os.path.join(OUTDIR, fn)
        log(f'  {fn}  {os.path.getsize(p)}B')
