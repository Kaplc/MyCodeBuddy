from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"c:/Users/v_zhyyzheng/Desktop/MyCodeBuddy")
OUTPUT_ROOT = ROOT / "docs" / "AI人机协同规划执行"

DOCS = [
    {
        "source": ROOT / "AI人机协同规划执行开发文档.md",
        "folder": OUTPUT_ROOT / "开发文档",
        "label": "开发文档",
    },
    {
        "source": ROOT / "AI人机协同规划执行方案.md",
        "folder": OUTPUT_ROOT / "方案文档",
        "label": "方案文档",
    },
]

INVALID_CHARS = re.compile(r'[<>:"/\\|?*]')
SECTION_RE = re.compile(r'^##\s+(.+)$', re.MULTILINE)
TITLE_RE = re.compile(r'^###\s+(.+)$', re.MULTILINE)
CHINESE_INDEX_RE = re.compile(r'^[一二三四五六七八九十百零]+、\s*')


def sanitize_filename(name: str) -> str:
    name = CHINESE_INDEX_RE.sub('', name).strip()
    name = INVALID_CHARS.sub('-', name)
    name = re.sub(r'\s+', '', name)
    return name or '未命名章节'


def split_markdown(doc: dict) -> list[dict]:
    source = doc['source']
    folder = doc['folder']
    folder.mkdir(parents=True, exist_ok=True)

    text = source.read_text(encoding='utf-8')
    title_match = TITLE_RE.search(text)
    doc_title = title_match.group(1).strip() if title_match else source.stem

    matches = list(SECTION_RE.finditer(text))
    sections: list[dict] = []
    for idx, match in enumerate(matches, start=1):
        start = match.start()
        end = matches[idx].start() if idx < len(matches) else len(text)
        heading = match.group(1).strip()
        section_text = text[start:end].strip() + '\n'
        file_name = f"{idx:02d}-{sanitize_filename(heading)}.md"
        file_path = folder / file_name
        file_content = f"### {doc_title}\n\n{section_text}"
        file_path.write_text(file_content, encoding='utf-8')
        sections.append({
            'heading': heading,
            'file_name': file_name,
            'relative_path': file_path.relative_to(OUTPUT_ROOT).as_posix(),
        })

    readme_lines = [
        f"### {doc_title}（拆分版）",
        '',
        f"- **来源文件**：`{source.name}`",
        f"- **章节数**：{len(sections)}",
        '- **说明**：按一级章节（`##`）拆分，保留原始根目录单文件版本。',
        '',
        '## 章节导航',
        '',
    ]
    for section in sections:
        readme_lines.append(f"- [{section['heading']}]({section['file_name']})")

    (folder / 'README.md').write_text('\n'.join(readme_lines) + '\n', encoding='utf-8')
    return [{**section, 'doc_title': doc_title, 'label': doc['label'], 'source_name': source.name} for section in sections]


def build_root_readme(all_sections: dict[str, list[dict]]) -> None:
    lines = [
        '### AI 人机协同规划执行文档导航',
        '',
        '- **说明**：这里是拆分后的多文件版本，便于按主题阅读、评审和后续维护。',
        '- **保留策略**：根目录原始文档保留不变，拆分版放在本目录。',
        '',
        '## 文档入口',
        '',
        '- [开发文档总览](开发文档/README.md)',
        '- [方案文档总览](方案文档/README.md)',
        '',
        '## 原始单文件',
        '',
        '- [`AI人机协同规划执行开发文档.md`](../../AI人机协同规划执行开发文档.md)',
        '- [`AI人机协同规划执行方案.md`](../../AI人机协同规划执行方案.md)',
        '',
    ]

    for key in ['开发文档', '方案文档']:
        sections = all_sections[key]
        lines.extend([
            f'## {key}',
            '',
        ])
        for section in sections:
            lines.append(f"- [{section['heading']}]({section['relative_path']})")
        lines.append('')

    (OUTPUT_ROOT / 'README.md').write_text('\n'.join(lines), encoding='utf-8')


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    all_sections: dict[str, list[dict]] = {}
    for doc in DOCS:
        all_sections[doc['label']] = split_markdown(doc)
    build_root_readme(all_sections)
    print('split complete')


if __name__ == '__main__':
    main()
