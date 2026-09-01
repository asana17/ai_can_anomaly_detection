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
- Each file is a contiguous recording of **~10 minutes / ~50,000 rows**.
- Total on the order of **~560 million CAN frames**.

Each file is an independent, time-contiguous capture. This matters for the
train/val/test split. We split at **file granularity in chronological order**
(no shuffling) to avoid temporal leakage.

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

## Profiling findings (one `part_1` file, ~50k rows, ~10 min)

- **57 unique PGNs**, **10 source addresses**.
- Source address **`230`** produces ~78% of frames (the main powertrain ECU).
- DLC distribution: `8` (vast majority), `4`, `1`, `3`.
- **Target SPNs are present** (message, PGN):
  - `EEC1` (61444), engine speed and engine torque
  - `EEC2` (61443), accelerator pedal and engine percent load
  - `CCVS1` (65265), wheel-based vehicle speed and brake switch
  - `LFE1` (65266), engine fuel rate and instantaneous fuel economy
- **`ETC2` (65234) is absent.** Selected gear is not available from this PGN, so
  it must come from another PGN or be dropped.
- **Multi-packet transport (TP) exists but is negligible.** TP.CM (60416) and
  TP.DT (60160) appear in small counts and do **not** carry the target SPNs. No
  reassembly is needed, so these PGNs are simply added to the whitelist.

Per-file PGN frequencies are measured, not assumed (e.g. EEC1 is about 5 Hz in
the sampled file, not the textbook 20 ms). **Per-PGN period baselines are
therefore measured from the training data**, not taken from the J1939 nominal
periods.

## Implications for preprocessing

1. **Decode keys on the PGN, and priority and SA are kept.** The payload meaning
   is set by the PGN alone (the same PGN has the same signal layout regardless of
   source or priority), so the decode lookup uses the PGN only. Priority and
   source address are retained and used by the downstream rule layer to sort
   anomalies (spoofing from SA, DoS from priority and timing, and so on).
2. **Measure statistics from training data only.** Normalization ranges, per-PGN
   period baselines, and the detector threshold are all fit on the training split
   and then applied to val and test, to avoid leakage.
3. **Split chronologically at file granularity.** No shuffling. Default is
   `part_1..part_3` for train and val, `part_4` for test.
4. **Anomalies are injected only into the test split.** Training and validation
   see normal traffic exclusively.
5. **Skip TP reassembly.** Whitelist the TP PGNs, and revisit only if a target SPN
   is ever found inside a multi-packet message.

The chronological split has two caveats. Validation is a short continuous slice of
time, enough to set a threshold but not to cover every driving condition. Train and
test fall in different seasons, so some normal drift between them is expected, which
can raise false positives.
