# english-study-notes

把编号式英语句子翻译练习 PDF、图片或文档制作成彩色学霸笔记。

完整翻译并详细讲解结构、词汇、考点与易错点，配箭头拆句和趣味词义图；正文语法术语使用 English，集中提供中英对照。默认交付可打印 PDF 和可搜索、自测、跳转的离线 HTML。

适用于考研核心词句子练习及类似材料，不用于仅翻译一句话或通用文件转换。

## 安装

本仓库是一个 [Agent Skill](https://agentskills.io/)（基于 `SKILL.md`），兼容 TRAE、Claude Code、Cursor 等支持该规范的客户端。

### 方式一：openskills（推荐）

```bash
npx openskills install hyperactification/english-study-notes
```

### 方式二：手动导入（TRAE）

1. 下载本仓库为 zip 并解压，或直接 `git clone`
2. 打开 TRAE → 设置 → 技能与命令 → 创建 → 上传 zip（或选择 `SKILL.md`）
3. 安装后即可在对话中调用

### 方式三：手动复制

将 `english-study-notes` 目录复制到全局技能目录：

- macOS/Linux：`~/.trae/skills/`
- Windows：`%userprofile%/.trae/skills/`

## 目录结构

```
english-study-notes/
├── SKILL.md                # 智能体核心指令
├── agents/                 # agent 配置
│   └── openai.yaml
├── assets/                 # 参考样张与可复用素材
│   ├── example-notes.json
│   ├── grammar_glossary.json
│   └── reference-*.png
├── references/             # 内容、设计、数据结构与运行时说明
│   ├── content-guide.md
│   ├── design-guide.md
│   ├── schema.md
│   └── runtime.md
└── scripts/                # 提取、校验、渲染与校验脚本
    ├── extract_sentences.py
    ├── render_notes.py
    ├── validate_content.py
    ├── verify_artifacts.py
    ├── check_web.cjs
    ├── grammar_terms.py
    └── run.ps1
```

## 使用

安装后，向智能体发送类似指令即可触发：

> 把附件里的全部句子制作成同款彩色学霸笔记，详细讲解并输出 PDF 和离线互动版。

## License

本仓库仅包含技能指令与辅助脚本，不附带第三方受版权保护的学习材料。用户需自行准备原始句子材料。
