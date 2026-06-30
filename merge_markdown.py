#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并「缠中说禅教你炒股票 108 课」Markdown 源文件。

相比根目录下的 mergeMarkdownFiles.js，本脚本做了三点关键改进：
  1. 物理隔离产物：仅匹配 108/ 下符合源文件命名规则的 .md，产物写到项目根目录，
     永远不会被当作源文件重复读入——彻底避免 JS 版「重复运行导致内容翻倍」的陷阱。
  2. 按课号正确排序（001..108，再 W 补遗），而非 readdirSync 的字母序。
  3. 新增 ebook 模式，针对 Pandoc → EPUB 做排版优化：
       · 评论由 ``` 代码块改为 Markdown 引用块（EPUB 中可正常换行、阅读）
       · 评论按 UID 头切分并清除所有反引号——天然规避个别文件因网友行内反引号
         导致的围栏破损问题
       · 一级标题去除「博客ID -」前缀，目录更干净
       · 元信息（日期/分类）改为斜体小字题注，不再混入正文
       · 图片 alt 由无意义时间戳改为「图」
       · 规范化多余空行

用法:
  python3 merge_markdown.py                       # 生成 article / full / ebook / audio 四个版本
  python3 merge_markdown.py --only ebook          # 仅生成 EPUB 优化版
  python3 merge_markdown.py --only audio          # 仅生成听书优化版
  python3 merge_markdown.py --src 108 --out .     # 指定源目录与输出目录
"""

import argparse
import os
import re
import sys
from pathlib import Path

# ── 路径与正则 ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
DEFAULT_SRC = ROOT / "108"
DEFAULT_OUT = ROOT
README = ROOT / "README.md"

# 源文件命名：
#   0187-486e105c01000461-001.md   正式课文 001..108
#   0483-...-W004.md               W 补遗
#   0596-...-(4).md                括号补遗（108 课之外的缠论相关文章）
SRC_RE = re.compile(r"^\d{4}-486e105c0100[\w]+-(\d{3}|W\d{3}|\(\d+\))\.md$")
# 课文 / 评论分隔标记（原 JS 用 split("**本文评论获取自") 切分）
COMMENT_SEP = "**本文评论获取自"
# 评论头：UID:[1215172700] 昵称：[匿名] 缠中说禅 日期：(2006-12-05 11:53:53)
HEAD_RE = re.compile(
    r"^UID:\[([^\]]*)\]\s*昵称：(.*?)\s*日期：\(([^)]*)\)\s*$", re.MULTILINE
)
# 标题：# 0187 - 教你炒股票1：……
TITLE_RE = re.compile(r"^# (\d{4})\s*-\s*(.+?)\s*$", re.MULTILINE)


# ── 排序 ──────────────────────────────────────────────────────────────────
def lesson_key(lesson_no: str):
    """排序键：数字课号(001..108) → W 补遗 → 括号补遗。"""
    if lesson_no.startswith("("):           # (4) 括号补遗排最后
        return (2, int(lesson_no.strip("()")))
    if lesson_no.startswith("W"):           # W 补遗
        return (1, int(lesson_no[1:]))
    return (0, int(lesson_no))              # 001..108 正式课文


def discover_sources(src_dir: Path):
    """返回按课号排序的 (课号, Path) 列表，仅含符合命名规则的源文件。"""
    items = []
    for p in sorted(src_dir.iterdir()):
        m = SRC_RE.match(p.name)
        if m:
            items.append((m.group(1), p))
    items.sort(key=lambda x: lesson_key(x[0]))
    return items


# ── 课文 / 评论切分 ───────────────────────────────────────────────────────
def split_article_comment(text: str):
    """按 COMMENT_SEP 切成 (课文, 评论原始文本)。无分隔符则评论为空。"""
    idx = text.find(COMMENT_SEP)
    if idx == -1:
        return text, ""
    return text[:idx], text[idx:]


# ── ebook 模式：单文件排版优化 ────────────────────────────────────────────
def clean_metadata_line(line: str):
    """日期：(...) 分类：[...]  → 斜体小字题注；末尾空格清除。"""
    line = line.rstrip()
    if line.startswith("日期：") or line.startswith("分类：") or "分类：" in line:
        # 去掉分类（几乎全是同一个值，信息量为零），保留日期
        date_m = re.search(r"日期：\(([^)]*)\)", line)
        if date_m:
            return f"*{date_m.group(1)}*"
    return line


def convert_comment_block(comment_text: str):
    """
    把整段评论区（含 ``` 围栏）转为 Markdown 引用块字符串。

    解析以「UID:」开头的评论头为边界，不依赖反引号配对，因此即使个别
    评论正文里含网友写的行内 ``` 也能正确切分。评论内所有反引号会被
    清除（评论是纯对话文本，反引号均为围栏噪音）。
    """
    text = comment_text.replace("`", "")  # 清除全部反引号
    matches = list(HEAD_RE.finditer(text))
    if not matches:
        return comment_text.strip()

    blocks = []
    for i, m in enumerate(matches):
        nick_raw = m.group(2).strip()
        date = m.group(3).strip()
        nick = re.sub(r"^\[匿名\]\s*", "", nick_raw).strip() or "匿名"
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip("\n").strip()
        blocks.append(format_one_comment(nick, date, body))
    return "\n\n".join(blocks)


def format_one_comment(nick: str, date: str, body: str):
    """单条评论 → 引用块。识别独占一行的 `==`/`===` 分隔的「引用网友提问 / 禅师回复」。"""
    parts = re.split(r"\n[=]{2,}\s*\n", body, maxsplit=1)
    header = f"> **{nick}**　<small>{date}</small>"
    if len(parts) == 2:
        quoted = _dedent(parts[0]).strip()
        reply = _dedent(parts[1]).strip()
        if quoted:
            quoted_blk = _prefix(quoted, ">> ")
            reply_blk = _prefix(reply, "> ")
            return f"{header}\n>\n{quoted_blk}\n>\n{reply_blk}".rstrip()
    # 无分隔符：整段为该评论者发言，去掉行首缩进后作为引用块
    return f"{header}\n>\n{_prefix(_dedent(body), '> ')}".rstrip()


def _dedent(text: str):
    """去掉每行行首的 tab / 空格缩进。"""
    return re.sub(r"^[ \t]+", "", text, flags=re.MULTILINE)


def _prefix(text: str, prefix: str):
    """给每个非空行加前缀（空行只加一个 '>' 标记，保持引用块连续）。"""
    out = []
    for ln in text.split("\n"):
        out.append(prefix + ln if ln.strip() else ">")
    return "\n".join(out)


def transform_for_ebook(raw: str, pic_prefix: str = "108/pic/"):
    """单篇课文 → EPUB 优化版 Markdown。

    pic_prefix 为图片目录相对输出目录的路径前缀，用于重写图片链接，
    使 Pandoc 无需 --resource-path 即可找到 108/pic/ 下的配图。
    """
    article, comment = split_article_comment(raw)
    lines = article.split("\n")
    out = []
    for ln in lines:
        # 1. 标题去博客ID
        tm = re.match(r"^# \d{4}\s*-\s*(.+?)\s*$", ln)
        if tm:
            out.append(f"# {tm.group(1).strip()}")
            continue
        # 2. 元信息行优化
        if "分类：" in ln and "日期：" in ln:
            out.append(clean_metadata_line(ln))
            continue
        # 3. 图片 alt 优化 + 路径重写：![image-时间戳](./pic/x) → ![图]({pic_prefix}x)
        ln = re.sub(r"!\[[^\]]*\]\(\./pic/", f"![图]({pic_prefix}", ln)
        out.append(ln)
    article_clean = "\n".join(out)

    # 4. 评论代码块 → 引用块
    if comment.strip():
        # 保留分隔标记作为评论区引导，并去掉其加粗（改为小标题式引导）
        sep_line = comment.split("\n", 1)[0]  # 形如 **本文评论获取自...[N]**
        n_m = re.search(r"\[(\d+)\]", sep_line)
        n_str = f"（共 {n_m.group(1)} 条）" if n_m else ""
        comment_body = comment[len(sep_line):]  # 去掉分隔标记行
        converted = convert_comment_block(comment_body)
        article_clean = (
            article_clean.rstrip()
            + "\n\n---\n\n"
            + f"## 课后回复{n_str}\n\n".rstrip("\n")
            + "\n\n"
            + converted
        )

    # 规范化：压缩 3+ 连续空行为 2 个
    article_clean = re.sub(r"\n{3,}", "\n\n", article_clean)
    return article_clean.strip() + "\n"


# ── audio 模式：听书优化（TTS 友好）──────────────────────────────────────
CHAN_NICK = "缠中说禅"
AUDIO_HEADER = (
    "# 缠中说禅教你炒股票108课\n\n"
    "听书版：不含图片，课后回复仅保留缠中说禅本人的答复。\n\n---\n\n"
)


def transform_for_audio(raw: str):
    """单篇课文 → 听书优化版 Markdown。

    针对电子书 TTS 朗读优化：
      · 移除图片、图注、ASCII 走势图（代码块）—— TTS 无法朗读图形
      · 评论仅保留「缠中说禅」本人的回复（网友闲聊对学习无价值，徒增朗读时长）
      · 评论不再逐条署名（全是同一人），问答用「问：/答：」引导，便于听辨
      · 移除行内术语反引号
    """
    article, comment = split_article_comment(raw)

    # ── 课文：去图 / 去编者注 / 去 ASCII 代码块 / 去博客ID / 元信息简化 ──
    out, in_code = [], False
    for ln in article.split("\n"):
        ln = ln.replace("​", "").replace("﻿", "")   # 零宽空格 / BOM
        ln = re.sub(r"【编者注[^】]*】", "", ln)                # 编者注（图注 & 文内注）
        s = ln.strip()
        if s.startswith("```"):               # 围栏（079 课 ASCII 走势图等），整块跳过
            in_code = not in_code
            continue
        if in_code:
            continue
        if s.startswith("!["):                # 图片行
            continue
        if not s:                             # 空行保留（维持段落）
            out.append("")
            continue
        tm = re.match(r"^# \d{4}\s*-\s*(.+?)\s*$", ln)
        if tm:                                # 标题去博客ID
            out.append(f"# {tm.group(1).strip()}")
            continue
        if "分类：" in ln and "日期：" in ln:    # 元信息简化
            out.append(clean_metadata_line(ln))
            continue
        out.append(ln.replace("`", ""))       # 移除行内术语反引号
    article_clean = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()

    # ── 评论：仅禅师回复 ──
    replies = extract_chan_replies(comment)
    if replies:
        article_clean += "\n\n---\n\n## 禅师课后回复\n\n" + replies
    return article_clean + "\n"


def extract_chan_replies(comment_text: str):
    """从评论区提取「缠中说禅」的回复，返回拼好的引用块字符串。"""
    text = comment_text.replace("`", "")
    matches = list(HEAD_RE.finditer(text))
    blocks = []
    for i, m in enumerate(matches):
        nick = re.sub(r"^\[匿名\]\s*", "", m.group(2).strip()).strip()
        if nick != CHAN_NICK:
            continue
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = _dedent(text[m.end():body_end])
        body = body.replace("​", "")
        body = re.sub(r"【编者注[^】]*】", "", body).strip()
        if body:
            blocks.append(format_audio_reply(body))
    return "\n\n".join(b for b in blocks if b)


def format_audio_reply(body: str):
    """单条禅师回复 → 引用块。有「==」分隔的网友提问转为「问：/答：」。"""
    parts = re.split(r"\n[=]{2,}\s*\n", body, maxsplit=1)
    segs = []
    if len(parts) == 2:
        q, a = parts[0].strip(), parts[1].strip()
        if q:
            segs.append("问：" + q)
        if a:
            segs.append("答：" + a)
    elif parts[0].strip():
        segs.append(parts[0].strip())
    return _prefix("\n\n".join(segs), "> ").rstrip() if segs else ""


# ── 合并写出 ──────────────────────────────────────────────────────────────
def read_readme_header():
    if README.exists():
        return README.read_text(encoding="utf-8").strip() + "\n\n\n"
    return ""


def build(targets, src_dir: Path, out_dir: Path):
    # 图片目录相对输出目录的路径（ebook 模式据此重写图片链接）
    pic_prefix = os.path.relpath(src_dir / "pic", out_dir).replace(os.sep, "/") + "/"
    sources = discover_sources(src_dir)
    if not sources:
        sys.exit(f"✗ 未在 {src_dir} 找到源文件（命名需匹配 {SRC_RE.pattern}）")
    print(f"✓ 发现 {len(sources)} 篇源文件，按课号排序合并。")

    # 预读并缓存原文
    raw_texts = [(no, p.read_text(encoding="utf-8")) for no, p in sources]

    jobs = {
        "article": ("108-Article.md", "仅课文（忠实原文）"),
        "full": ("108-Full.md", "全文（忠实原文，评论保留为代码块）"),
        "ebook": ("108-Ebook.md", "EPUB 优化版（评论→引用块 / 去博客ID / 元信息优化）"),
        "audio": ("108-Audio.md", "听书优化版（无图 / 仅禅师回复 / 去 ASCII 图）"),
    }

    for t in targets:
        # ebook 用 README 前言；audio 用专属简短前言（README 的构建说明对听书无意义）；
        # 其余版本保留 [toc] 占位以兼容旧工具（Pandoc 用 --toc 生成目录）
        readme = read_readme_header()
        if t == "audio":
            header = AUDIO_HEADER
        elif t == "ebook":
            header = readme
        else:
            header = "[toc]\n\n" + readme
        fname, desc = jobs[t]
        out = [header]
        for no, raw in raw_texts:
            if t == "article":
                out.append(split_article_comment(raw)[0].strip())
            elif t == "full":
                out.append(raw.strip())
            elif t == "audio":
                out.append(transform_for_audio(raw))
            else:  # ebook
                out.append(transform_for_ebook(raw, pic_prefix))
            out.append("\n\n---\n\n")  # 篇与篇之间分隔
        body = "\n\n".join(block.strip() for block in out if block and block.strip())
        # 篇间分隔：上面用 join 已经够了，这里去掉多余尾部
        dest = out_dir / fname
        dest.write_text(body.rstrip() + "\n", encoding="utf-8")
        print(f"  ✓ {fname:<18} {desc}\n      → {dest}")


def main():
    ap = argparse.ArgumentParser(description="合并 108 课 Markdown（Python 版）")
    ap.add_argument("--only", nargs="+", choices=["article", "full", "ebook", "audio"],
                    help="只生成指定版本，默认全部生成")
    ap.add_argument("--src", default=str(DEFAULT_SRC), help="源目录（默认 ./108）")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="输出目录（默认项目根）")
    args = ap.parse_args()
    targets = args.only or ["article", "full", "ebook"]
    build(targets, Path(args.src), Path(args.out))


if __name__ == "__main__":
    main()
