# Results

Every nonlinear autoencoder of `results/20260916-001002`, quantized to int8 and measured
against the model it was quantized from. The export is `quantize/20260916-221145`, made
at commit `8077570`.

```
python3 -u -m quantize.export "data/part_*/*.csv" out runs_clone 20260916-001002
python3 -u -m evaluate.quantize.compare "data/part_*/*.csv" out runs_clone 20260916-221145
```

Quantizing all 24 took 14 s. Measuring all 24 took 58 s, at 7.17 GB peak.

## What the measurement settles

None of these models needs quantizing to reach the board, so quantizing them only costs
detection. In float, the largest of the 24 takes 7.0% of the board's flash and 0.21% of
its SRAM. Going to int8 frees at most 20,550 B, which is 3.9% of a flash the float model
was already inside, and it spends 1,976 to 2,648 B more RAM to do it. At k=2 h=32 the
int8 build is 124 B larger than the float one.

What it costs is attacks, at every one of the 24 fits. Read against what a fit adds to
the 373 attacks the rules find on their own, the cheapest fits are k=8 and 10, at 1.3 to
6.4%: k=8 h=128 keeps 296 of the 300 it adds, k=10 h=128 keeps 241 of 253. The dearest
are k=2 and 4, where 52 to 100% of a small addition goes, k=4 h=128 keeping none of its
79. k=6 and 12 lose 13 to 41%. k=14 and 16 lose 98 to 145 attacks, though those k had
already missed `TARGET` in `results/20260916-001002`.

So int8 is for a model that does not fit in float, which none of these is. A windowed
model is where that could change, since its weights grow with the window.

If an int8 model is used, it needs the threshold taken from its own scores, 1.09 to 6.38
times the model's at k=2 to 12 and 31.7 to 112 times at k=14 and 16, which `export`
records in `meta.json`.

## Each model

Attacks found at 10 rows held, out of 862. `held TARGET` is whether that fit's threshold
held `TARGET` on the clean test rows of `results/20260916-001002`, from
[evaluate/results.md](../evaluate/results.md).

The rules find 373 of the 862 on their own, so what a fit adds is its `model` column
less 373, and what survives quantizing is its `int8` column less 373.

| k | h | model | int8 | lost | int8 threshold over the model's | held `TARGET` |
|---|---|---|---|---|---|---|
| 2 | 32 | 394 | 380 | 14 | 1.81 | yes |
| 2 | 64 | 390 | 381 | 9 | 1.28 | yes |
| 2 | 128 | 388 | 377 | 11 | 1.51 | yes |
| 4 | 32 | 413 | 392 | 21 | 1.73 | yes |
| 4 | 64 | 440 | 376 | 64 | 5.33 | yes |
| 4 | 128 | 452 | 373 | 79 | 6.38 | yes |
| 6 | 32 | 486 | 469 | 17 | 1.25 | yes |
| 6 | 64 | 530 | 466 | 64 | 2.01 | yes |
| 6 | 128 | 531 | 507 | 24 | 1.31 | yes |
| 8 | 32 | 544 | 533 | 11 | 1.09 | yes |
| 8 | 64 | 582 | 572 | 10 | 1.23 | yes |
| 8 | 128 | 673 | 669 | 4 | 1.24 | no |
| 10 | 32 | 596 | 573 | 23 | 1.53 | yes |
| 10 | 64 | 619 | 573 | 46 | 1.96 | yes |
| 10 | 128 | 626 | 614 | 12 | 1.49 | yes |
| 12 | 32 | 546 | 523 | 23 | 1.78 | yes |
| 12 | 64 | 530 | 508 | 22 | 2.19 | yes |
| 12 | 128 | 589 | 516 | 73 | 5.67 | yes |
| 14 | 32 | 573 | 439 | 134 | 112.25 | no |
| 14 | 64 | 638 | 529 | 109 | 33.07 | no |
| 14 | 128 | 599 | 501 | 98 | 31.73 | no |
| 16 | 32 | 623 | 497 | 126 | 42.84 | no |
| 16 | 64 | 605 | 460 | 145 | 51.77 | no |
| 16 | 128 | 534 | 398 | 136 | 49.39 | no |

Six fits lose more than 90 attacks, all at k=14 or 16. All six are among the seven that
missed `TARGET` in `results/20260916-001002`. The seventh, k=8 h=128, loses 4.

## The threshold

The model and the int8 file each take a threshold from the calibration rows of
`results/20260916-001002` at `TARGET`, from their own scores for those rows.

The widest pair is k=16 h=128, at 9.6e-05 for the model and 4.7e-03 for the int8 file.
[export](docs/export.md) records each int8 threshold in `meta.json`.

Why the int8 threshold divided by the model's threshold grows with k is not measured.

## The alarms

Alarms an hour at 10 rows held rise at three fits, by 0.4 at k=4 h=128, 0.1 at k=8 h=128
and 0.5 at k=10 h=64. They fall or hold at the other 21.

## What float costs

`stedgeai analyze --target stm32h5` on each float and int8 file of the export, with what
the ST runtime adds to each. The NUCLEO-H533RE carries 512 KB of flash and 272 KB of
SRAM, which is the datasheet rather than anything measured here.

| k | h | float flash | of flash | float ram | int8 flash | int8 ram |
|---|---|---|---|---|---|---|
| 2 | 32 | 7,106 B | 1.4% | 196 B | 7,230 B | 2,172 B |
| 2 | 64 | 12,234 B | 2.3% | 324 B | 9,022 B | 2,524 B |
| 2 | 128 | 22,474 B | 4.3% | 580 B | 12,610 B | 3,228 B |
| 4 | 32 | 7,626 B | 1.5% | 196 B | 7,376 B | 2,172 B |
| 4 | 64 | 13,262 B | 2.5% | 324 B | 9,296 B | 2,524 B |
| 4 | 128 | 24,526 B | 4.7% | 580 B | 13,140 B | 3,228 B |
| 6 | 32 | 8,146 B | 1.6% | 196 B | 7,522 B | 2,172 B |
| 6 | 64 | 14,298 B | 2.7% | 324 B | 9,570 B | 2,524 B |
| 6 | 128 | 26,586 B | 5.1% | 580 B | 13,670 B | 3,228 B |
| 8 | 32 | 8,666 B | 1.7% | 196 B | 7,668 B | 2,172 B |
| 8 | 64 | 15,326 B | 2.9% | 324 B | 9,844 B | 2,524 B |
| 8 | 128 | 28,642 B | 5.5% | 580 B | 14,196 B | 3,228 B |
| 10 | 32 | 9,190 B | 1.8% | 196 B | 7,814 B | 2,172 B |
| 10 | 64 | 16,362 B | 3.1% | 324 B | 10,118 B | 2,524 B |
| 10 | 128 | 30,698 B | 5.9% | 580 B | 14,730 B | 3,228 B |
| 12 | 32 | 9,710 B | 1.9% | 196 B | 7,960 B | 2,172 B |
| 12 | 64 | 17,394 B | 3.3% | 324 B | 10,396 B | 2,524 B |
| 12 | 128 | 32,754 B | 6.2% | 580 B | 15,264 B | 3,228 B |
| 14 | 32 | 10,234 B | 2.0% | 196 B | 8,106 B | 2,172 B |
| 14 | 64 | 18,426 B | 3.5% | 324 B | 10,670 B | 2,524 B |
| 14 | 128 | 34,810 B | 6.6% | 580 B | 15,794 B | 3,228 B |
| 16 | 32 | 10,746 B | 2.0% | 196 B | 8,252 B | 2,172 B |
| 16 | 64 | 19,450 B | 3.7% | 324 B | 10,940 B | 2,524 B |
| 16 | 128 | 36,866 B | 7.0% | 580 B | 16,316 B | 3,228 B |

Every float fit is inside the flash, the largest at 7.0% of it, and every one takes
0.21% or less of the SRAM.

Against that, int8 frees 250 to 20,550 B of flash at 23 of the 24 fits, and at k=2 h=32
it takes 124 B more than float. It spends 1,976 to 2,648 B more RAM at every fit,
because the int8 runtime carries more than the float one.

## Size on the board

The int8 files on their own, without the runtime the table above adds. `flash` is
`weights (ro)`, `ram` is `ram (total)`, and `macc` is one multiply-accumulate per
inference of one row.

| k | h | flash | ram | macc |
|---|---|---|---|---|
| 2 | 32 | 1,548 B | 408 B | 1,299 |
| 2 | 64 | 3,020 B | 760 B | 2,579 |
| 2 | 128 | 5,964 B | 1,464 B | 5,139 |
| 4 | 32 | 1,684 B | 408 B | 1,429 |
| 4 | 64 | 3,284 B | 760 B | 2,837 |
| 4 | 128 | 6,484 B | 1,464 B | 5,653 |
| 6 | 32 | 1,820 B | 408 B | 1,559 |
| 6 | 64 | 3,548 B | 760 B | 3,095 |
| 6 | 128 | 7,004 B | 1,464 B | 6,167 |
| 8 | 32 | 1,956 B | 408 B | 1,689 |
| 8 | 64 | 3,812 B | 760 B | 3,353 |
| 8 | 128 | 7,524 B | 1,464 B | 6,681 |
| 10 | 32 | 2,092 B | 408 B | 1,819 |
| 10 | 64 | 4,076 B | 760 B | 3,611 |
| 10 | 128 | 8,044 B | 1,464 B | 7,195 |
| 12 | 32 | 2,228 B | 408 B | 1,949 |
| 12 | 64 | 4,340 B | 760 B | 3,869 |
| 12 | 128 | 8,564 B | 1,464 B | 7,709 |
| 14 | 32 | 2,364 B | 408 B | 2,079 |
| 14 | 64 | 4,604 B | 760 B | 4,127 |
| 14 | 128 | 9,084 B | 1,464 B | 8,223 |
| 16 | 32 | 2,500 B | 408 B | 2,209 |
| 16 | 64 | 4,868 B | 760 B | 4,385 |
| 16 | 128 | 9,604 B | 1,464 B | 8,737 |

`h` sets the size. At one `h` the flash grows by 136 B, 264 B and 520 B per step of k,
and the ram does not move at all.

## What `evaluate.quantize.compare` printed

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

The `torch` rows match the run's own table.
