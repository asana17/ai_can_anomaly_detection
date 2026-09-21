# Results

Two full runs over all 11,194 logs, on 2026-09-16. They differ only in `TORCH_SEED`.

| called here | recorded as | `TORCH_SEED` | commit | took | peak memory |
|---|---|---|---|---|---|
| run 1 | `results/20260916-001002` | 0 | `c997f8c` | 6 h 36 min | 6.21 GB |
| run 2 | `results/20260916-064753` | 1 | `4329c2a` | 6 h 27 min | 6.22 GB |

`4329c2a` changes `TORCH_SEED` and nothing else. k, `HIDDEN` and `HOLD` are not chosen
here, so every value is reported.

```
python3 -u -m evaluate.pc.run "data/part_*/*.csv" out runs_clone
```

## What the two runs settle

The nonlinear autoencoder is the one worth adding to the rules. The rules find 373 of
the 862 attacks on their own at 10 rows held. The best nonlinear fit holding `TARGET`
adds 253 to that in run 1 and 274 in run 2, at the rules' own 0.2 alarms an hour, while
PCA and the linear autoencoder add at most 163 and 164 and stay within 2 attacks of each
other everywhere.

Changing `TORCH_SEED` does not disturb that. It moves a single fit by up to 66 attacks,
which is well short of the 253 and 274, so the second run repeats the finding rather
than qualifying it.

These runs do not say which k and `HIDDEN` to take. Two `HIDDEN` at one k differ by up
to 129 attacks, the seed moves one fit by up to 66, and 5 of the 24 fits changed whether
they hold `TARGET` between the runs. Picking one of them needs more runs than two.

## Run 1

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
  + nonlinear ae h=64 k=2       2.361        0.00064     613
 + nonlinear ae h=128 k=2       2.254        0.00062     478
                + pca k=4       6.409        0.00031
          + linear ae k=4       2.434        0.00030      14
  + nonlinear ae h=32 k=4      0.7424        0.00075     292
  + nonlinear ae h=64 k=4      0.7192        0.00090     555
 + nonlinear ae h=128 k=4      0.5413        0.00093     455
                + pca k=6       5.091        0.00090
          + linear ae k=6       1.512        0.00093      16
  + nonlinear ae h=32 k=6      0.2423        0.00080     262
  + nonlinear ae h=64 k=6      0.1634        0.00092     566
 + nonlinear ae h=128 k=6       0.157        0.00060     398
                + pca k=8       3.239        0.00067
          + linear ae k=8      0.6154        0.00065      33
  + nonlinear ae h=32 k=8     0.07506        0.00065     375
  + nonlinear ae h=64 k=8     0.04168        0.00073     425
 + nonlinear ae h=128 k=8     0.02515        0.00103     729
               + pca k=10       2.073        0.00137
         + linear ae k=10       0.252        0.00124      32
 + nonlinear ae h=32 k=10     0.02527        0.00073     583
 + nonlinear ae h=64 k=10     0.01735        0.00072     750
+ nonlinear ae h=128 k=10     0.01167        0.00065     481
               + pca k=12       1.416        0.01446
         + linear ae k=12      0.1195        0.01444      41
 + nonlinear ae h=32 k=12     0.01327        0.00060     243
 + nonlinear ae h=64 k=12    0.004432        0.00055     550
+ nonlinear ae h=128 k=12    0.001569        0.00071     503
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
  + nonlinear ae h=64 k=2       480/862      390/862           44.9           0.5
 + nonlinear ae h=128 k=2       474/862      388/862           44.1           0.6
                + pca k=4       452/862      374/862           37.3           0.2
          + linear ae k=4       452/862      374/862           37.2           0.2
  + nonlinear ae h=32 k=4       512/862      413/862           47.9           0.3
  + nonlinear ae h=64 k=4       540/862      440/862           51.3           0.5
 + nonlinear ae h=128 k=4       562/862      452/862           53.3           0.3
                + pca k=6       458/862      380/862           44.9           0.4
          + linear ae k=6       459/862      381/862           45.1           0.5
  + nonlinear ae h=32 k=6       592/862      486/862           47.6           0.5
  + nonlinear ae h=64 k=6       637/862      530/862           44.9           0.6
 + nonlinear ae h=128 k=6       627/862      531/862           46.0           0.3
                + pca k=8       496/862      414/862           39.7           0.8
          + linear ae k=8       496/862      414/862           39.6           0.8
  + nonlinear ae h=32 k=8       659/862      544/862           44.7           0.3
  + nonlinear ae h=64 k=8       677/862      582/862           49.5           0.3
 + nonlinear ae h=128 k=8       748/862      673/862           56.9           0.5
               + pca k=10       570/862      464/862           46.7           1.0
         + linear ae k=10       570/862      464/862           45.4           0.9
 + nonlinear ae h=32 k=10       686/862      596/862           51.3           0.2
 + nonlinear ae h=64 k=10       706/862      619/862           51.9           0.3
+ nonlinear ae h=128 k=10       716/862      626/862           52.0           0.2
               + pca k=12       646/862      544/862           56.0           6.2
         + linear ae k=12       645/862      542/862           55.7           6.4
 + nonlinear ae h=32 k=12       670/862      546/862           50.8           0.2
 + nonlinear ae h=64 k=12       636/862      530/862           52.0           0.2
+ nonlinear ae h=128 k=12       692/862      589/862           50.6           0.5
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

## Every fit stopped on its own

No fit of either run reached `EPOCHS` 1000. In run 1 the longest nonlinear fit
ran 750 epochs, at k=10 h=64, and the linear fits ran 14 to 59.

## The thresholds

The `threshold` column comes from the calibration rows at `TARGET` 0.001. The
`on clean test` column is the share of clean test rows above that threshold.

The nonlinear autoencoder holds `TARGET` at 17 of its 24 fits. It misses at k=14 and
16 for every `HIDDEN`, letting through up to 0.00204, and at k=8 with h=128, at
0.00103.

PCA and the linear autoencoder hold `TARGET` at six of the eight k. At k=10 PCA lets through
0.00137 and the linear autoencoder 0.00124. At k=12 both let through about 0.0144,
14.5 times the target, at 6.2 and 6.4 alarms an hour at 10 rows held.

## What the models add to the rules

The rules alone find 373 of the 862 attacks at 10 rows held, at 0.2 alarms an hour.

PCA and the linear autoencoder stay within 2 attacks of each other at every k and both
`HOLD`. Among the k whose threshold holds `TARGET`, the linear autoencoder adds 1
attack at k=2, 4 and 16, 8 at k=6, 41 at k=8 and 163 at k=14.

Among the nonlinear fits that hold `TARGET`, the most found at 10 rows held is 626, at
k=10 with h=128, 253 more than the rules alone, at 0.2 alarms an hour.

## What run 2 changes

| | run 1 | run 2 |
|---|---|---|
| fits holding `TARGET` | 17 of 24 | 16 of 24 |
| longest nonlinear fit | 750 epochs | 625 epochs |
| linear fits | 14 to 59 epochs | 14 to 72 epochs |

Five fits crossed `TARGET` between the runs. h=32 k=2, h=128 k=2 and h=32 k=8 stopped
holding `TARGET`, and h=128 k=8 and h=128 k=14 started. The largest change is h=32 k=8,
which goes from 0.00065 to 0.00523, five times the target, and from 0.3 to 2.0 alarms
an hour at 10 rows held.

Attacks found at 10 rows held move by 18.2 on average and by up to 66, at h=64 k=12.
PCA finds exactly what it found in run 1. The linear autoencoder moves by at most 3
attacks between the runs, since `TORCH_SEED` sets its initial weights too.

The largest gap between two `HIDDEN` at the same k in run 1 is 129 attacks, at k=8. The
seed moves a single fit by up to 66.
