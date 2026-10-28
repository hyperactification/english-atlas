# English Atlas｜英語精讀圖譜

将编号式英语句子练习 PDF、图片或文档制作成完整精读笔记，默认输出可打印 PDF 和可搜索、自测、跳转的单文件离线 HTML。

新版让阅读顺序更明确：原句、译文与拆句图先行；结构分析与记忆提示位于左侧，考试提示和易错点位于右侧；每个词条独立成卡，蓝色近义表达与右侧替换限制逐项配对。内容长度决定分页，完整译文、详细解析和近义辨析都会保留。

![English Atlas 精读笔记预览](assets/reference-note.png)

正文 Grammar 术语使用 English，集中提供中英对照与真实例号。适用于考研核心词句及类似整份材料，不用于只翻译一句话或通用文件转换。

## 在 Codex 中安装

仓库地址：[hyperactification/english-atlas](https://github.com/hyperactification/english-atlas)。显示名称为 **English Atlas｜英語精讀圖譜**；为兼容既有调用，安装后的技能目录名及 `SKILL.md` 中的 `name` 仍为 **english-study-notes**，调用仍用 `$english-study-notes`。

可在 Codex 中调用内置安装器，并明确安装名称：

```text
$skill-installer 从 https://github.com/hyperactification/english-atlas 的仓库根目录安装此技能，安装目录名保持 english-study-notes。
```

也可[下载 ZIP](https://github.com/hyperactification/english-atlas/archive/refs/heads/main.zip)，将包含 `SKILL.md`、`scripts`、`references`、`assets`、`agents` 的完整目录放入实际的 Codex skills 目录，并命名为 `english-study-notes`。

本项目当前验证的 Windows Codex 安装位置是 `%USERPROFILE%\.codex\skills\english-study-notes`；其他环境以实际加载的 Skill 目录为准。已有安装不因仓库更名而改技能 ID。

需要本地克隆时，可显式保留目录名：

```powershell
git clone https://github.com/hyperactification/english-atlas.git english-study-notes
```

其他支持 Agent Skills 的客户端可按各自支持的方式导入完整目录；其路径、脚本权限、字体和依赖需自行核验，本仓库不承诺未经验证的全面兼容。

## 使用

```text
$english-study-notes 把附件中的全部句子制作成 English Atlas，完整翻译和详细讲解，突出词条、近义辨析及考点，输出 PDF 和离线互动版。
```

每题保留原题号、来源页码和完整英文，提供自然译文、Sentence structure、Vocabulary、Exam focus、Pitfalls、拆句图与记忆提示；原文用法问题独立列为 Source note。近义表达以本句义项为准，并说明语气、程度、词性或结构差别；没有合适表达时说明原因。

PDF 的长题可续页，页眉保留题号和关键词，长词卡重复词条头。HTML 支持全文／题号搜索、译文遮罩、单句揭晓、重置、章节导航及 Grammar Glossary 例句跳转，可直接离线打开。

## 当前 Windows 运行入口

`<skill-dir>` 替换为实际安装目录，例如当前环境的 `%USERPROFILE%\.codex\skills\english-study-notes`。运行器优先发现当前用户的 Codex bundled Python，再查 PATH：

```powershell
& '<skill-dir>\scripts\run.ps1' doctor
& '<skill-dir>\scripts\run.ps1' extract --input '<source.pdf>' --output-dir '<work\run>'
```

核对原文并撰写本次 `notes.json` 后，依次运行：

```powershell
& '<skill-dir>\scripts\run.ps1' validate --input '<work\run\notes.json>' --source '<work\run\sentences.json>'
& '<skill-dir>\scripts\run.ps1' render --input '<work\run\notes.json>' --output-dir '<outputs>' --qa-dir '<work\run\qa>'
& '<skill-dir>\scripts\run.ps1' verify --qa-dir '<work\run\qa>' --render
node '<skill-dir>\scripts\check_web.cjs' --html '<实际生成的.html>' --qa-dir '<work\run\qa>'
```

Python 依赖为 `reportlab`、`pypdf`、`Pillow`；PDF 视觉检查需要 Poppler，网页检查需要 Node、Playwright 和可用浏览器。`doctor` 只检查 Python 包，不能替代字体、全部页面和实际交互验收。详细入口、依赖与排错见 [runtime.md](references/runtime.md)。

## 目录与脚本

```text
english-study-notes/
├── SKILL.md
├── agents/openai.yaml
├── assets/
│   ├── example-notes.json
│   ├── grammar_glossary.json
│   └── reference-*.png
├── references/
│   ├── content-guide.md
│   ├── design-guide.md
│   ├── schema.md
│   └── runtime.md
└── scripts/
    ├── run.ps1
    ├── extract_sentences.py
    ├── validate_content.py
    ├── render_notes.py
    ├── atlas_layout.py
    ├── lexical_resources.py
    ├── grammar_terms.py
    ├── verify_artifacts.py
    └── check_web.cjs
```

`atlas_layout.py` 实现新版 PDF／HTML 的阅读层级、分区面板和词卡；`lexical_resources.py` 保留词条、语境义、近义项与辨析的文本表示。内容结构见 [schema.md](references/schema.md)，教学边界见 [content-guide.md](references/content-guide.md)，视觉与续页验收见 [design-guide.md](references/design-guide.md)。

## 材料与示例

仓库提供技能指令、辅助脚本、小型演示 JSON 与参考图；示例用于展示数据格式和版式，不代表某一完整教材章节。本仓库不附用户完整源 PDF 或第三方完整学习材料，使用者自行提供有权使用的原始内容。提取、JSON 和 QA 留在本次工作目录，最终交付 PDF 与离线 HTML。
