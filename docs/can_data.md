# CAN Bus Dataset

Reference description of the raw CAN data used in this project. It records what
the data is, how it is laid out, and what we learned from profiling it.

日本語版: [`can_data.ja.md`](can_data.ja.md)

## Source

- **Vehicle**: Renault Euro VI heavy-duty truck (single vehicle).
- **Collection**: real on-road driving (not a dynamometer).
- **Standard**: SAE J1939 / FMS, 250 kbit/s, all data frames, extended (29-bit) IDs.
- **Content**: normal traffic only. There are no attacks or anomalies in the recordings.
- **Origin**: University of Turku J1939 truck dataset.
  https://etsin.fairdata.fi/dataset/7586f24f-c91b-41df-92af-283524de8b3e/data

## On-disk layout

```
data/
  part_1/   ~2,800 CSV files
  part_2/   ~2,800 CSV files
  part_3/   ~2,800 CSV files
  part_4/   ~2,800 CSV files
```

- **~11,194 CSV files** total.
- Each file holds exactly **50,001 rows** (1,200 of 1,200 sampled files).
- Total on the order of **~560 million CAN frames**.

Each file is an independent capture, but a file is **not** guaranteed to be
contiguous in time. The recorder can stop and resume inside one, leaving a single
long gap in an otherwise ordinary log.

| span of one file | share of files |
|------------------|----------------|
| about 59 s (p1 to p90 span 58.6 to 59.4 s) | about 98% |
| over 2 minutes  | 2.2% |
| over 10 minutes | 1.6% |
| over 1 hour     | 0.8% |

So a typical file covers about **one minute** at roughly 850 frames per second. The
longest sampled spans **70.8 hours**, its 50,001 frames split either side of one
70.6 hour gap.

## CSV format

Semicolon-separated, one CAN frame per row, with a header line.

```
timestamp;id;dlc;data
2020-11-23 08:03:31.985194;0x10ff80e6;8;0;0;251;109;240;144;255;255
2020-11-23 08:03:31.988986;0x1cff80e6;1;230
```

| Column      | Meaning                                                         |
|-------------|----------------------------------------------------------------|
| `timestamp` | `YYYY-MM-DD HH:MM:SS.ffffff`, microsecond resolution           |
| `id`        | 29-bit extended arbitration ID, hex (e.g. `0x18f004e6`)        |
| `dlc`       | data length in bytes (mostly 8; also 1, 3, 4 observed)         |
| `data`      | `dlc` **decimal** byte values (0 to 255), each in its own column |

The first 3 columns (`timestamp`, `id`, `dlc`) are fixed, followed by exactly
`dlc` data bytes. So the total number of columns in a row is `3 + dlc`.

- e.g. `dlc=8` gives 3 + 8 = **11 columns** (data bytes are columns 4 to 11)
- e.g. `dlc=1` gives 3 + 1 = **4 columns** (a single data byte in column 4)

The data bytes start at the 4th column, and their values are decimal, **not** hex.

## Identifiers and signals

How a 29-bit identifier decomposes into a PGN (message type) and a source address
is documented with the code in
[preprocess/docs/can_id_decompose.md](../preprocess/docs/can_id_decompose.md).
A PGN carries one or more SPNs (individual signals such as engine speed), decoded
from the payload bytes with a fixed scale and offset. Full field definitions are
in the SAE J1939 standard.

## Profiling findings (1,200 files across all four parts, 60,001,200 frames)

- **57 unique PGNs.** One file carries 52 to 57 of them (median 55), and 52 appear
  in every file. **10 source addresses**, of which `230`, the main powertrain ECU,
  sends 75.9% of all frames. The next five send 3.5 to 3.9% each.
- DLC distribution: `8` is **98.22%**, then `4` 1.19%, `1` 0.59%, `3` under 0.01%.
- **41 PGNs are public and 16 are proprietary**, carrying 76.1% and 23.9% of frames.
  The proprietary ones have no published SPN definitions, so they cannot be decoded.
  See [pgn_classify](../preprocess/docs/pgn_classify.md).
- **EEC1, EEC2, CCVS1 and LFE1 are in 100% of files** (share of frames, rate):
  - `EEC1` (61444), 5.91%, every 20 ms, engine speed and engine torque
  - `EEC2` (61443), 2.36%, every 50 ms, accelerator pedal and engine percent load
  - `CCVS1` (65265), 1.18%, every 100 ms, wheel based vehicle speed
  - `LFE1` (65266), 1.18%, every 100 ms, engine fuel rate
- `ETC2` (61445) is in every file at 10 Hz, carrying SPN 524 selected gear and SPN
  523 current gear. Observed values are `-1` reverse, `0` neutral and `1` to `12`,
  with `0xFF` not available in 0.68% of frames.
- **Multi packet transport is small and always present.** TP.CM (60416) is 0.25% of
  frames and TP.DT (60160) is 0.74%. Neither carries the target SPNs.

Rates are the median gap per (PGN, source address) stream, not frames divided by
file duration. The latter understates any file that contains a gap, which is how an
earlier profile of one file put EEC1 at 5 Hz instead of its actual 50 Hz.
