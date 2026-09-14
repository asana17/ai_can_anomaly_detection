# Results

The full run of `evaluate.run` over all 11,194 logs, at commit `5c23300` on 2026-09-15.
k and `HOLD` are not chosen here, so every value is reported.

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
       + pca k=4       6.409        0.00031
 + linear ae k=4       2.434        0.00030      14
       + pca k=6       5.091        0.00090
 + linear ae k=6       1.512        0.00093      16
       + pca k=8       3.239        0.00067
 + linear ae k=8      0.6154        0.00065      33
      + pca k=10       2.073        0.00137
+ linear ae k=10       0.252        0.00124      32
      + pca k=12       1.416        0.01446
+ linear ae k=12      0.1195        0.01444      41
      + pca k=14      0.6291        0.00096
+ linear ae k=14     0.02299        0.00095      38
      + pca k=16     0.02591        0.00075
+ linear ae k=16   4.068e-05        0.00075      59

        detector    found in 1  found in 10     alarms/h 1   alarms/h 10
           rules       448/862      373/862           34.4           0.2
       + pca k=2       450/862      374/862           39.8           0.9
 + linear ae k=2       450/862      374/862           39.6           0.9
       + pca k=4       452/862      374/862           37.3           0.2
 + linear ae k=4       452/862      374/862           37.2           0.2
       + pca k=6       458/862      380/862           44.9           0.4
 + linear ae k=6       459/862      381/862           45.1           0.5
       + pca k=8       496/862      414/862           39.7           0.8
 + linear ae k=8       496/862      414/862           39.6           0.8
      + pca k=10       570/862      464/862           46.7           1.0
+ linear ae k=10       570/862      464/862           45.4           0.9
      + pca k=12       646/862      544/862           56.0           6.2
+ linear ae k=12       645/862      542/862           55.7           6.4
      + pca k=14       636/862      534/862           46.7           0.9
+ linear ae k=14       636/862      536/862           46.6           0.8
      + pca k=16       458/862      374/862           58.4           0.2
+ linear ae k=16       458/862      374/862           58.4           0.2
```

## What it shows

The threshold from the calibration rows holds `TARGET` 0.001 on clean test rows at six
of the eight k, the same six for PCA and the linear autoencoder. At k=10 PCA lets through
0.00137 and the autoencoder 0.00124. At k=12 both let through about 0.0144, 14 times the
target, which shows as over 6 alarms per hour at 10 rows held.

The autoencoder threshold is a mean squared error and PCA's is a residual norm. Squared
and divided by the 17 signals, PCA's threshold is within 3% of the autoencoder's at every
k. Every autoencoder fit stopped before `EPOCHS` 500, after 14 to 59 epochs.

The linear autoencoder finds within 2 attacks of PCA at every k and both `HOLD`, with
alarms within 1.3 per hour. So the autoencoder matches PCA here.

The rules alone find 373 of the 862 attacks at 10 rows held, at 0.2 alarms per hour.
Among the k whose threshold holds `TARGET`, either model adds almost nothing at k=2, 4, 6
and 16 and adds up to 163 attacks at k=14, while alarms stay under one per hour at 10 rows
held.
