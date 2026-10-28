# 跨平台运行与验证

## 环境与路径

`<skill-dir>` 指实际加载的 `SKILL.md` 所在目录。以下命令在该目录执行，示例路径须替换为本次真实位置；路径含空格时加引号。使用 Python 3.10+，根据环境将 `python` 换成 `python3` 或解释器的绝对路径。

```sh
python -m pip install -r requirements.txt
python scripts/run.py doctor
```

依赖为 `reportlab`、`pypdf`、`Pillow`。可使用已有的满足依赖的解释器或项目虚拟环境。`run.py` 使用启动它的 Python，脚本与资源按 Skill 自身位置解析；不要求专有宿主的 Python 安装位置。

PDF 提取可使用 Poppler `pdftotext`；PDF 页面渲染需要 `pdftoppm`。优先读取环境变量 `PDFTOTEXT`／`PDFTOPPM` 指定的可执行文件，再查 PATH，最后检查当前解释器附近的可用工具目录。安装 Poppler 后，将其可执行文件目录加入当前执行环境 PATH，或显式配置上述变量。

`doctor` 提供环境诊断；其通过不能代替来源核对、全部页面的视觉检查和浏览器实际验收。本项目已经在 Windows 上实跑；macOS／Linux 的运行入口和发现逻辑尚未经过原生系统验证。

## 字体

渲染器尝试发现 Windows、macOS 和 Linux 常见字体位置及可用 fontconfig 字体。中文字体须覆盖材料中的汉字，并具有 ReportLab 可嵌入的 TrueType outlines；使用 `.ttf` 或兼容的 `.ttc`。带 CFF outlines 的 OpenType 字体不能直接用于本渲染器，扩展名本身不能证明可用。

显式指定字体时，命令行参数优先于对应环境变量：

| 命令行参数 | 环境变量 | 用途 |
| --- | --- | --- |
| `--font-cn` | `ENGLISH_ATLAS_FONT_CN` | 中文常规字体 |
| `--font-cn-bold` | `ENGLISH_ATLAS_FONT_CN_BOLD` | 中文粗体 |
| `--font-en` | `ENGLISH_ATLAS_FONT_EN` | English 常规字体 |
| `--font-en-bold` | `ENGLISH_ATLAS_FONT_EN_BOLD` | English 粗体 |

```sh
python scripts/run.py render --input work/run/notes.json --output-dir outputs --qa-dir work/run/qa --font-cn /path/to/chinese-regular.ttf --font-cn-bold /path/to/chinese-bold.ttf
```

Windows 可选已安装的 Microsoft YaHei；其他系统可安装具有 TrueType outlines 的中文字体并显式指定。首次使用新字体时，检查 PDF 中的中文、English 单词边界、标点和箭头。遇到不兼容字体应更换或正确配置字体，不能靠省略字符、改译文或删内容通过。

## 内容到产物

```sh
python scripts/run.py extract --input source.pdf --output-dir work/run
```

`extract` 只提取来源，不执行 OCR、翻译或教学分析。读取报告并逐句核对后，按照 [schema.md](schema.md) 撰写完整 `work/run/notes.json`，再继续：

```sh
python scripts/run.py validate --input work/run/notes.json --source work/run/sentences.json
python scripts/run.py render --input work/run/notes.json --output-dir outputs --qa-dir work/run/qa
python scripts/run.py verify --qa-dir work/run/qa --render
```

`render_notes.py` 自动调用 `atlas_layout.py`，不用单独执行布局模块。每个 `.py` 也可直接执行，参数保持一致。PowerShell 用户可选用 `scripts/run.ps1` 分派相同的五个动作；通用工作流程使用 `run.py`。

## 离线 HTML 检查

需要 Node.js、Playwright 和可用 Chromium 浏览器。在可写的测试环境安装依赖；若宿主已有这些工具，可直接使用：

```sh
npm install --no-save playwright
npx playwright install chromium
node scripts/check_web.cjs --html outputs/actual-output.html --qa-dir work/run/qa
```

HTML 的实际路径从 renderer 输出或 `qa/artifacts.json` 读取。模块使用标准 Node 解析规则；环境预装依赖可通过 `NODE_PATH` 提供，多个路径使用系统分隔符。默认尝试 Playwright Chromium，并可回退到可用系统浏览器。需指定浏览器时使用下列方式之一：

```sh
node scripts/check_web.cjs --html outputs/actual-output.html --qa-dir work/run/qa --browser-channel msedge
node scripts/check_web.cjs --html outputs/actual-output.html --qa-dir work/run/qa --browser-executable /path/to/chromium
```

对应环境变量为 `ENGLISH_ATLAS_BROWSER_CHANNEL`、`ENGLISH_ATLAS_BROWSER_EXECUTABLE`。检查器测试外部请求、搜索、重置、自测、链接、打印、窄屏与页面错误。有其他浏览器工具的宿主可完成等效检查，并准确记录实际检查范围。

## 检查范围与排版排错

| 文件 | 职责 |
| --- | --- |
| `run.py` | 通用环境诊断与 Python 脚本分派。 |
| `extract_sentences.py` | PDF／TXT 提取、来源记录和待核对报告。 |
| `validate_content.py` | 内容结构、来源覆盖、词汇字段、分组和 glossary 引用检查。 |
| `render_notes.py` | 参数、字体与共享图形设置，调用布局模块。 |
| `atlas_layout.py` | PDF／HTML 版式、面板、词卡、续页标识与交互内容。 |
| `lexical_resources.py` | 完整保留词条、语境义、近义项和辨析的文本表示。 |
| `grammar_terms.py` | Grammar 术语显示转换。 |
| `verify_artifacts.py` | 对照全部正文，检查题数，按需生成全部页 PNG 与 contact sheets。 |
| `check_web.cjs` | 离线网页的实际交互与窄屏检查。 |

QA 的 `artifacts.json`、`layout_report.json`、`rendered_content.json` 是产物核对依据；`verification.json` 记录自动检查。渲染完成后再检查 PNG 与 contact sheets，避免读取尚在被覆盖的图片。

检查相邻首页与续页的密度，尤其是少量词卡被挤到下一页的情况。以完整面板、词卡或可读段落为单位重新分配，保持正常字号、行距与完整内容；不固定每题两页。超长卡或嵌套表格触发 `LayoutError` 时，检查拆分和重复表头实现。自动完整性检查后仍须逐页确认文字接续、词条归属、字体、箭头和版面。

修改渲染逻辑后，先用 `assets/example-notes.json` 小样，再用当前真实材料验证。产物放在本次独立 `work/`／`outputs/`，不改写演示资产或其他章节。离线交付无需部署。