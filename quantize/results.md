# Results

Every nonlinear autoencoder of `results/20260916-001002`, quantized to int8 and measured
against the model it was quantized from. The export is `quantize/20260916-221145`, made
at commit `8077570`.

```
python3 -u -m quantize.export "data/part_*/*.csv" out runs_clone 20260916-001002
python3 -u -m evaluate.quantize.compare "data/part_*/*.csv" out runs_clone 20260916-221145
```

Quantizing all 24 took 14 s. Measuring all 24 took 58 s, at 7.17 GB peak.

## Report

```
206227 calibration rows, 862 attacks scored in 17.5 hours

       model  source     threshold   found in 1  found in 10     alarms/h 1   alarms/h 10
    k=2 h=32   torch       2.31778      488/862      394/862           44.3           0.6
    k=2 h=32    int8       4.19706      475/862      380/862           53.3           0.2
    k=2 h=64   torch       2.36104      480/862      390/862           44.9           0.5
    k=2 h=64    int8       3.03061      478/862      381/862           52.5           0.4
   k=2 h=128   torch       2.25355      474/862      388/862           44.1           0.6
   k=2 h=128    int8       3.40605      483/862      377/862           58.0           0.3
    k=4 h=32   torch      0.742422      512/862      413/862           47.9           0.3
    k=4 h=32    int8       1.28722      501/862      392/862           64.6           0.2
    k=4 h=64   torch      0.719221      540/862      440/862           51.3           0.5
    k=4 h=64    int8       3.83418      467/862      376/862           57.9           0.2
   k=4 h=128   torch      0.541297      562/862      452/862           53.3           0.3
   k=4 h=128    int8       3.45551      454/862      373/862           43.8           0.7
    k=6 h=32   torch      0.242289      592/862      486/862           47.6           0.5
    k=6 h=32    int8      0.302905      582/862      469/862           48.8           0.2
    k=6 h=64   torch      0.163445      637/862      530/862           44.9           0.6
    k=6 h=64    int8      0.328649      583/862      466/862           49.9           0.2
   k=6 h=128   torch      0.157038      627/862      531/862           46.0           0.3
   k=6 h=128    int8      0.206131      628/862      507/862           47.3           0.3
    k=8 h=32   torch     0.0750598      659/862      544/862           44.7           0.3
    k=8 h=32    int8     0.0816887      665/862      533/862           45.8           0.3
    k=8 h=64   torch     0.0416793      677/862      582/862           49.5           0.3
    k=8 h=64    int8     0.0513921      684/862      572/862           53.3           0.3
   k=8 h=128   torch      0.025155      748/862      673/862           56.9           0.5
   k=8 h=128    int8     0.0312421      752/862      669/862           56.5           0.6
   k=10 h=32   torch     0.0252666      686/862      596/862           51.3           0.2
   k=10 h=32    int8     0.0385444      700/862      573/862           52.6           0.2
   k=10 h=64   torch     0.0173544      706/862      619/862           51.9           0.3
   k=10 h=64    int8     0.0339411      684/862      573/862           61.8           0.8
  k=10 h=128   torch     0.0116674      716/862      626/862           52.0           0.2
  k=10 h=128    int8     0.0173599      717/862      614/862           51.6           0.2
   k=12 h=32   torch     0.0132703      670/862      546/862           50.8           0.2
   k=12 h=32    int8     0.0235638      688/862      523/862           54.2           0.2
   k=12 h=64   torch    0.00443183      636/862      530/862           52.0           0.2
   k=12 h=64    int8    0.00972391      644/862      508/862           55.4           0.2
  k=12 h=128   torch    0.00156856      692/862      589/862           50.6           0.5
  k=12 h=128    int8    0.00889354      643/862      516/862           67.1           0.2
   k=14 h=32   torch   0.000195394      683/862      573/862           63.9           1.0
   k=14 h=32    int8     0.0219332      579/862      439/862           58.8           0.2
   k=14 h=64   torch   0.000290325      736/862      638/862           55.6           0.4
   k=14 h=64    int8    0.00960079      671/862      529/862           67.2           0.3
  k=14 h=128   torch   0.000187746      703/862      599/862           58.5           0.5
  k=14 h=128    int8    0.00595752      649/862      501/862           80.1           0.2
   k=16 h=32   torch   0.000153236      723/862      623/862           63.3           0.3
   k=16 h=32    int8    0.00656528      660/862      497/862           71.8           0.2
   k=16 h=64   torch   0.000148013      725/862      605/862           67.6           0.5
   k=16 h=64    int8    0.00766309      630/862      460/862           70.7           0.2
  k=16 h=128   torch   9.60747e-05      646/862      534/862           58.2           0.5
  k=16 h=128    int8    0.00474523      563/862      398/862           76.1           0.2
```

The `torch` rows repeat the run's own table, which is the check that the rows and the
counting here are the run's.

## The int8 file needs its own threshold

Every int8 file thresholds above the model it came from, and the gap widens with k.

| k | int8 threshold over the model's |
|---|---|
| 2 to 10 | 1.09 to 2.01 times, except 5.33 at k=4 h=64 and 6.38 at k=4 h=128 |
| 12 | 1.78 to 5.67 times |
| 14 | 31.7 to 112 times |
| 16 | 42.8 to 51.8 times |

At k=16 h=128 the model thresholds at 9.6e-05 and the int8 file at 4.7e-03. A board
given the model's threshold there would flag almost every row. So the threshold of the
int8 file's own calibration scores is what a board has to be given, and
[export](docs/export.md) records it in `meta.json`.

Why the gap widens with k is not measured. A larger `latent_dim` leaves less to
reconstruct, so the model's scores fall towards 1e-4, while the error int8 adds does
not fall with them.

## What the quantization costs

Both sides hold their own threshold, so what is left between the two rows is detection.

| k | attacks lost at 10 rows held, out of 862 |
|---|---|
| 2 | 9 to 14 |
| 4 | 21 to 79 |
| 6 | 17 to 64 |
| 8 | 4 to 11 |
| 10 | 12 to 46 |
| 12 | 22 to 73 |
| 14 | 98 to 134 |
| 16 | 126 to 145 |

The worst is k=16 h=64, from 605 to 460. Every fit loses something and none gains.

Alarms an hour at 10 rows held rise at three fits, by 0.4 at k=4 h=128, 0.1 at k=8
h=128 and 0.5 at k=10 h=64. They fall or hold at the other 21. So the losses are not
bought back by a looser threshold anywhere.

The fit that finds the most, k=8 h=128 at 673, keeps 669. k=8 loses least of all the k,
4 to 11 attacks. The large k lose most, and those are the k the run already reports as
missing `TARGET`.

## Size on the board

`stedgeai analyze --target stm32h5` on k=8 h=64, from an earlier export of the same
weights.

| | float | int8 |
|---|---|---|
| flash | 13,412 B | 3,812 B |
| RAM | 324 B | 760 B |
| macc | 3,481 | 3,353 |

The int8 file needs more RAM because it holds the quantized and dequantized buffers at
once. The model has 3,353 parameters, which is 36h + 2hk + k + 17 at k=8 h=64.
