#!/usr/bin/env python3
"""Deliver exactly one Markdown mode; SVG is rendered with Mermaid CLI."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import quote

FENCES = re.compile(r'(?m)^(?P<fence>`{3,}|~{3,})(?P<info>[^\r\n]*)\r?\n(?P<body>[\s\S]*?)^(?P=fence)[ \t]*\r?$', re.MULTILINE)


def diagrams(text):
    return [m for m in FENCES.finditer(text) if m.group('info').strip().lower() == 'mermaid']


def renderer(cli):
    if cli:
        target = Path(cli).expanduser().resolve()
        if not target.is_file():
            raise ValueError(f'Mermaid CLI 不存在：{target}')
        if target.suffix in ('.js', '.mjs'):
            node = shutil.which('node')
            if not node:
                raise ValueError('未找到 Node.js')
            return [node, str(target)]
        # Execute Windows npm shims through their actual JS entry, avoiding shell interpolation.
        if target.suffix.lower() in ('.cmd', '.ps1'):
            entry = target.parent / 'node_modules/@mermaid-js/mermaid-cli/src/cli.js'
            if entry.is_file():
                return renderer(str(entry))
            raise ValueError('请用 --mmdc 指定 mermaid-cli/src/cli.js，不能执行未知 shell 包装器')
        return [str(target)]
    env = os.environ.get('MERMAID_CLI')
    if env:
        return renderer(env)
    found = shutil.which('mmdc')
    if found:
        return renderer(found)
    raise ValueError('未找到 Mermaid CLI；请设置 MERMAID_CLI 或传入 --mmdc 的 cli.js 路径')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--mode', required=True, choices=['svg', 'mermaid'])
    p.add_argument('--mmdc', help='Mermaid CLI 的 cli.js 或原生可执行文件路径')
    p.add_argument('--browser', help='Chrome/Chromium 可执行文件路径；也可用 MERMAID_BROWSER')
    p.add_argument('--config', type=Path, default=Path(__file__).resolve().parent.parent / 'mermaid-config.json')
    p.add_argument('--force', action='store_true', help='允许更新输出文档及其同名派生 SVG')
    args = p.parse_args()
    source, output = args.input.resolve(), args.output.resolve()
    if source.suffix.lower() != '.md' or output.suffix.lower() != '.md':
        raise ValueError('输入与输出都必须是 .md 文件')
    if output.exists() and not args.force:
        raise ValueError(f'输出已存在，更新时请显式加 --force：{output}')
    text = source.read_text(encoding='utf-8-sig')
    matches = diagrams(text)
    if not matches:
        raise ValueError('输入没有 Mermaid 图；请使用含 Mermaid 代码块的源稿，不要输入 SVG 成品')
    if args.mode == 'mermaid':
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding='utf-8')
        print(json.dumps({'mode': 'mermaid', 'output': str(output), 'diagrams': len(matches),
                          'render_validation': '未执行；仅检查并保留 Mermaid 代码块', 'images_created': 0}, ensure_ascii=False))
        return
    command = renderer(args.mmdc)
    config = args.config.resolve()
    settings = json.loads(config.read_text(encoding='utf-8-sig'))
    browser = args.browser or os.environ.get('MERMAID_BROWSER')
    if browser and not Path(browser).is_file():
        raise ValueError(f'浏览器不存在：{browser}')
    image_dir = output.parent / 'images' / output.stem
    if image_dir.exists() and not args.force:
        raise ValueError(f'图片目录已存在；确认更新后加 --force：{image_dir}')
    with tempfile.TemporaryDirectory(prefix='mermaid-render-') as tmp:
        stage = Path(tmp)
        # Render all graphs together, preserving source order; original prose is never rewritten by CLI.
        graph_doc = '\n\n'.join('```mermaid\n' + m.group('body').rstrip() + '\n```' for m in matches)
        stage_input, stage_output = stage / 'input.md', stage / 'rendered.md'
        stage_input.write_text(graph_doc, encoding='utf-8')
        stage_config = stage / 'mermaid.json'
        stage_config.write_text(json.dumps(settings, ensure_ascii=False), encoding='utf-8')
        cmd = command + ['-i', str(stage_input), '-o', str(stage_output), '-c', str(stage_config), '-b', 'white']
        if browser:
            puppeteer = stage / 'browser.json'
            puppeteer.write_text(json.dumps({'executablePath': str(Path(browser).resolve())}), encoding='utf-8')
            cmd += ['-p', str(puppeteer)]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300)
        if result.returncode:
            raise ValueError('Mermaid 渲染失败，未写入交付文档：\n' + result.stdout[-4000:] + result.stderr[-4000:])
        expected = [stage / f'rendered-{i}.svg' for i in range(1, len(matches) + 1)]
        for file in expected:
            if not file.is_file() or '<svg' not in file.read_text(encoding='utf-8'):
                raise ValueError(f'渲染输出缺失或不是 SVG：{file.name}')
        replacements = []
        for i, match in enumerate(matches, 1):
            relative = f'./images/{output.stem}/diagram-{i:03d}.svg'
            replacements.append((match, f'![流程图 {i}]({quote(relative, safe="/.-_")})'))
        converted = text
        for match, replacement in reversed(replacements):
            converted = converted[:match.start()] + replacement + converted[match.end():]
        output.parent.mkdir(parents=True, exist_ok=True)
        image_dir.mkdir(parents=True, exist_ok=True)
        for i, file in enumerate(expected, 1):
            shutil.copyfile(file, image_dir / f'diagram-{i:03d}.svg')
        output.write_text(converted, encoding='utf-8')
        print(json.dumps({'mode': 'svg', 'output': str(output), 'diagrams': len(matches),
                          'images': str(image_dir), 'render_validation': '全部真实渲染通过'}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(f'错误：{exc}', file=sys.stderr)
        sys.exit(1)
