# Camera Database · 相机数据库

仓库：[colorfullife123/camera-database](https://github.com/colorfullife123/camera-database)。
客户端数据库根地址：`https://raw.githubusercontent.com/colorfullife123/camera-database/main/database`。

这是现有苹果内置快捷指令水印项目的数据源。客户端 v1.5.x 通过 GET 检查 `database/manifest.json`，有新版才下载数据库；不发送照片、EXIF 或机型查询参数。

数据库包括厂商别名、厂商图标、准确的型号别名、型号艺术字和按具体机型核实的影像联名关系。所有匹配使用有限的精确键；数据文件不包含可执行代码或在线正则表达式。

## 数据入口

- `database-source.json`：唯一维护入口，含固定尺寸 PNG 的 Base64 数据。
- `database/manifest.json`：很小的当前版本清单。
- `database/database-<revision>.json`：不可变的完整版本文件。
- `artwork-provenance.json`、`ASSET-SOURCES.md`：初始字样与商标来源。
- `tools/database_protocol.py`：仅用 Python 标准库验证并发布数据。

首批版本 `2026110401` 包含 68 个图像素材，沿用 v1.4.0 的 28 个厂商品牌、32 款型号艺术字及已核实联名机型。别名数量不等于独立机型数量。

本版数据 `2026110501` 增加 32 个白底 RGB 型号字样，合计 100 个素材。新增的 `model_rows` 字典供 v1.5.2 的分行拼接流程使用，原始 `model_art` 字段继续保留。

## 发布更新

1. 在 `database-source.json` 中增加或修正条目，并递增整数 `revision`，例如 `2026110502`。
2. 确保艺术字和联名关系有可靠出处。PNG 尺寸固定为 1400 × 220；厂商／联名底图为白底，型号字样为透明叠加层。
3. 生成并检查：

```bash
python3 tools/database_protocol.py --input database-source.json --output database
python3 tools/check_release.py
```

4. 将 `database-source.json`、新增的 `database/database-<revision>.json` 和最后更新的 `database/manifest.json` 一起提交。保留此前发布的版本文件。

客户端校验清单与下载内容的 SHA-256、数据格式、版式和版本，拒绝比缓存更旧的数据。GitHub Actions 会检查素材 PNG、引用、别名及发布内容的一致性。

SHA-256 用来检查下载内容是否与清单一致，信任来源仍是你控制的 GitHub 仓库和 HTTPS；它不是独立的数字签名。不要修改已发布版本的内容，内容变化必须提升 revision。

## 规则格式

- `maker_aliases`：规范化厂商名 → 厂商键。
- `model_brand_aliases`：规范化原始型号 → 厂商键，用于确有依据的特殊厂商归组。
- `brands`：厂商键 → 素材 ID。
- `model_art`：`厂商键/规范化原始型号` → 原始透明字样素材 ID，保留兼容。
- `model_rows`：`厂商键/规范化原始型号` → 白底 RGB 字样素材 ID；同为 1400 × 220，字样位于 y=96～133。新客户端裁取 y=88～147，避免运行时叠放图像。
- `partnerships`：`厂商键/规范化原始型号` → 联名组合素材 ID。
- `partnership_defaults`：用户明确选择 confirmed 模式时使用的组合。
- `assets`：素材 ID → PNG Base64；ID 不带扩展名，也不包含点号或路径分隔符。

规范化：把 `+` 替换为 `plus`，保留英文字母、数字和基本汉字，然后转为小写。例如 `NIKON Z6_3` → `nikonz63`。不同地区的设备代码必须核实后单独加入，不能把品牌全系都视为联名机型。

数据库只能更新识别数据和字样。快捷指令动作、EXIF 读取方式或版式尺寸变化，需要客户端版本更新。
