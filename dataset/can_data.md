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
  part_1/   ~2,800 logs
  part_2/   ~2,800 logs
  part_3/   ~2,800 logs
  part_4/   ~2,800 logs
```

- **~11,194 logs** total.
- Each log holds exactly **50,001 frames** (1,200 of 1,200 sampled).
- Total on the order of **~560 million CAN frames**.

Each log is an independent capture, but a log is **not** guaranteed to be
contiguous in time. The recorder can stop and resume inside one, leaving a single
long gap in an otherwise ordinary log.

| span of one log | share of logs |
|------------------|----------------|
| about 59 s (p1 to p90 span 58.6 to 59.4 s) | about 98% |
| over 2 minutes  | 2.2% |
| over 10 minutes | 1.6% |
| over 1 hour     | 0.8% |

So a typical log covers about **one minute** at roughly 850 frames per second. The
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
from the payload bytes with a fixed scale and offset.

Field definitions come from two places. The
[FMS-Standard description](https://www.fms-standard.com/Truck/down_load/fms%20document_v_05_vers.07.07.2024.pdf)
is free and defines the interface this data was recorded from, giving the byte and
bit position, resolution, offset and repetition rate of every parameter it covers.
It defines 43 PGNs, 19 of which are on this bus, carrying 28.6% of the frames.
Everything outside that set needs SAE J1939-71, which is not free.

What profiling the logs found is in [measurements](measurements.md).
