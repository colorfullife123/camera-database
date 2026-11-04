# 数据库镜像与中国大陆访问

v1.5.3 更新器默认使用 Gcore CDN，另提供 Fastly CDN 与 GitHub 源站。三者是同一仓库的分发入口，共用相同的 SHA-256、格式与版本校验，以及同一份设备缓存。

| 来源 | 数据库根地址 | 使用顺序 |
| --- | --- | --- |
| Gcore CDN | `https://gcore.jsdelivr.net/gh/colorfullife123/camera-database@main/database` | 默认，大陆网络优先尝试 |
| Fastly CDN | `https://fastly.jsdelivr.net/gh/colorfullife123/camera-database@main/database` | Gcore 不通时手动切换 |
| GitHub 源站 | `https://raw.githubusercontent.com/colorfullife123/camera-database/main/database` | 两个 CDN 均不可用或需要较新清单时尝试 |

这是 jsDelivr 的两个 CDN 入口，不是自行部署的中国大陆服务器。可达性取决于所在地、运营商与网络环境，不能保证全国直连；当前执行环境的探测不能代替大陆手机实测。

## 在已有快捷指令中直接改地址

编辑「相机水印数据库更新」，找到开头的「数据库根地址」文本动作，将整段地址替换为上表其中一个根地址，不要加 `/manifest.json` 或末尾斜杠。主水印指令无需修改。

v1.5.3 安装包还提供三个独立更新器：「大陆优先」「Fastly备用」「GitHub源站」。日常自动化只运行其中一个；网络错误时可手动运行另一个，成功后将日常自动化改用可用的更新器。

内置「获取 URL 内容」发生网络错误会终止当前快捷指令，因此本版不宣称自动故障切换。三个更新器写入同一缓存，使用相同的先验证后保存流程。断网时继续用已有缓存或内置数据制作照片。

## 更新延迟与一致性

按 [jsDelivr 官方说明](https://github.com/jsdelivr/jsdelivr#caching)，分支文件的 CDN 缓存为 12 小时；手机及中间缓存也可能影响刷新时间。刚发布的数据库可能暂时在不同入口显示不同版本。版本文件一经发布不应修改；清单仅指向该版本的数据文件。若清单与数据未同步、下载失败或校验不符，更新器不会覆盖当前缓存。

镜像不是额外的信任根：HTTPS 和你控制的 GitHub 仓库仍是来源信任基础。SHA-256 检查下载内容与所取清单的一致性，不是独立数字签名；没有第三方脚本或在线执行代码。

## 维护与检查

`update-sources.json` 是本项目的源配置。手机更新器将这些地址固化在工作流内，不会在运行时从网络读取任意新地址。

```bash
python3 tools/check_release.py
python3 tools/check_mirrors.py --catalog-only
python3 tools/check_mirrors.py --output mirror-check.json
```

在线检查会从三个入口各取清单及其版本数据，验证文件名、包格式、版本绑定、素材和 SHA-256。失败时返回非零状态；镜像比仓库落后时明确报告警告。它不更新设备文件，也不清除 CDN 缓存。GitHub Actions 的 `Check database mirrors` 工作流每天运行两次，发布相关文件或手动触发时也运行。
