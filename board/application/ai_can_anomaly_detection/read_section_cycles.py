"""Print the fewest and most cycles of each part the running board keeps in `section_cycles`.

    python3 -m board.application.ai_can_anomaly_detection.read_section_cycles

It reads `section_cycles` and `SystemCoreClock` over SWD without stopping the board, at
the addresses in the map file of the project in `board/paths.json`. It names the parts
from `Section` in `section_cycles.h` and prints each in cycles and in us.
"""

import argparse
import re
import subprocess

from board.flash import project_name
from board.paths import read_paths
from board.pc_answer import LIB

SECTION_CYCLES = LIB / "section_cycles" / "section_cycles.h"
NONE_SEEN = 0xFFFFFFFF  # what section_cycles_clear() sets fewest to


def section_names():
    """The parts in the order of `Section`, without the SECTION_ prefix."""
    body = re.search(r"typedef enum \{(.*?)\} Section;", SECTION_CYCLES.read_text(), re.S)
    names = re.findall(r"^\s*SECTION_(\w+),", body.group(1), re.M)
    return [name.lower() for name in names if name != "COUNT"]


def symbol_address(map_text, symbol):
    """The address the map file gives `symbol`."""
    found = re.search(rf"^\s+(0x[0-9a-f]+)\s+{symbol}$", map_text, re.M)
    if not found:
        raise SystemExit(f"{symbol} not in the map file")
    return int(found.group(1), 16)


def read_words(programmer, address, count):
    """count 32-bit words from address, read over SWD while the board runs."""
    output = subprocess.run(
        [str(programmer), "-c", "port=SWD", "mode=HOTPLUG", "-r32", hex(address),
         str(4 * count)], capture_output=True, text=True, check=True).stdout
    output = re.sub(r"\x1b\[[0-9;]*m", "", output)
    words = [int(word, 16) for line in output.splitlines()
             if re.match(r"0x[0-9A-F]+ :", line)
             for word in line.split(":", 1)[1].split()]
    if len(words) != count:
        raise SystemExit(f"read {len(words)} words of {count}")
    return words


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    project_dir, programmer = read_paths("project", "programmer")
    map_file = project_dir / "Release" / f"{project_name(project_dir)}.map"
    map_text = map_file.read_text()
    names = section_names()
    words = read_words(programmer, symbol_address(map_text, "section_cycles"), 2 * len(names))
    (hz,) = read_words(programmer, symbol_address(map_text, "SystemCoreClock"), 1)
    print(f"core clock {hz} Hz")
    for i, name in enumerate(names):
        fewest, most = words[2 * i], words[2 * i + 1]
        if fewest == NONE_SEEN:
            print(f"{name:28s} none")
            continue
        print(f"{name:28s} {fewest:>10d} to {most:>10d} cycles "
              f"{fewest * 1e6 / hz:>12.1f} to {most * 1e6 / hz:>12.1f} us")


if __name__ == "__main__":
    main()
