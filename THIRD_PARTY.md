# 第三方来源声明

本项目 MIT 授权，见 [LICENSE](LICENSE)。以下部分衍生自其他项目或涉及第三方权利。

---

## miao-plugin

遗器评分算法与词条权重表移植自 **miao-plugin**：

    miao-plugin — https://github.com/yoimiya-kokomi/miao-plugin
    Copyright (c) Yoimiya-Kokomi
    Licensed under the MIT License.

具体对应关系：

| 本源文件 | 上游文件 |
|---|---|
| `service/hsr/core/artifact.py` | `models/artis/ArtisMark.js` + `models/artis/ArtisMarkCfg.js` |
| `service/hsr/data/useful_attr.py` | `resources/meta-sr/artifact/artis-mark.js` |
| `service/hsr/data/sonata_effects.py` | `resources/meta-sr/artifact/calc.js`（仅静态数值部分） |
| `service/hsr/data/attr_meta.py` | `resources/meta-sr/artifact/meta.js` |

`useful_attr.py` 与 `sonata_effects.py` 由 `scripts/harvest_miao.py` 自动生成，
未做手工改动。

---

## 游戏数据与商标

《崩坏：星穹铁道》及其角色、光锥、遗器等名称与数据版权归
**miHoYo / HoYoverse** 所有。

本项目是非官方粉丝工具，与游戏发行商无任何隶属关系，不包含也不分发游戏美术资源。

---

## 接口

- **mihomo**（<https://api.mihomo.me>）：第三方维护的公开展柜数据接口，无需登录。
- **米游社战绩接口**（`api-takumi-record.mihoyo.com`）：官方前端使用的接口，
  非公开文档化。本项目按其前端行为构造请求，仅用于查询用户自己的账号数据。

使用第三方接口时请遵守对应服务条款。本项目不鼓励高频请求或批量抓取。
