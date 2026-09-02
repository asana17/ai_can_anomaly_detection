# summary

Folds a set of logs into one set of counts. This is how the profiling findings in
[can_data](../../docs/can_data.md) were measured, so those numbers can be checked or
measured again on other files.

```python
summarize(paths)          # -> Profile, every log in paths folded together
report(profile)           # -> str, the totals and a row per PGN
public_pgns(profile)      # -> [pgn, ...] that have published SPN definitions
pgn_gap(profile, pgn)     # -> seconds, median gap of that PGN's fastest sender
median_gap(bucket)        # -> seconds, median of one bucketed stream
```

`Profile` carries the counts themselves, so a caller can read them instead of
parsing them back out of the report.

```python
files, frames       # how many logs, and how many frames in them
pgn_frames          # Counter of pgn -> frames
pgn_files           # Counter of pgn -> logs it appears in
sender_frames       # Counter of source address -> frames
dlc_frames          # Counter of payload length -> frames
pgns_per_file       # distinct PGNs in each log, ascending
gaps                # {(pgn, sender): Counter of bucketed gap -> count}
```

## Running it

```
python3 -m preprocess.profile.summary data/part_*/*.csv
```

For the 1,200 file sample behind can_data:

```
1200 files, 60,001,200 frames, 57 PGNs
per file 52 to 57 PGNs, median 55, 52 in every file
public 41 PGNs at 76.1% of frames, proprietary 16 at 23.9%
dlc 8 98.22%, 4 1.19%, 1 0.59%, 3 0.00%
senders 230 75.94%, 232 3.92%, 192 3.55%, 200 3.55%, 184 3.55%, 168 3.55%

    PGN     hex   frames   files       gap  kind
  65408  0xff80  12.406%    100%    10.0ms  proprietary
  61449  0xf009  11.817%    100%     9.8ms  public
  ...
```

Each row is one PGN. `frames` is its share of all frames, `files` the share of logs
it appears in, `gap` the median time between its frames, and `kind` whether it has
published SPN definitions and so can be decoded ([pgn_classify](pgn_classify.md)).

## Details

It reuses [pgn_counts](pgn_counts.md), [pgn_intervals](pgn_intervals.md) and
[pgn_classify](pgn_classify.md), reading each log once and walking it in memory.

Holding on to every arrival gap of a large sweep would not fit in memory, so `gaps`
rounds each one to 0.1 ms and counts how often that value comes up. A message sent
on a fixed period falls into one or two of those counts, which is enough to take a
median from.

`pgn_gap` reports the fastest sender of a PGN, since several ECUs can send the same
PGN at rates of their own.
