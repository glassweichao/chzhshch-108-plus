#!/usr/bin/env bash
# 用 Pandoc 把合并后的 Markdown 转为 EPUB 电子书
#
# 用法：
#   ./build_epub.sh            # 图文完整版（108-Ebook.md）
#   ./build_epub.sh --audio    # 听书版（108-Audio.md：无图、仅禅师回复、去 ASCII 走势图）
#   ./build_epub.sh -f         # 强制重新生成 Markdown 后再转
#   ./build_epub.sh --audio -f
#
# 依赖：
#   - python3   （生成 Markdown）
#   - pandoc    （macOS: brew install pandoc ；其他平台见 https://pandoc.org/install.html）
set -e
cd "$(dirname "$0")"

AUDIO=0; FORCE=0
for a in "$@"; do
    case "$a" in
        --audio) AUDIO=1 ;;
        -f)      FORCE=1 ;;
        *)       echo "未知参数: $a"; exit 1 ;;
    esac
done

if [ "$AUDIO" = "1" ]; then
    MODE=audio; SRC=108-Audio.md; OUT="缠中说禅教你炒股票108课（听书版）.epub"
else
    MODE=ebook; SRC=108-Ebook.md; OUT="缠中说禅教你炒股票108课.epub"
fi

# 1) 生成 Markdown（已存在则跳过；-f 强制重新生成）
if [ "$FORCE" = "1" ] || [ ! -f "$SRC" ]; then
    echo "→ 生成 $SRC …"
    python3 merge_markdown.py --only "$MODE"
fi

# 2) Pandoc → EPUB
echo "→ 转换为 EPUB …"
pandoc "$SRC" \
    -o "$OUT" \
    --metadata-file=epub/metadata.yaml \
    --css=epub/style.css \
    --toc \
    --toc-depth=1 \
    --split-level=1

echo "✓ 完成：$OUT"
