#!/usr/bin/env python3
"""
Generate a filtered OpenCC-format phrase pinyin dictionary.

The source phrase data uses:
    phrase: syllable1 syllable2 ...

OpenCC text dictionaries use spaces to separate multiple candidate values, so
syllables within one phrase reading are concatenated before writing. If the
same phrase appears with multiple readings, those full readings are preserved as
OpenCC candidates.

Only multi-character phrases containing at least one polyphonic character from
pinyin.txt are kept.

Usage:
    python3 gen_phrase_dict.py [phrase_source] [pinyin_dict] [output]

If no arguments are given, reads from
third_party/phrase-pinyin-data/large_pinyin.txt and pinyin.txt, and writes to
phrase_pinyin.txt in the current directory.
"""

from __future__ import annotations

import sys
from collections import OrderedDict
from pathlib import Path

DEFAULT_PHRASE_PATH = Path('third_party/phrase-pinyin-data/large_pinyin.txt')
DEFAULT_PINYIN_PATH = Path('pinyin.txt')
DEFAULT_OUTPUT_PATH = Path('phrase_pinyin.txt')


def load_polyphonic_chars(pinyin_path: Path) -> set[str]:
    """Return characters whose OpenCC pinyin entry has multiple candidates."""
    polyphonic_chars: set[str] = set()
    for line in pinyin_path.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#') or '\t' not in line:
            continue
        char, values = line.split('\t', 1)
        if len(values.split()) > 1:
            polyphonic_chars.add(char)
    return polyphonic_chars


def parse_phrase_line(line: str) -> tuple[str, str] | None:
    """Parse one upstream phrase line into (phrase, concatenated_reading)."""
    stripped = line.strip()
    if not stripped or stripped.startswith('#') or ':' not in stripped:
        return None

    phrase, reading = stripped.split(':', 1)
    phrase = phrase.strip()
    syllables = reading.split()
    if not phrase or not syllables:
        return None

    return phrase, ''.join(syllables)


def generate_phrase_entries(
    phrase_content: str,
    polyphonic_chars: set[str],
) -> OrderedDict[str, list[str]]:
    """Return filtered phrase entries with duplicate readings removed."""
    entries: OrderedDict[str, list[str]] = OrderedDict()
    for line in phrase_content.splitlines():
        parsed = parse_phrase_line(line)
        if parsed is None:
            continue

        phrase, reading = parsed
        if len(phrase) < 2 or not any(char in polyphonic_chars for char in phrase):
            continue

        readings = entries.setdefault(phrase, [])
        if reading not in readings:
            readings.append(reading)

    return entries


def write_opencc_dict(entries: OrderedDict[str, list[str]], output_path: Path) -> None:
    """Write phrase entries as OpenCC text dictionary lines."""
    with output_path.open('w', encoding='utf-8') as fh:
        for phrase, readings in entries.items():
            fh.write(f'{phrase}\t{" ".join(readings)}\n')


def main() -> None:
    args = sys.argv[1:]
    phrase_path = Path(args[0]) if len(args) >= 1 else DEFAULT_PHRASE_PATH
    pinyin_path = Path(args[1]) if len(args) >= 2 else DEFAULT_PINYIN_PATH
    output_path = Path(args[2]) if len(args) >= 3 else DEFAULT_OUTPUT_PATH

    polyphonic_chars = load_polyphonic_chars(pinyin_path)
    phrase_content = phrase_path.read_text(encoding='utf-8')
    entries = generate_phrase_entries(phrase_content, polyphonic_chars)
    write_opencc_dict(entries, output_path)

    reading_count = sum(len(readings) for readings in entries.values())
    print(
        f'Wrote {len(entries)} phrase entries '
        f'({reading_count} readings) to {output_path}'
    )


if __name__ == '__main__':
    main()
