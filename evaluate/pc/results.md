# Results

The full run of `evaluate.run` over all 11,194 logs, at commit `c7cf191` on 2026-09-15.
It took about 6 hours 15 minutes with the caches reused, against about 9 minutes before
the nonlinear autoencoder was added. k, `HIDDEN` and `HOLD` are not chosen here, so
every value is reported.

```
python3 -u -m evaluate.run "data/part_*/*.csv" out
```

## Report

```
6585 train and 4609 test logs, 206977s and 69031s above the minimum speed
206849 calibration rows in 1293 stretches, the gap drops 118571 training rows
grid reused, train (3538312, 17)
attack set reused, 3975 attacks
moving rows: train 1760019, calibration 206227, test 689738. 862 attacks reach a moving row and moved it

17.5 hours above MIN_SPEED with no attack in them

                 detector   threshold  on clean test  epochs
                + pca k=2       9.332        0.00072
          + linear ae k=2       5.111        0.00072      14
  + nonlinear ae h=32 k=2       2.318        0.00069     440
  + nonlinear ae h=64 k=2       2.414        0.00066     500
 + nonlinear ae h=128 k=2       2.254        0.00062     478
                + pca k=4       6.409        0.00031
          + linear ae k=4       2.434        0.00030      14
  + nonlinear ae h=32 k=4      0.7424        0.00075     292
  + nonlinear ae h=64 k=4      0.7151        0.00097     500
 + nonlinear ae h=128 k=4      0.5413        0.00093     455
                + pca k=6       5.091        0.00090
          + linear ae k=6       1.512        0.00093      16
  + nonlinear ae h=32 k=6      0.2423        0.00080     262
  + nonlinear ae h=64 k=6      0.1612        0.00097     500
 + nonlinear ae h=128 k=6       0.157        0.00060     398
                + pca k=8       3.239        0.00067
          + linear ae k=8      0.6154        0.00065      33
  + nonlinear ae h=32 k=8     0.07506        0.00065     375
  + nonlinear ae h=64 k=8     0.04168        0.00073     425
 + nonlinear ae h=128 k=8     0.02731        0.00102     500
               + pca k=10       2.073        0.00137
         + linear ae k=10       0.252        0.00124      32
 + nonlinear ae h=32 k=10     0.02576        0.00071     500
 + nonlinear ae h=64 k=10     0.01884        0.00078     500
+ nonlinear ae h=128 k=10     0.01167        0.00065     481
               + pca k=12       1.416        0.01446
         + linear ae k=12      0.1195        0.01444      41
 + nonlinear ae h=32 k=12     0.01327        0.00060     243
 + nonlinear ae h=64 k=12    0.004554        0.00054     500
+ nonlinear ae h=128 k=12    0.001637        0.00067     500
               + pca k=14      0.6291        0.00096
         + linear ae k=14     0.02299        0.00095      38
 + nonlinear ae h=32 k=14   0.0001954        0.00204     261
 + nonlinear ae h=64 k=14   0.0002903        0.00102     220
+ nonlinear ae h=128 k=14   0.0001877        0.00116     169
               + pca k=16     0.02591        0.00075
         + linear ae k=16   4.068e-05        0.00075      59
 + nonlinear ae h=32 k=16   0.0001532        0.00130     139
 + nonlinear ae h=64 k=16    0.000148        0.00139      89
+ nonlinear ae h=128 k=16   9.607e-05        0.00136     220

                 detector    found in 1  found in 10     alarms/h 1   alarms/h 10
                    rules       448/862      373/862           34.4           0.2
                + pca k=2       450/862      374/862           39.8           0.9
          + linear ae k=2       450/862      374/862           39.6           0.9
  + nonlinear ae h=32 k=2       488/862      394/862           44.3           0.6
  + nonlinear ae h=64 k=2       474/862      388/862           44.2           0.5
 + nonlinear ae h=128 k=2       474/862      388/862           44.1           0.6
                + pca k=4       452/862      374/862           37.3           0.2
          + linear ae k=4       452/862      374/862           37.2           0.2
  + nonlinear ae h=32 k=4       512/862      413/862           47.9           0.3
  + nonlinear ae h=64 k=4       539/862      443/862           52.6           0.6
 + nonlinear ae h=128 k=4       562/862      452/862           53.3           0.3
                + pca k=6       458/862      380/862           44.9           0.4
          + linear ae k=6       459/862      381/862           45.1           0.5
  + nonlinear ae h=32 k=6       592/862      486/862           47.6           0.5
  + nonlinear ae h=64 k=6       637/862      533/862           45.3           0.7
 + nonlinear ae h=128 k=6       627/862      531/862           46.0           0.3
                + pca k=8       496/862      414/862           39.7           0.8
          + linear ae k=8       496/862      414/862           39.6           0.8
  + nonlinear ae h=32 k=8       659/862      544/862           44.7           0.3
  + nonlinear ae h=64 k=8       677/862      582/862           49.5           0.3
 + nonlinear ae h=128 k=8       745/862      671/862           54.8           0.6
               + pca k=10       570/862      464/862           46.7           1.0
         + linear ae k=10       570/862      464/862           45.4           0.9
 + nonlinear ae h=32 k=10       685/862      593/862           51.0           0.2
 + nonlinear ae h=64 k=10       712/862      620/862           54.1           0.3
+ nonlinear ae h=128 k=10       716/862      626/862           52.0           0.2
               + pca k=12       646/862      544/862           56.0           6.2
         + linear ae k=12       645/862      542/862           55.7           6.4
 + nonlinear ae h=32 k=12       670/862      546/862           50.8           0.2
 + nonlinear ae h=64 k=12       640/862      535/862           51.6           0.2
+ nonlinear ae h=128 k=12       689/862      592/862           49.6           0.5
               + pca k=14       636/862      534/862           46.7           0.9
         + linear ae k=14       636/862      536/862           46.6           0.8
 + nonlinear ae h=32 k=14       683/862      573/862           63.9           1.0
 + nonlinear ae h=64 k=14       736/862      638/862           55.6           0.4
+ nonlinear ae h=128 k=14       703/862      599/862           58.5           0.5
               + pca k=16       458/862      374/862           58.4           0.2
         + linear ae k=16       458/862      374/862           58.4           0.2
 + nonlinear ae h=32 k=16       723/862      623/862           63.3           0.3
 + nonlinear ae h=64 k=16       725/862      605/862           67.6           0.5
+ nonlinear ae h=128 k=16       646/862      534/862           58.2           0.5
```

## What it shows

Every PCA and linear autoencoder row repeats the run at `5c23300` exactly, so refitting
them in each run does not move them.

The threshold from the calibration rows holds `TARGET` 0.001 on clean test rows at six
of the eight k for PCA and the linear autoencoder. At k=10 PCA lets through 0.00137 and
the linear autoencoder 0.00124. At k=12 both let through about 0.0144, 14 times the
target, which shows as over 6 alarms per hour at 10 rows held.

The nonlinear autoencoder holds `TARGET` at 17 of its 24 fits, including k=10 and 12
where the other two do not. It misses at k=14 and 16 for every `HIDDEN`, letting through
up to 0.00204, and at k=8 with h=128, at 0.00102. At 10 rows held no nonlinear fit raises
more than 1.0 alarm per hour. At 1 row held they raise 44.1 to 67.6, against 34.4 for
the rules alone.

The autoencoder threshold is a mean squared error and PCA's is a residual norm. Squared
and divided by the 17 signals, PCA's threshold is within 3% of the linear autoencoder's
at every k. The nonlinear autoencoder's threshold is 2.1 to 123 times lower than the
linear one's at k=2 to 14, so it reconstructs the calibration rows more closely. At
k=16 it is 2.4 to 3.8 times higher.

Every linear fit stopped before `EPOCHS` 500, after 14 to 59 epochs. 8 of the 24
nonlinear fits ran to 500, so their rows are for a fit cut off by the cap rather than
one that stopped improving. The rest stopped after 89 to 481 epochs. `BATCH` 1024 was
carried over from the linear autoencoder and not compared for the nonlinear one.

| k | `HIDDEN` that ran to 500 epochs |
|---|---|
| 2 | 64 |
| 4 | 64 |
| 6 | 64 |
| 8 | 128 |
| 10 | 32, 64 |
| 12 | 64, 128 |

The linear autoencoder finds within 2 attacks of PCA at every k and both `HOLD`, with
alarms within 1.3 per hour. So the linear autoencoder matches PCA here.

At the same k and 10 rows held, the nonlinear autoencoder finds more attacks than the
linear one at 23 of its 24 fits. The gap is 14 to 20 attacks at k=2 and 39 to 257 at
k=4 to 10, for every `HIDDEN`. At k=12 it runs from 7 fewer to 50 more. At k=14 and 16 it
is 37 to 249 more, but there the nonlinear threshold misses `TARGET`, so that gain cannot
be read apart from the looser threshold. No `HIDDEN` finds the most at every k. At k=8
h=128 finds the most and h=32 the fewest, and at k=16 the order is reversed.

The rules alone find 373 of the 862 attacks at 10 rows held, at 0.2 alarms per hour.
Among the k whose threshold holds `TARGET`, PCA or the linear autoencoder adds almost
nothing at k=2, 4, 6 and 16 and up to 163 attacks at k=14. Among the nonlinear fits that
hold `TARGET` and stopped before the cap, the most found is 626 at k=10 with h=128, 253
more than the rules alone, at 0.2 alarms per hour.
