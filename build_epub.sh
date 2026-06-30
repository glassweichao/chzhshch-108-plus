#!/usr/bin/env bash
# 用 Pandoc 把 108-Ebook.md 转为 EPUB 电子书
#
# 依赖：
#   - python3   （生成 108-Ebook.md）
#   - pandoc    （macOS: brew install pandoc ；其他平台见 https://pandoc.org/install.html）
set -e
cd "$(dirname "$0")"

OUT="缠中说禅教你炒股票108课.epub"

# 1) 生成 EPUB 优化版 Markdown（已存在则跳过；加 -f 强制重新生成）
if [ "$1" = "-f" ] || [ ! -f 108-Ebook.md ]; then
    echo "→ 生成 108-Ebook.md …"
    python3 merge_markdown.py --only ebook
fi

# 2) Pandoc → EPUB
echo "→ 转换为 EPUB …"
pandoc 108-Ebook.md \
    -o "$OUT" \
    --metadata-file=epub/metadata.yaml \
    --css=epub/style.css \
    --toc \
    --toc-depth=1 \
    --split-level=1

echo "✓ 完成：$OUT"
