"""Print the fewest and most cycles of each part the running board keeps in `section_cycles`.

    python3 -m board.application.ai_can_anomaly_detection.read_section_cycles [--over SECONDS]

It reads `section_cycles` and `SystemCoreClock` over SWD without stopping the board, at
the addresses in the map file of the project in `board/paths.json`. It names the parts
from `Section` in `section_cycles.h` and prints each in cycles and in us.
With SECONDS it reads the total cycles of each part and the DWT cycle counter, waits,
reads them again, and prints each part's share of the CPU in between. SECONDS must stay
below one turn of the counter.
"""

import argparse
import re
import subprocess
import time

from board.flash import project_name
from board.paths import read_paths
from board.pc_answer import LIB

SECTION_CYCLES = LIB / "section_cycles" / "section_cycles.h"
NONE_SEEN = 0xFFFFFFFF  # what section_cycles_clear() sets fewest to
SECTION_WORDS = 4       # fewest, most and the two words of total in SectionCycles
DWT_CYCCNT = 0xE0001004
COUNTER_TURN = 1 << 32


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


def read_words(programmer, *reads):
    """For each (address, count) in reads, count 32-bit words from address, all read in
    one SWD connection while the board runs."""
    command = [str(programmer), "-c", "port=SWD", "mode=HOTPLUG"]
    for address, count in reads:
        command += ["-r32", hex(address), str(4 * count)]
    output = subprocess.run(command, capture_output=True, text=True, check=True).stdout
    output = re.sub(r"\x1b\[[0-9;]*m", "", output)
    words = [int(word, 16) for line in output.splitlines()
             if re.match(r"0x[0-9A-F]+ :", line)
             for word in line.split(":", 1)[1].split()]
    if len(words) != sum(count for _, count in reads):
        raise SystemExit(f"read {len(words)} words of {sum(count for _, count in reads)}")
    blocks = []
    for _, count in reads:
        blocks.append(words[:count])
        words = words[count:]
    return blocks


def totals(words, names):
    """The total cycles of each part, from the words of `section_cycles`."""
    return [words[SECTION_WORDS * i + 2] | words[SECTION_WORDS * i + 3] << 32
            for i in range(len(names))]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--over", type=float, metavar="SECONDS",
                        help="print each part's share of the CPU over this many seconds")
    args = parser.parse_args()
    project_dir, programmer = read_paths("project", "programmer")
    map_file = project_dir / "Release" / f"{project_name(project_dir)}.map"
    map_text = map_file.read_text()
    names = section_names()
    sections = (symbol_address(map_text, "section_cycles"), SECTION_WORDS * len(names))
    ((hz,),) = read_words(programmer, (symbol_address(map_text, "SystemCoreClock"), 1))
    print(f"core clock {hz} Hz")
    if args.over is not None:
        if args.over * hz >= COUNTER_TURN:
            raise SystemExit(f"--over must stay below {COUNTER_TURN / hz:.0f} s")
        (counter_before,), words_before = read_words(programmer, (DWT_CYCCNT, 1), sections)
        time.sleep(args.over)
        (counter_after,), words = read_words(programmer, (DWT_CYCCNT, 1), sections)
        elapsed = (counter_after - counter_before) % COUNTER_TURN
        spent = [after - before for before, after
                 in zip(totals(words_before, names), totals(words, names))]
        print(f"share of the CPU over {elapsed / hz:.2f} s")
    else:
        (words,) = read_words(programmer, sections)
    for i, name in enumerate(names):
        fewest, most = words[SECTION_WORDS * i], words[SECTION_WORDS * i + 1]
        if fewest == NONE_SEEN:
            print(f"{name:28s} none")
            continue
        line = (f"{name:28s} {fewest:>10d} to {most:>10d} cycles "
                f"{fewest * 1e6 / hz:>12.1f} to {most * 1e6 / hz:>12.1f} us")
        if args.over is not None:
            line += f" {100 * spent[i] / elapsed:>8.3f} %"
        print(line)


if __name__ == "__main__":
    main()
