# 河南高考志愿填报系统

> 河南 2026 年新高考物理类志愿草表 · 冲稳保三段编排 · 多端同步 · 数据驱动的填报辅助工具

---

## 功能介绍

### 核心能力

- **志愿组管理**：支持最多 48 个院校专业组，每组最多 6 个正式专业 + 不限量备选专业，完全对齐河南省 2026 年普通本科批平行志愿规则
- **三段策略编排**：内建"冲 · 稳 · 保"三层分类，配合拖拽排序直观调整 1—48 号志愿优先级——投档顺序直接决定录取结果
- **历年录取参考**：每个专业组和专业均可录入近三年最低录取分与位次，系统自动对比考生位次分析冲稳保风险；内置一分一段表支持分数与位次双向换算
- **智能数据获取**：集成河小阳 API 自动查询院校录取分数；支持从阳光高考 / 招生考试网复制表格数据后"智能粘贴"一键解析填入
- **国标代码搜索**：支持按院校国标代码搜索并批量填入历史录取数据
- **PDF 专业组级投档线修正**：支持读取 PDF 版投档线数据，自动匹配修正已有志愿组

### 编辑与查看

- **可视化编辑**：精美的纸质杂志风格 UI，志愿组卡片式管理，专业拖拽排序
- **显示/隐藏切换**：每组可单独设为隐藏（草稿阶段暂时搁置），隐藏组在查看模式中灰显且不参与序号
- **查看模式**：一键切换只读视图，自动排版为正式志愿表样式，支持浏览器原生打印
- **导出**：支持导出为 JSON（完整数据备份）、高质量 PNG 图片、PDF 文档

### 多端同步

- **本地服务器架构**：同一局域网内手机、平板、其他电脑打开同一地址即可自动同步，适合家庭多人协作填报
- **版本化同步**：基于时间戳的版本比对，仅传输变更数据
- **密码鉴权**：Session + Cookie 机制，72 小时有效期，保护隐私数据

### 导入 / 导出 / 互操作

- **JSON 导入**：支持完整结构（含考生信息）和纯专业组数组两种格式，支持替换或追加模式
- **大模型友好**：内置"导入格式说明"面板，含完整 JSON Schema、字段说明表、可直接发送给大模型的提示词模板——让 AI 帮你生成志愿方案后一键导入
- **数据便携**：所有数据以本地 JSON 文件存储，可随时备份、迁移

---

## 项目结构

```
gaokao/
├── server.go                  # Go 后端服务器（纯标准库，零依赖）
├── server_linux               # 预编译的 Linux amd64 二进制
├── volunteer_form.html         # 前端单页应用（志愿表编辑器）
├── go.mod                      # Go module 定义
├── data/
│   ├── score_rank_map.js       # 一分一段表（内置，分数↔位次换算）
│   ├── all_schools_data.json   # 全量院校录取数据
│   └── volunteer_data_current.json  # 当前志愿数据（运行时）
├── tools/
│   ├── fetch_scores.py         # 河小阳 API 自动查询录取分数
│   ├── scrape_all.py           # 全量爬取院校录取数据
│   ├── scrape_school.py        # 单校数据爬取
│   ├── match_and_update.py     # 批量匹配更新录取数据
│   ├── final_match.py          # 最终匹配工具
│   ├── pdf_correct.py          # PDF 投档线数据解析与修正
│   ├── parse_score.py          # 分数解析 v1
│   └── parse_score_v2.py       # 分数解析 v2
└── .gitignore
```

---

## 快速部署

### 前置条件

- **Go 1.24+**（仅从源码运行时需要；也可直接使用预编译二进制）
- 或 **Python 3.10+**（仅数据爬取工具需要）

### 方式一：直接运行（推荐）

**Windows：**
```powershell
# 下载预编译的 server_linux 或从源码编译
go build -o server.exe server.go
.\server.exe -addr :8080 -password 你的密码
```

**Linux / macOS：**
```bash
# 使用预编译二进制
chmod +x server_linux
./server_linux -addr :8080 -password 你的密码

# 或从源码运行
go run server.go -addr :8080 -password 你的密码
```

**通过环境变量设置密码（更安全）：**
```bash
export PASSWORD=你的密码
go run server.go -addr :8080
```

### 方式二：后台运行（Linux）

```bash
nohup ./server_linux -addr :8080 -password 你的密码 > server.log 2>&1 &
```

或使用 systemd：

```ini
# /etc/systemd/system/gaokao.service
[Unit]
Description=河南高考志愿填报系统
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/gaokao
Environment=PASSWORD=你的密码
ExecStart=/path/to/gaokao/server_linux -addr :8080
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gaokao
```

### 启动参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `-addr` | `:8080` | HTTP 监听地址 |
| `-password` | `gaokao2026` | 访问密码（也可通过 `PASSWORD` 环境变量设置） |
| `-data` | `volunteer_data.json` | 数据文件路径 |

### 访问

启动后终端会打印局域网地址，在浏览器打开即可：
- 本机：`http://localhost:8080`
- 局域网：`http://<你的IP>:8080`（手机/平板可扫码或直接输入）

---

## 数据工具使用

```bash
# 查询单个院校录取数据
python tools/fetch_scores.py

# 全量爬取所有目标院校
python tools/scrape_all.py

# 批量匹配更新到志愿表
python tools/match_and_update.py

# 用 PDF 专业组级投档线修正数据
python tools/pdf_correct.py
```

---

## 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 后端 | Go 1.24 | 纯标准库，零外部依赖 |
| 前端 | 原生 HTML/CSS/JS | 单页应用，SortableJS + html2canvas + jsPDF |
| 数据 | JSON 文件存储 | 版本化同步，无需数据库 |
| 工具链 | Python 3 | 数据爬取、解析、匹配 |

---

## 志愿填报规则摘要

本系统严格遵循河南省 2026 年普通本科批规则：

1. **志愿单位**：1 个院校专业组 = 1 个志愿，可填 1—48 个
2. **组内专业**：每组设 6 个专业 + 是否服从调剂，调剂仅限组内
3. **投档原则**：分数优先、遵循志愿、一轮投档——1—48 号顺序决定录取
4. **排序策略**：前段"冲"、中段"稳"、后段"保"，保底位次建议低于考生位次 1 万名以上

> ⚠️ 本系统为志愿草表工具，用于模拟编排与排序练习。正式填报请登录「河南省普通高校招生考生服务平台」([pzwb.haeea.cn](https://pzwb.haeea.cn))。

---

## 大模型工具部署指南

> 以下为供大模型 / AI 编程工具（Claude Code、Cursor、Copilot 等）专属读取的精简部署说明，方便直接执行部署操作。

```markdown
# 河南高考志愿填报系统 · 部署指令

## 项目概述
- 语言：Go 1.24（后端）+ 原生 HTML/CSS/JS（前端）
- 依赖：零外部依赖（Go 标准库即可）
- 数据存储：本地 JSON 文件
- 入口文件：server.go

## 部署步骤

### 1. 编译后端
\`\`\`bash
cd /path/to/gaokao
go build -o server server.go
\`\`\`

### 2. 启动服务
\`\`\`bash
# 基础启动（密码默认 gaokao2026）
./server -addr :8080

# 自定义密码
./server -addr :8080 -password "你的密码"

# 或通过环境变量
PASSWORD=你的密码 ./server -addr :8080
\`\`\`

### 3. 验证
浏览器打开 http://localhost:8080，输入密码即可使用。

### 端口与防火墙
- 默认监听 :8080
- 如需局域网访问，确保防火墙放行对应端口

### 数据文件
- 数据默认存储在 ./volunteer_data.json
- 可通过 -data 参数指定路径

### 多端同步
- 同一局域网内多设备访问同一服务器地址即可自动同步
- Session 有效期 72 小时

## 关键文件
| 文件 | 用途 |
|------|------|
| server.go | 后端入口，HTTP API + 静态文件服务 |
| volunteer_form.html | 前端单页应用 |
| data/score_rank_map.js | 一分一段表（分数位次换算） |
| data/volunteer_data_current.json | 当前志愿数据 |
| tools/*.py | Python 数据爬取/匹配工具 |

## API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth | 密码验证，返回 session token |
| GET | /api/check | 检查登录状态 |
| GET | /api/data?version=xxx | 获取志愿数据（支持版本比对 304） |
| POST | /api/data | 保存志愿数据 |
| GET | / | 前端页面 |

## 注意事项
- 默认密码 gaokao2026，生产使用务必修改
- HTTPS 未内置，建议配合 nginx/caddy 反向代理
- 数据文件包含隐私信息，请妥善保管
```
