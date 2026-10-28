# notes.json 数据约定

顶层包含 `meta`、`entries`、`groups`、`glossary`。JSON UTF-8，无注释。完整可运行的最小例子见 `../assets/example-notes.json`，其中内容只用于演示和检查。

## meta

`title` 为输出标题，`chapter` 为本章名称，`source_name` 为本次原文件名称，`source_pages` 为实际原文件页数。可选 `source_author` 仅填写原材料明确给出的作者。不得默认沿用 Chapter 2、151 句或原示例作者。

## entries

按原文顺序排列，`id` 保留原题号且唯一；本 renderer 支持非连续正整数编号。分节重复编号先建立明确的全局编号与原题号映射，再适配标签，不能静默合并。

| 字段 | 类型 | 内容 |
|---|---|---|
| id | integer | 原题号，唯一正整数 |
| page | integer | 实际来源页码 |
| english | string | 已核对的完整英文，移除题外释义后不能删词或纠正原文 |
| raw | string，可选 | 包含原括注与原始排版信息的提取文字 |
| keyword | string | 简短标题，如 `precede`；不得放整段词汇解释 |
| translation | string | 忠实、自然、完整的中文译文 |
| structure | string[] | 常规2至3条，结构拆解和逻辑关系 |
| vocabulary | object[]（兼容旧string[]） | 常规3至4条；本句义项、English词性、搭配，以及逐项近义Words or Phrases与辨析 |
| exam_points | string[] | 常规2条，具体语法或翻译考法 |
| pitfalls | string[] | 常规1至2条，易错点与原因 |
| source_note | string | 必要时说明原文瑕疵并另给建议；否则空字符串 |
| diagram | object[] | 常规3至4格；每格 `role` 为English标签，`text` 为原句片段 |
| memory_tip | string | 一个准确、简明、便于记忆的提示 |

写作长度由难度决定。300至500中文字是本次参考风格的常见密度，不是硬性配额。图格可用省略号压缩，但应保持来源可辨，不任意改变关系。新增需要标注的非逐字逻辑转换要明确说明。

### Vocabulary / Lexical Resources

新任务每项使用以下结构；旧 `string` 仍可读取，不会自动编造近义词。

```json
{
  "term": "provoke opposition",
  "explanation": "verb phrase，激起反对；provoke强调引发反应，在本句并非‘挑衅’。",
  "near_synonyms": [
    {"text": "arouse opposition", "distinction": "同样表示激起反对；arouse常与情绪、反应搭配。"},
    {"text": "trigger opposition", "distinction": "强调触发反对的起点；与provoke的侧重点不同。"}
  ]
}
```

`term`、`explanation`、`near_synonyms` 均必填，每个近义项包含非空的 `text` 和 `distinction`。通常选1至3个贴合本句的表达；数量不是硬配额。完整原词义及搭配仍放 `explanation`，近义表达不能替代原词讲解。

若确无合适表达，用 `"near_synonyms":[]` 并添加非空 `"no_synonym_reason"`。排版显示 Near synonyms 与原因。不得用反义词、宽泛同主题词或无解释的 `N/A` 填充；不能暗示所有近义项可直接替换。词性或结构变化在 `distinction` 写明，必要时给完整替换短语。

## groups

主题组按原句順序排列，每条 entry 恰好落入一个 `range:[firstId,lastId]`。不要为了套图重新打乱原句。

- `title`、`subtitle`：短中文标题与助学提示。
- `nodes`：恰好3项，每项 `[简短标题,核心English词,中文解释]`，用于三栏词义框。
- `rows`：比较表，各行 `[词或短语,含义区别,搭配或例子]`。
- `focus`、`warning`：一句语法提示及关键辨析。
- `icon` 可选：`reading` 通用；其余为具体语义的 `boundary`、`hurdle`、`choices`、`growth`、`family`、`pressure`、`fade`、`hourglass`、`traffic`、`filter`、`magnifier`。这些内置图有特定文字，只能在主题匹配时用。
- 新主题优先提供 `illustration:{primitives:[...]}` 替代内置图。

## 自定义矢量插图

画布480×180，左上角为原点。每项为 `{"type":...,"args":[...]}`。PDF与HTML共用相同绘图数据：

- `line`：`[x1,y1,x2,y2,"#颜色",线宽]`
- `rect`：`[x,y,宽,高,"#填色","#描边",圆角]`
- `circle`：`[中心x,中心y,半径,"#填色","#描边"]`
- `text`：`[中心x,顶部y,"文字","#颜色",字号]`

文字保持简短；图形别与标签重叠。用线与箭头建立清晰联系，可画路障、家谱、时间轴、对比或过程，但比喻不代替准确解释。顶层可选 `cover_illustration` 接受内置图名或相同对象；默认通用阅读流程。

## glossary

数组，每项为 `{term,translation,explanation,examples:[id,...]}`。`term` 为English，`translation` 为中文名称，`explanation` 为清楚的中文说明。所有 `examples` 都必须存在于本次 entries，不能沿用词表旧题号。

可以从 `../assets/grammar_glossary.json` 选择并扩展，但例句须重新验证。表应覆盖本次实际使用的核心术语，尤其 Subject、Predicate、Object、Complement、clause、phrase、tense、voice 等。

可选顶层 `review` 为 `[标题,正文]` 数组，覆盖默认复习路线；其中的题号和例子也必须来自新材料。
