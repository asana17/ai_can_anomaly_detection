# Results

The full run of `evaluate.run` over all 11,194 logs, at commit `91ccaf2` on 2026-09-14.
k and `HOLD` are not chosen here, so every value is reported.

```
python3 -u -m evaluate.run "data/part_*/*.csv" out
```

## Report

```
6585 train and 4609 test logs, 206977s and 69031s above the minimum speed
206849 calibration rows in 1293 stretches, the gap drops 118571 training rows
grid reused, train (3538312, 17)
attack set in 1550s, 3975 attacks
moving rows: train 1760019, calibration 206227, test 689738. 862 attacks reach a moving row and moved it

17.5 hours above MIN_SPEED with no attack in them

   k   threshold  on clean test
   2      9.3319        0.00072
   4      6.4092        0.00031
   6      5.0906        0.00090
   8      3.2393        0.00067
  10      2.0726        0.00137
  12      1.4157        0.01446
  14      0.6291        0.00096
  16      0.0259        0.00075

   detector    found in 1  found in 10     alarms/h 1   alarms/h 10
      rules       448/862      373/862           34.4           0.2
  + pca k=2       450/862      374/862           39.8           0.9
  + pca k=4       452/862      374/862           37.3           0.2
  + pca k=6       458/862      380/862           44.9           0.4
  + pca k=8       496/862      414/862           39.7           0.8
 + pca k=10       570/862      464/862           46.7           1.0
 + pca k=12       646/862      544/862           56.0           6.2
 + pca k=14       636/862      534/862           46.7           0.9
 + pca k=16       458/862      374/862           58.4           0.2
```

## What it shows

The threshold from the calibration rows holds `TARGET` 0.001 on clean test rows at six
of the eight k. At k=10 it lets through 0.00137. At k=12 it lets through 0.01446, about
14 times the target, so the detections k=12 adds come with false alarms the other k do
not pay, which shows as 6.2 alarms per hour at 10 rows held.

The rules alone find 373 of the 862 attacks at 10 rows held, at 0.2 alarms per hour.
Among the k whose threshold holds `TARGET`, PCA adds almost nothing at k=2, 4, 6 and 16
and adds up to 161 attacks at k=14, while alarms stay under one per hour at 10 rows held.
