#!/usr/bin/env python
"""提取原型 HTML 的纯文本，按关键字切段输出，供 PRD/原型对照阅读。

用法：
  python -I extract_html_text.py <html文件> <输出txt> [起始关键字] [结束关键字]

- 自动尝试 utf-8 / gb18030 解码
- 剥离 style/script/标签，压缩空白
- 不给关键字则提取全文
"""
import re
import sys


def strip_html(s: str) -> str:
    s = re.sub(r'<style.*?</style>', ' ', s, flags=re.S)
    s = re.sub(r'<script.*?</script>', ' ', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'&[a-z]+;', ' ', s)
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\n\s*\n+', '\n', s)
    return s.strip()


def main() -> None:
    src, dst = sys.argv[1], sys.argv[2]
    start_kw = sys.argv[3] if len(sys.argv) > 3 else None
    end_kw = sys.argv[4] if len(sys.argv) > 4 else None

    raw = open(src, 'rb').read()
    for enc in ('utf-8', 'gb18030'):
        try:
            html = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        html = raw.decode('utf-8', errors='ignore')

    i = html.find(start_kw) if start_kw else 0
    if i < 0:
        i = 0
    j = html.find(end_kw, i) if end_kw else len(html)
    if j < 0:
        j = len(html)

    text = strip_html(html[i:j])
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'extracted {len(text)} chars -> {dst}')


if __name__ == '__main__':
    main()
