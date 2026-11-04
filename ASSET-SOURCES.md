# Asset sources

The trademarks identify the camera manufacturer in a personal photo watermark. No endorsement is implied.

- Nikon: official full brand symbol, downloaded from https://www.nikon-image.com/common2/img/mod-header/logo_01.svg on 2026-11-02. Brand reference: https://www.nikon.com/company/corporate/brand/brand_symbol/
- Canon: official wordmark, downloaded from https://global.canon/01cmn/img/common/logo.svg on 2026-11-02. Converted to monochrome for contrast.
- Sony, Fujifilm, Panasonic, Leica, DJI, Apple: vector outlines from the Simple Icons 11.15.0 package, `icons/<brand>.svg`, obtained from https://cdn.jsdelivr.net/npm/simple-icons@11.15.0/icons/ on 2026-11-02. Source project: https://github.com/simple-icons/simple-icons . These outlines are rendered as monochrome PNGs for offline use. Trademarks remain the property of their respective owners.
- Preview backdrop: procedural landscape drawn specifically to demonstrate the layout; it is not a photograph supplied by the user.

No remote font, image or rendering service is required at runtime.

## v1.3.0 additional manufacturer assets

- Smartphone and Insta360 outlines: Simple Icons 11.15.0, https://cdn.jsdelivr.net/npm/simple-icons@11.15.0/icons/ .
- Hasselblad, Pentax, Olympus and OM SYSTEM: Wikimedia Commons files Hasselblad logo.svg, Pentax wordmark.svg, Olympus Corporation logo.svg, OMDS OM-System-Logo.svg.
- Ricoh: https://www.ricoh.com/-/Media/Ricoh/Common/cmn_g_header_footer/img/logo/logo.svg
- realme: https://image01.realme.net/general/20181218/1545105227803.png
- ZTE: https://www.zte.com.cn/content/dam/zte-site/res-www-zte-com-cn/navigator/global/main/img/logo-en.png

Original vector colors and internal white details are preserved. All marks are embedded in local PNG footer assets.

## v1.4.0 official model lettering and partnerships

Individual source URLs, source SHA-256 values, original model names, and exact matching rules are stored in `artwork-provenance.json`. Nikon model artwork comes from the heading graphics on imaging.nikon.com. Fujifilm X-T5 artwork is extracted from page 1 of the official X-T5 brochure at https://dl.fujifilm-x.com/ja-jp/products/brochure/x-t5_catalogue_rzpr6.pdf . Apple model wordmark vectors are mirrored by Wikimedia Commons with Apple attributed as the original author. Xiaomi 14 title graphics come from the official appmifile.com product CDN. Artwork is rendered in monochrome while retaining its original letter contours.

ZEISS mark: https://commons.wikimedia.org/wiki/File:Zeiss_logo.svg . Leica and Hasselblad marks reuse the credited embedded manufacturer assets. Paired headers are local layout compositions, not new official joint logos. Partnership references are attached to each finite model rule in the style catalog.

## v1.5.0 数据库传输

本版沿用 v1.4.0 的商标和型号字样素材，将它们封装为可离线缓存的数据文件。数据库中没有照片、EXIF 或可执行代码。当前在线版本见 `database/manifest.json`。数据库自身维护工具只依赖 Python 标准库；手机处理和更新只使用苹果内置 App。

## v1.5.2 白底型号字样

ModelRow-*.png 由已列明来源的 ModelArt-*.png 与纯白背景合成，输出不含透明通道的 RGB PNG。字样轮廓沿用原素材，供原生裁切与拼接动作使用，手机无需安装额外 App。
