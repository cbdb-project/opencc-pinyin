#!/usr/bin/env python3
"""
Generate an OpenCC-format pinyin dictionary (pinyin.txt) from the bundled
third-party pinyin-data zdic.txt.

Source data: https://github.com/mozillazg/pinyin-data/blob/master/zdic.txt

For polyphonic characters (多音字), all readings are kept in original order and
joined by spaces.

Usage:
    python gen_dict.py [zdic.txt] [pinyin.txt]

If no arguments are given, reads from third_party/pinyin-data/zdic.txt and
writes to pinyin.txt in the current directory.
"""

import re
import sys
from pathlib import Path

# Pattern: U+XXXX: pinyin1,pinyin2,...  # character
_LINE_RE = re.compile(r'^U\+([0-9A-Fa-f]+):\s+(\S+)\s+#')
DEFAULT_ZDIC_PATH = Path('third_party/pinyin-data/zdic.txt')


def parse_zdic(content: str) -> list[tuple[str, str]]:
    """Parse zdic.txt and return a list of (character, output_value) pairs.

    The order in zdic.txt is preserved.
    For polyphonic characters (multiple comma-separated readings), all readings
    are preserved and joined by spaces.
    """
    entries: list[tuple[str, str]] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        m = _LINE_RE.match(line)
        if not m:
            continue
        codepoint_hex, pinyins_str = m.group(1), m.group(2)
        char = chr(int(codepoint_hex, 16))
        readings = pinyins_str.split(',')
        entries.append((char, ' '.join(readings)))
    return entries


def write_opencc_dict(entries: list[tuple[str, str]], output_path: Path) -> None:
    """Write an OpenCC text-format dictionary file.

    Each line is:  key TAB value
    """
    with output_path.open('w', encoding='utf-8') as fh:
        for char, pinyin in entries:
            fh.write(f'{char}\t{pinyin}\n')


def main() -> None:
    args = sys.argv[1:]
    zdic_path = Path(args[0]) if len(args) >= 1 else DEFAULT_ZDIC_PATH
    out_path = Path(args[1]) if len(args) >= 2 else Path('pinyin.txt')

    if not zdic_path.exists():
        print(
            f'Error: {zdic_path} not found.\n'
            'Download it with:\n'
            '  mkdir -p third_party/pinyin-data\n'
            '  curl -fsSL https://raw.githubusercontent.com/mozillazg/'
            'pinyin-data/master/zdic.txt '
            '-o third_party/pinyin-data/zdic.txt',
            file=sys.stderr,
        )
        sys.exit(1)

    content = zdic_path.read_text(encoding='utf-8')
    entries = parse_zdic(content)
    write_opencc_dict(entries, out_path)
    print(f'Wrote {len(entries)} entries to {out_path}')


if __name__ == '__main__':
    main()
