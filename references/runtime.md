# 运行与验证

优先使用当前 Codex bundled runtime；`scripts/run.ps1` 会在当前用户目录动态发现，不依赖固定用户名或工作区路径。不修改全局配置、PATH 或用户文档。

## 依赖

- Python：`reportlab`、`pypdf`、`Pillow`。`doctor` 必须实际通过。
- PDF 渲染：Poppler 的 `pdftoppm`。先找当前 runtime，再找 PATH。
- 字体：Windows 默认 Microsoft YaHei 和 Arial。其他环境可通过 `--font-cn`、`--font-cn-bold` 指定支持中文的 TrueType字体或兼容TTC。不能用缺字字体假装成功。
- 网页检查：Node 和 Playwright，使用当前 runtime 的模块；浏览器可用已安装的 Edge 或 Playwright Chromium。

只有缺少实际需要的依赖时才安装相应包，不替换用户已有环境。不要把临时依赖安装误报成全局安装。

## 手动调用

```text
python extract_sentences.py --input source.pdf --output-dir work/run
python validate_content.py --input work/run/notes.json --source work/run/sentences.json
python render_notes.py --input work/run/notes.json --output-dir outputs --qa-dir work/run/qa
python verify_artifacts.py --qa-dir work/run/qa --render
node check_web.cjs --html outputs/notes.html --qa-dir work/run/qa
```

真实文件名来自 renderer 输出，不能照抄 `notes.html` 猜测存在。

## 检查范围

`validate_content.py` 检查结构与来源覆盖，不证明翻译正确。`verify_artifacts.py` 检查所有英文、译文、解析与提示是否进入 PDF，按需生成每页 PNG 和 contact sheets；人工视觉检查仍必需。`check_web.cjs` 验证题号检索、重置、译文遮罩、单句揭晓、glossary 链接、窄屏与页面错误。

渲染和检查必须顺序执行。不要一边覆盖 PNG 一边拼 contact sheets，否则可能读取尚未写完的图像。

新增或改造脚本后，先用 `assets/example-notes.json` 小样，再用当前新材料实跑。输出在本次 `work/` 或 `outputs/`，不得写回 Skill 的 assets 或覆盖其他章节交付文件。前端 HTML 不含外部资源，无需部署。
