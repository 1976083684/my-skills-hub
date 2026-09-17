
"""
有道云笔记 JSON → Markdown 转换器
用法: python convert_youdao.py <input.json> [-o output.md]

递归解析有道云笔记新版编辑器的 JSON block 树，
输出格式规范的 Markdown 文件。
"""
import json
import os
import re
import sys
import uuid
from argparse import ArgumentParser
from urllib.request import Request, urlopen


def extract_text(block, collect_styles=False):
    """递归提取 block 中的纯文本。

    关键：递归处理任意嵌套深度。
    表格单元格结构为 tc -> para -> text_block -> runs，
    简单单层遍历会返回空文本。
    """
    texts = []
    for child in block.get('5', []):
        # 链接块：type "3" with "4.hf" as URL
        if child.get('2') == '3':
            url = child.get('4', {}).get('hf', '')
            inner_text = extract_text(child)
            if url and inner_text:
                texts.append('[{}]({})'.format(inner_text, url))
            elif inner_text:
                texts.append(inner_text)
            continue

        # 文本 runs（直接在当前 child 上）
        has_runs = False
        for run in child.get('7', []):
            text = run.get('8', '')
            if text:
                has_runs = True
                if collect_styles:
                    texts.append((text, run.get('9', [])))
                else:
                    texts.append(text)

        # 没有 runs 但有子节点 → 递归进入（处理表格单元格等嵌套）
        if not has_runs and child.get('5'):
            sub_text = extract_text(child, collect_styles)
            if sub_text:
                if collect_styles:
                    texts.extend(sub_text)
                else:
                    texts.append(sub_text)

    if collect_styles:
        return texts
    return ''.join(texts)


def apply_inline_styles(text, styles):
    """应用行内样式：b=粗体, i=斜体, u=下划线, s=删除线"""
    has_bold = any(s.get('2') == 'b' for s in styles)
    has_italic = any(s.get('2') == 'i' for s in styles)
    has_strikethrough = any(s.get('2') == 's' for s in styles)

    result = text.strip()
    if not result:
        return result

    if has_bold and has_italic:
        result = '***{}***'.format(result)
    elif has_bold:
        result = '**{}**'.format(result)
    elif has_italic:
        result = '*{}*'.format(result)

    if has_strikethrough:
        result = '~~{}~~'.format(result)

    return result


def block_to_markdown(block, indent_level=0):
    """将单个 JSON block 转换为 Markdown 字符串"""
    block_type = block.get('6', '?')

    # === 标题 ===
    if block_type == 'h':
        level_map = block.get('4', {}).get('l', 'h2')
        level_num = int(level_map[1]) if level_map.startswith('h') else 2
        text = extract_text(block)
        return '\n{} {}\n'.format('#' * level_num, text)

    # === 引用块 ===
    elif block_type == 'q':
        lines = []
        for child in block.get('5', []):
            child_type = child.get('6', '')
            if child_type:
                sub = block_to_markdown(child)
                for line in sub.strip().split('\n'):
                    lines.append('> {}'.format(line))
            else:
                for sub_child in child.get('5', []):
                    for run in sub_child.get('7', []):
                        lines.append('> {}'.format(run.get('8', '')))
        return '\n'.join(lines) + '\n'

    # === 列表 ===
    elif block_type == 'l':
        lt = block.get('4', {}).get('lt', 'unordered')
        ll = block.get('4', {}).get('ll', 1)
        indent = '  ' * (ll - 1)

        lines = []
        for i, child in enumerate(block.get('5', [])):
            prefix = '- ' if lt == 'unordered' else '{}. '.format(i + 1)
            first_text = ''
            for sb in child.get('5', []):
                if sb.get('2') == '3':
                    url = sb.get('4', {}).get('hf', '')
                    inner = extract_text(sb)
                    first_text += '[{}]({})'.format(inner, url) if url else inner
                else:
                    for run in sb.get('7', []):
                        text = run.get('8', '')
                        styled = apply_inline_styles(text, run.get('9', []))
                        first_text += styled
            lines.append('{}{}{}'.format(indent, prefix, first_text))
        return '\n'.join(lines) + '\n'

    # === 代码块 ===
    elif block_type == 'cd':
        language = block.get('4', {}).get('la', '')
        code_lines = []
        for child in block.get('5', []):
            if child.get('6') == 'cl':
                for sub in child.get('5', []):
                    for run in sub.get('7', []):
                        code_lines.append(run.get('8', ''))
        code = '\n'.join(code_lines)
        return '\n```{}\n{}\n```\n'.format(language, code)

    # === 图片 ===
    elif block_type == 'im':
        url = block.get('4', {}).get('u', '')
        if url:
            return '\n![image]({})\n'.format(url)
        return ''

    # === 表格 ===
    elif block_type == 't':
        rows = block.get('5', [])
        table_lines = []
        for row_idx, row in enumerate(rows):
            cells = []
            for cell in row.get('5', []):
                if cell.get('6') == 'tc':
                    text = extract_text(cell).replace('\n', ' ').replace('|', '\\|')
                    cells.append(text.strip())
            if not cells:
                continue
            table_lines.append('| ' + ' | '.join(cells) + ' |')
            if row_idx == 0:
                table_lines.append('| ' + ' | '.join(['---'] * len(cells)) + ' |')
        return '\n' + '\n'.join(table_lines) + '\n'

    # === 段落 / 未知 ===
    else:
        styled_texts = extract_text(block, collect_styles=True)
        if not styled_texts:
            return ''

        result_parts = []
        for text, styles in styled_texts:
            result_parts.append(apply_inline_styles(text, styles))

        line = ''.join(result_parts)
        if not line.strip():
            return '\n'
        return '{}\n'.format(line)


def convert_to_markdown(data):
    """主转换函数：API 返回的 JSON → Markdown 字符串"""
    raw_content = data.get('content', '{}')
    content = json.loads(raw_content)

    title = data.get('tl', content.get('title', '未命名笔记'))
    blocks = content.get('5', [])

    md_lines = ['# {}\n'.format(title)]
    md_lines.append('> **来源：** 有道云笔记分享\n')

    # 跳过与标题重复的第一个 h1 block（需 Unicode 规范化比较）
    skip_first_h1 = False
    for i, block in enumerate(blocks):
        if block.get('6') == 'h' and block.get('4', {}).get('l') == 'h1':
            h1_text = extract_text(block).strip()

            def norm(s):
                return re.sub(r'\s+', '', s)
            if norm(h1_text) == norm(title):
                skip_first_h1 = True
        break

    for i, block in enumerate(blocks):
        if skip_first_h1 and i == 0:
            continue

        # 跳过空标题
        bt = block.get('6', '?')
        if bt == 'h' and not extract_text(block).strip():
            continue

        # 跳过空列表
        if bt == 'l' and not extract_text(block).strip():
            continue

        md = block_to_markdown(block)
        if md:
            md_lines.append(md)

    # === 后处理 ===
    result = '\n'.join(md_lines)

    # 压缩多余空行
    result = re.sub(r'\n{4,}', '\n\n\n', result)

    # 清理空列表项（多次迭代处理嵌套情况）
    for _ in range(3):
        result = re.sub(r'\n+( {0,6})[-*+]\s*\n+', '\n', result)
        result = re.sub(r'\n+( {0,6})\d+\.\s*\n+', '\n', result)

    # 兜底清理
    result = re.sub(r'\n( {0,6})[-*+] ?\n', '\n', result)
    result = re.sub(r'\n+( {0,6})[-*+]\s*$', '', result)

    # 末尾规范化
    result = result.rstrip() + '\n'
    return result


def fetch_note(share_key):
    """通过有道云 API 获取笔记 JSON"""
    url = (
        'https://note.youdao.com/yws/api/note/{key}'
        '?sev=j1&editorType=1&unloginId={uid}&editorVersion=new-json-editor&sec=v1'
    ).format(key=share_key, uid=str(uuid.uuid4()))

    req = Request(url, headers={
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ),
        'Referer': (
            'https://share.note.youdao.com/ynoteshare/index.html'
            '?id={key}&type=note'.format(key=share_key)
        ),
    })

    with urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))


def main():
    parser = ArgumentParser(description='有道云笔记 JSON → Markdown 转换器')
    parser.add_argument('input', nargs='?', help='API 返回的 JSON 文件路径（如不提供则从 shareKey 在线获取）')
    parser.add_argument('-k', '--share-key', help='有道云分享链接的 shareKey（在线获取时必填）')
    parser.add_argument('-o', '--output', help='输出 Markdown 文件路径')
    parser.add_argument('--download-only', action='store_true', help='仅下载 JSON，不转换')

    args = parser.parse_args()

    # 在线获取
    if args.share_key:
        print('正在获取笔记 {} ...'.format(args.share_key))
        data = fetch_note(args.share_key)
        title = data.get('tl', 'youdao_note')

        if args.download_only:
            out_file = args.output or '{}.json'.format(title)
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print('已保存 JSON: {}'.format(out_file))
            return

        markdown = convert_to_markdown(data)
        out_file = args.output or '{}.md'.format(title)
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
        print('转换完成: {} ({} 字符)'.format(out_file, len(markdown)))
        return

    # 从本地 JSON 文件转换
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)

        markdown = convert_to_markdown(data)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(markdown)
            print('转换完成: {} ({} 字符)'.format(args.output, len(markdown)))
        else:
            sys.stdout.reconfigure(encoding='utf-8')
            print(markdown)
        return

    parser.print_help()


if __name__ == '__main__':
    main()
