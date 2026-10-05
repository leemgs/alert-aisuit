#!/usr/bin/env python3
"""Cut the overruled-decisions table out of `pdftotext -layout` CONAN text.

    python cut_table.py data/raw/conan.txt data/raw/overruled_table.txt

The table runs from its title page ("TABLE OF SUPREME COURT DECISIONS") up to,
not including, the next table ("TABLE OF LAWS HELD UNCONSTITUTIONAL").
The output's sha256 is recorded in checksums.txt.
"""

import re
import sys

START = re.compile(r"^\f\s*TABLE OF SUPREME COURT DECISIONS\s*$")
END = re.compile(r"TABLE OF LAWS HELD UNCONSTITUTIONAL")


def main() -> int:
    src, dst = sys.argv[1], sys.argv[2]
    lines = open(src, encoding="utf-8").read().split("\n")
    start = next(i for i, l in enumerate(lines) if START.match(l))
    end = next(i for i in range(start + 1, len(lines)) if END.search(lines[i]))
    with open(dst, "w", encoding="utf-8") as f:
        f.write("\n".join(lines[start:end]) + "\n")
    print(f"lines {start}-{end} -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
