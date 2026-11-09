# -*- coding: utf-8 -*-
"""1:1 复刻 miao-plugin 的圣遗物评分卡。

CSS 数值全部取自上游，未自行调整：

- ``resources/character/artis-mark.css``
- ``resources/character/profile-detail.css``

关键版式（照抄上游）：

- 容器 660px 宽
- ``.main-pic`` 1400x520（``.game-sr`` 覆盖），``background-size: contain``，
  ``margin-left: -545px`` 居中，于是立绘完整可见、被 660 宽窗口横向裁切
- ``.detail`` 绝对定位在**右上角**，右对齐
- ``.artis`` 是 flex 网格，``.item`` 宽 185px，每行 3 张，``margin-top: -280px``
  压到立绘下半部分上

图片资源走社区库 Mar-7th/StarRailRes（jsDelivr）。
上游的 ``card-bg.png`` 等本地贴图不随本项目分发，这里用等效纯色代替。
"""

from __future__ import annotations

import os
import time
from typing import Any

RES_CDN = 'https://cdn.jsdelivr.net/gh/Mar-7th/StarRailRes@master/'

# 与 miao 一致（profile-detail.css）
GRADE_COLOR = {
    'ACE': '#e85656', 'MAX': '#e85656',
    'SSS': '#ffe699', 'SS': '#ffe699',
    'S': '#d699ff', 'A': '#d699ff',
}

_CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
body {
  width:660px;
  font-family:"Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif;
  font-size:16px; color:#fff;
  background:#191919;
}
.container { width:660px; background:#191919; }
.profile-cont { padding:0 10px; margin-right:5px; }

/* ---------- 立绘 ---------- */
.basic { position:relative; margin:0 -15px 15px -10px; }
.main-pic {
  width:1400px; height:520px;
  background-size:contain; background-repeat:no-repeat; background-position:center;
  margin-left:-545px; position:relative; z-index:2;
}
.detail { position:absolute; right:20px; top:20px; color:#fff; z-index:3; text-align:right; }
.char-name {
  font-size:50px; font-weight:700; text-align:right; letter-spacing:2px;
  text-shadow:0 0 3px #000, 2px 2px 4px rgba(0,0,0,.7);
}
.char-lv { margin-bottom:25px; text-align:right;
  text-shadow:0 0 3px #000, 2px 2px 4px rgba(0,0,0,.7); }
.char-lv .cons { margin-left:5px; vertical-align:bottom;
  display:inline-block; padding:0 6px; border-radius:10px; font-size:14px;
  background:rgba(0,0,0,.45); border:1px solid rgba(255,255,255,.25); }

/* ---------- 评分统计 ---------- */
.arti-stat {
  width:185px; background:rgba(0,0,0,.4);
  box-shadow:0 0 1px 0 #ccc, 2px 2px 4px 0 rgba(50,50,50,.8);
  margin-left:auto;
}
.arti-class-title {
  height:25px; line-height:25px; font-size:12px; text-align:center;
  color:rgba(255,255,255,.9); text-shadow:0 0 2px #000; background:rgba(0,0,0,.5);
}
.arti-stat-ret { height:78px; padding:12px 10px 2px; width:100%; display:table; }
.arti-stat-ret > div { display:table-cell; text-align:center; color:#fff; }
.arti-stat-ret strong { display:block; height:35px; font-size:30px; line-height:32px; font-weight:700; }
.arti-stat span { font-size:12px; line-height:20px; color:#bbb; }

/* ---------- 遗器网格 ---------- */
.artis {
  display:flex; flex-wrap:wrap;
  width:650px; margin:10px -5px 5px;
  margin-top:-280px; position:relative; z-index:3;
}
.artis .item {
  width:185px; border-radius:10px; margin:5px; position:relative;
  /* 上游用 card-bg.png 浅色底衬托遗器图标，这里用等效渐变代替 */
  background:linear-gradient(180deg, #4a4d57 0%, #34373f 55%, #2b2e35 100%);
  box-shadow:0 0 1px 0 #ccc, 2px 2px 4px 0 rgba(50,50,50,.8);
}
.artis .item .arti-icon { width:60px; height:60px; position:absolute; left:2px; top:3px; z-index:2; }
.artis .item .arti-icon .img {
  width:50px; height:50px; margin:5px;
  background-size:contain; background-repeat:no-repeat; background-position:center;
}
.artis .item .arti-icon span {
  position:absolute; right:2px; bottom:0; margin-left:5px;
  background:rgba(0,0,0,.65); border-radius:5px; height:18px; line-height:18px;
  padding:0 3px; color:#fff; font-size:12px;
}
.artis .head { color:#fff; padding:12px 4px 8px 68px; }
.artis .head strong {
  font-size:14px; display:block; white-space:nowrap; overflow:hidden;
  text-overflow:ellipsis; font-weight:700; text-shadow:0 1px 2px rgba(0,0,0,.7);
}
.artis .head span { font-size:14px; }

/* position:static 必须写：上方的 .detail 是绝对定位的角色信息块，
   不加这一条会把遗器里的 ul.detail 也一起拽成绝对定位 */
.artis ul.detail { width:100%; padding:0; list-style:none; position:static; }
/* 上游用 display:table / table-row 布局，在 flex 子项里会高度塌陷，
   这里用等价的 flex 行实现：行高 26px、列宽与上游一致 */
.artis ul.detail li {
  display:flex; align-items:center;
  padding:0 3px; font-size:13px;
  height:24px; line-height:24px; white-space:nowrap;
}
.artis ul.detail li span { color:#fff; }
.artis ul.detail li span.title {
  flex:1; text-align:left; padding-left:5px; font-size:13px;
  overflow:hidden; text-overflow:ellipsis;
}
.artis ul.detail li span.val { text-align:right; padding-right:6px; font-size:13px; }
.artis ul.detail li span.mark {
  width:42px; text-align:right; padding-right:4px; background:rgba(0,0,0,.35);
}
.artis ul.detail li span.mark:after { content:"分"; font-size:11px; }
.artis ul.detail li.arti-main { font-size:15px; font-weight:bold; }
.artis ul.detail li.arti-main span.title { padding-left:5px; font-size:15px; }

.detail.attr li:nth-child(even) { background:rgba(0,0,0,.4); }
.detail.attr li:nth-child(odd) { background:rgba(50,50,50,.4); }
.artis ul.detail li.great span.title { color:#ffe699; }
.artis ul.detail li.nouse span { color:#888; }

.footer { padding:6px 12px 12px; font-size:11px; color:#666; }
"""


def _css_grade(grade: str) -> str:
    return GRADE_COLOR.get(grade.upper(), '#ffffff')


def _fmt_num(value: float, percent: bool = False) -> str:
    """最多一位小数，去掉多余的 .0。"""
    if percent:
        return f'{value:.1f}%'
    r = round(value, 1)
    if abs(r - round(r)) < 1e-9:
        return f'{int(round(r))}'
    return f'{r:.1f}'


def _fmt_val(value: float, percent: bool) -> str:
    return '+' + _fmt_num(value, percent)


def _relic_class(weight: int) -> str:
    if weight >= 80:
        return 'great'
    if weight > 0:
        return ''
    return 'nouse'


def build_artifact_html(char: Any, report: Any, uid: str, footer: str = '') -> str:
    """按 miao 版式生成 HTML。"""
    portrait = f'{RES_CDN}{char.portrait}' if getattr(char, 'portrait', '') else ''
    bg = f"background-image:url('{portrait}')" if portrait else ''
    grade_color = _css_grade(report.grade)
    rank_txt = f'{char.rank}命' if getattr(char, 'rank', 0) else '0命'

    items: list[str] = []
    for pc in report.pieces:
        icon = f'{RES_CDN}{pc.icon}' if pc.icon else ''
        icon_css = f"background-image:url('{icon}')" if icon else ''
        gcls = _css_grade(pc.grade)

        rows: list[str] = []
        main_mark = getattr(pc, 'main_mark_display', 0.0)
        main_score = f'{main_mark:.1f}' if pc.pos >= 3 and main_mark else '-'
        rows.append(
            '<li class="arti-main">'
            f'<span class="title">{pc.main_title}</span>'
            f'<span class="val">{_fmt_num(pc.main_value)}</span>'
            f'<span class="mark">{main_score}</span>'
            '</li>'
        )
        for r in pc.sub_rows:
            lc = _relic_class(r['weight'])
            mark = f"{r['mark_display']:.1f}" if r['weight'] else '-'
            attr = f' class="{lc}"' if lc else ''
            rows.append(
                f'<li{attr}>'
                f'<span class="title">{r["title"]}</span>'
                f'<span class="val">{_fmt_val(r["value"], r["percent"])}</span>'
                f'<span class="mark">{mark}</span>'
                '</li>'
            )

        items.append(
            f'<div class="item arti {pc.pos}">'
            '<div class="arti-icon">'
            f'<div class="img" style="{icon_css}"></div>'
            f'<span>+{pc.level}</span></div>'
            '<div class="head">'
            f'<strong>{pc.name}</strong>'
            f'<span class="mark-{pc.grade}" style="color:{gcls}">'
            f'{pc.score:.1f}分 - {pc.grade}</span>'
            '</div>'
            f'<ul class="detail attr attr-detail">{"".join(rows)}</ul>'
            '</div>'
        )

    foot = footer or '遗器评分 · 权重来自 miao-plugin'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{_CSS}</style></head>
<body><div class="container">
  <div class="profile-cont game-sr">
    <div class="basic">
      <div class="main-pic" style="{bg}"></div>
      <div class="detail">
        <div class="char-name">{char.name}</div>
        <div class="char-lv">UID {uid} - Lv.{char.level}
          <span class="cons cons-{getattr(char, 'rank', 0)}">{rank_txt}</span></div>
        <div class="cont">
          <div class="item arti-stat">
            <div class="arti-class-title">评分规则：{report.title}</div>
            <div class="arti-stat-ret">
              <div><strong style="color:{grade_color}">{report.grade}</strong>
                   <span>圣遗物评级</span></div>
              <div><strong>{report.total:.1f}</strong><span>圣遗物总分</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="artis">
      {''.join(items)}
    </div>
  </div>
  <div class="footer">{foot}</div>
</div></body></html>"""


def render_artifact_card(
    char: Any,
    report: Any,
    uid: str,
    out_dir: str | None = None,
    filename: str | None = None,
    footer: str = '',
) -> str | None:
    """渲染评分卡 PNG。"""
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        return None

    html = build_artifact_html(char, report, uid, footer=footer)
    if out_dir is None:
        out_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'data', 'media',
        )
    os.makedirs(out_dir, exist_ok=True)
    name = filename or f'hsr-arti-{int(time.time() * 1000)}.png'
    path = os.path.join(out_dir, name)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])
            try:
                page = browser.new_page(
                    viewport={'width': 660, 'height': 900},
                    device_scale_factor=2,
                )
                page.set_content(html, wait_until='networkidle', timeout=25000)
                page.wait_for_timeout(350)
                el = page.query_selector('.container') or page
                el.screenshot(path=path)
            finally:
                browser.close()
        return path if os.path.isfile(path) else None
    except Exception:
        return None
