# 缠中说禅教你炒股票108课加强版



包含以下内容：

- 全部108课原文（包括现在新浪博客显示**已加密**，或**已删除**的文章）
- 大量课后回复（不仅仅是昵称为`缠中说禅`的，还包括`CCTV`、`罗锅`等被缠师点名表扬过，或者疑似缠师小号的回复）
- 原文配图（基本找全了）
- 108课之外的和缠论有关的文章（还在不断补充中）



希望对大家学习缠论有帮助！



更有缠论有用的内容，请关注原作者微信公众号【谢慕安】：

- MACD面积公式
- 防狼术公式
- 等等

---

## 制作 EPUB 电子书

本仓库提供脚本，可将全部课文（含课后回复、配图）合并并转为 EPUB 电子书。

### 依赖

- [Python 3](https://www.python.org/)（合并 Markdown）
- [Pandoc](https://pandoc.org/install.html)（转 EPUB；macOS 可 `brew install pandoc`）

### 一键生成

```bash
./build_epub.sh            # 图文完整版 →「缠中说禅教你炒股票108课.epub」
./build_epub.sh --audio    # 听书版（无图、仅禅师回复）→「缠中说禅教你炒股票108课（听书版）.epub」
./build_epub.sh -f         # 强制重新生成 Markdown 后再转
```

### 分步说明

1. `python3 merge_markdown.py` 生成四种合并版本（默认输出到项目根目录）：
   - `108-Article.md` —— 仅课文（忠实原文）
   - `108-Full.md` —— 全文（忠实原文，评论保留为代码块）
   - `108-Ebook.md` —— EPUB 优化版：评论转为引用块、标题去除博客ID、元信息改为题注、图片路径重写、多余空行规范化
   - `108-Audio.md` —— **听书优化版**：不含图片、课后回复仅保留缠中说禅本人的答复、移除 ASCII 走势图与编者注，问答用「问：/答：」引导（TTS 友好）
   - 可用 `--only article full ebook audio` 选择性生成

2. EPUB 相关配置在 `epub/` 目录：
   - `metadata.yaml` —— 书名、作者、语言等元数据
   - `style.css` —— 排版样式（中文字体、段落首行缩进、评论引用块、图片居中、ASCII 走势图等宽显示）

> Python 版 `merge_markdown.py` 相比旧版 `mergeMarkdownFiles.js` 修复了「重复运行导致内容翻倍」的陷阱：仅匹配源文件命名规则、产物写到项目根目录，物理隔离源文件与产物。

