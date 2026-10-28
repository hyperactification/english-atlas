---
name: english-study-notes
description: 将编号式英语句子练习 PDF、图片或文档制作成 English Atlas 英語精讀圖譜：完整翻译、拆句、词汇语境义与逐项近义辨析、考点及易错点，默认交付可打印 PDF 和可搜索、自测、跳转的离线 HTML。适用于考研核心词句及类似整份材料，不用于仅翻译一句话或通用格式转换。
---

# English Atlas｜英語精讀圖譜

复用阅读层级和工作方法，重新分析用户本次材料。章节、题数、主题图与 Grammar Glossary 均从来源推导。保留完整内容；用户当次指定的范围、语言和格式优先。

## 输出与阅读层级

- 默认交付可搜索、复制的 A4 PDF，以及单文件离线 HTML；中文字体嵌入 PDF。
- 每题先呈现原题号、来源页码、简短 `keyword`、完整原句、完整译文和拆句图。随后左侧放 Sentence structure 与 Memory key，右侧放 Exam focus 与 Pitfalls，使用可区分的浅底面板。
- Vocabulary 每项独立成卡：大字词条头 → 本句 Context 义项与搭配 → 左侧蓝色 Near synonyms、右侧中性色差别与替换限制。整卡尽量同页，长卡正常续页并重复词条头；单题续页重复题号与关键词。不能为视觉删内容或缩小文字硬塞一页。
- 正文解释用中性色，近义表达用蓝色，考试提示用琥珀色，警告用红色。Grammar 角色配色只在原句及拆句图中表示句法或明确的逻辑关系，不能给整段说明套角色色。
- 正文 Grammar 术语和图示角色用 English；集中 Grammar Glossary 提供 English、中文名称、中文解释及本次真实例号。HTML 支持题号／全文搜索、译文自测与单句揭晓、章节导航及术语例句跳转。

详细版式、续页和视觉验收见 [design-guide.md](references/design-guide.md)；预览见 [reference-note.png](assets/reference-note.png)。

## 工作流程

1. **取得并核对来源。** 读取本次实际附件；若只有可见文件名，先在当前工作区和常用下载位置按准确名称做有限查找，仍不可访问才索取路径。PDF／TXT 可用 `extract_sentences.py`；扫描件先 OCR／视觉转录。保留 `raw`、题号、页码，核对缺号、双句、跨页及括注。
2. **撰写内容。** 读 [content-guide.md](references/content-guide.md) 和 [schema.md](references/schema.md)，建立本次 `notes.json`。逐句还原结构，再写完整译文、词汇和考点。近义词须贴合本句义项；词性或替换结构变化明确说明，无适当表达时写原因。示例 JSON 与 glossary 仅供结构参考，答案和例号不套用。
3. **保留语言边界。** 不扩大 can／should、否定、数量或条件；to do 不自动证明目标已实现。原句保持来源文字，用法瑕疵与建议另放 `source_note`。`diagram.text` 来自原句，节选显式省略；Purpose、Condition 等不得一律标成 Object。
4. **验证与渲染。** 用 `validate_content.py --input notes.json --source sentences.json` 检查覆盖与结构，再用 `render_notes.py` 调用新版 `atlas_layout.py` 输出 PDF＋HTML。词义图只选语义匹配的内置图，或提供本次的 `illustration.primitives`。
5. **实际验收。** 用 `verify_artifacts.py --render` 对照全部段落并渲染所有页；检查全册缩略图、密集页和所有续页词卡。用 `check_web.cjs`／浏览器实际验证离线内容、搜索、自测、跳转与窄屏。结构校验通过不等于英语正确或版面合格；修复后重跑受影响检查。
6. **交付文件。** 链接最终 PDF 与 HTML，报告实际题数和页数。工作 JSON、提取与 QA 留在本次 `work/`；不覆盖 Skill 的演示资产或其他章节。

## 当前 Windows 入口

`<skill-dir>` 是本次实际加载的 `SKILL.md` 所在目录：

```powershell
& '<skill-dir>\scripts\run.ps1' doctor
& '<skill-dir>\scripts\run.ps1' render --input '<work\notes.json>' --output-dir '<outputs>' --qa-dir '<work\qa>'
```

尖括号表示需替换的路径。完整命令、依赖发现与排错见 [runtime.md](references/runtime.md)。不能用省略内容处理字体或 LayoutError，也不能把未检查的输出声称为已验证。

调用示例：`$english-study-notes 把附件全部句子做成 English Atlas，完整详解，突出词条、近义辨析与考点，输出 PDF 和离线互动版。`
