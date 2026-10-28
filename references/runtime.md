# Windows Codex 运行与验证

## 当前入口与依赖

优先运行本 Skill 的 `scripts/run.ps1`。它先检查当前用户下的 Codex bundled Python：

```text
%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

该文件不存在时才查找 PATH 中的 `python`。运行器为子进程启用 UTF-8，不改全局 PATH 或替换用户 Python。`<skill-dir>` 始终取本次实际加载的 `SKILL.md` 所在目录；不要硬编码某个用户名。

- `doctor` 只检查 Python 及 `reportlab`、`pypdf`、`Pillow` 是否可导入，不证明字体、Poppler、浏览器或最终产物合格。
- PDF 默认使用 Windows Microsoft YaHei／Arial；可通过 renderer 的 `--font-cn`、`--font-cn-bold` 指向经验证支持中文的 TrueType 字体或兼容 TTC。
- `verify --render` 先找当前 Python runtime 配套的 Poppler `native/poppler/Library/bin/pdftoppm.exe`，再查 PATH。未找到就先解决 PDF 渲染依赖。
- 网页检查需要 Node 与 Playwright。`check_web.cjs` 会尝试运行时模块目录、当前 Node 的模块目录及常规模块解析；浏览器先尝试已安装 Edge，再用 Playwright Chromium。

仅补齐本次实际缺少的依赖。其他客户端须根据其技能导入方式、脚本执行能力和可用环境配置；不能由 `SKILL.md` 格式推断全部客户端已兼容。

## 顺序执行

PowerShell 中的尖括号路径需替换为本次真实路径：

```powershell
& '<skill-dir>\scripts\run.ps1' doctor
& '<skill-dir>\scripts\run.ps1' extract --input '<source.pdf>' --output-dir '<work\run>'
& '<skill-dir>\scripts\run.ps1' validate --input '<work\run\notes.json>' --source '<work\run\sentences.json>'
& '<skill-dir>\scripts\run.ps1' render --input '<work\run\notes.json>' --output-dir '<outputs>' --qa-dir '<work\run\qa>'
& '<skill-dir>\scripts\run.ps1' verify --qa-dir '<work\run\qa>' --render
```

extract 只负责提取；在 validate 前须完成逐句撰写与来源核对，不能直接把提取结果当成 notes。render 自动经 `render_notes.py` 调用 `atlas_layout.py`，无需单独执行布局模块。

网页检查另行运行；HTML 路径从 `qa/artifacts.json` 或 renderer 输出读取，不能猜测文件名：

```powershell
node '<skill-dir>\scripts\check_web.cjs' --html '<实际生成的.html>' --qa-dir '<work\run\qa>'
```

若 PATH 无 Node，可使用经确认存在的 bundled Node：

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" '<skill-dir>\scripts\check_web.cjs' --html '<实际生成的.html>' --qa-dir '<work\run\qa>'
```

有其他已验证 Python 环境时，可直接执行对应 `.py`，参数相同。`run.ps1` 的动作仅有 doctor、extract、validate、render、verify，网页检查不通过该运行器分派。

## 脚本与检查范围

| 文件 | 实际职责 |
| --- | --- |
| `extract_sentences.py` | 提取 PDF／TXT，记录来源和待核对情况；扫描件仍需 OCR／视觉核对。 |
| `validate_content.py` | 检查结构、来源覆盖、词汇字段、分组和 glossary 引用，不证明翻译正确。 |
| `render_notes.py` | 解析参数、注册字体、准备共享角色／图形工具并调用新版布局。 |
| `atlas_layout.py` | PLATYPUS PDF、面板和词卡布局、重复表头、题号页眉，以及离线 HTML。 |
| `lexical_resources.py` | 将词条、义项、近义项与辨析完整转成文本表示，不编造近义词。 |
| `grammar_terms.py` | 支持 Grammar 术语显示；原始分析仍须人工核对。 |
| `verify_artifacts.py` | 对照 PDF 正文中的原句、译文、解析、词条与全部近义辨析，检查 HTML 题数，按需生成全部页 PNG 与 contact sheets。 |
| `check_web.cjs` | 拦截外部请求，测试搜索、重置、自测、链接、打印、窄屏及页面错误。 |
| `run.ps1` | 发现 Python 并分派上述 Python 入口。 |

渲染完成后再做提取和视觉检查；不要一边覆盖 PNG 一边拼 contact sheets。QA 中的 `artifacts.json`、`layout_report.json` 和 `rendered_content.json` 是产物核对依据，`verification.json` 记录自动检查结果。

新版用 `KeepTogether` 尽量让词卡同页，以 `Table(repeatRows=1)` 声明重复卡头／表头。遇到超长嵌套行的 `LayoutError` 要检查拆分实现，不能靠截断数据通过。自动完整性检查之外，仍须逐页确认段落接续、词条归属、表头、字体及版面。

新增或修改渲染逻辑后，先用 `assets/example-notes.json` 小样，再用当前真实材料实跑。全部输出留在本次 `work/`／`outputs/`，不要改写演示资产或覆盖其他章节。没有部署步骤；离线文件直接打开。
