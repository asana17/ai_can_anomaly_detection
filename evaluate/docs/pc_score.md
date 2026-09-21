# pc score

`score` counts the attacks each detector catches on the attacked test rows. A detector
is the instant rules, or the rules together with one model. The models and their thresholds
come from a directory [calibrate](calibrate.md) wrote, so nothing is fitted or
thresholded here.

An [attack set](../../assemble/docs/attack_set.md) holds two things: the attacked test
logs as rows on the grid, and the same logs as CAN frames. `score` reads the rows. The
frames are there to replay the attacks on a real bus, which is what the board does.

It writes one directory of the runs repository, `scores/<time>/`.

## Running it

```
python3 -m evaluate.pc.score repo revision attack_sets/<time> local_dir runs_repo revision thresholds/<time> runs_dir [--rebuild]
```

| argument | |
|---|---|
| `repo` | Hugging Face dataset repo holding `attack_sets/<time>/` |
| `revision` | commit of `repo` to read it at, as [attack_set](../../assemble/docs/attack_set.md) printed it |
| `attack_sets/<time>` | the attack set whose rows the detectors read. The split and grid it names are read too |
| `local_dir` | local folder the dataset directories are downloaded to |
| `runs_repo` | Hugging Face model repo holding the thresholds and uploaded to, needs `hf auth login` |
| `revision` | commit of `runs_repo` to read the thresholds at, as [calibrate](calibrate.md) printed it |
| `thresholds/<time>` | the thresholds the models run at. The models themselves are read too |
| `runs_dir` | local folder `scores/<time>/` is written to, kept after the upload |
| `--rebuild` | run again even if `runs_repo` already holds a directory with the same `inputs` |

It writes these files into `runs_dir/scores/<time>/` and uploads that directory to
`runs_repo` as `scores/<time>/`.

| file | holds |
|---|---|
| `detection.json` | one entry per detector, the rules first, then each model as the thresholds record it |
| `attacks.json` | one entry per attack, its log, the rows it reaches, and its `moved` |
| `meta.json` | where the rows, the models and the thresholds came from |

| field in `meta.json` | holds |
|---|---|
| `inputs` | `attack_sets/<time>`, `thresholds/<time>`, `MOVED` and `HOLD`. A later call with the same `inputs` reuses this directory |
| `thresholds`, `models` | the directories the thresholds and the weights came from, each a repo, a revision and a path |
| `attack_set`, `split`, `grid` | the dataset directories the rows came from |
| `min_speed` | the speed a row had to exceed to be counted |
| `rows` | how many attacked rows were read |
| `attacks` | how many attacks were injected into the test logs |
| `attacks_scorable` | how many of them reach a row above `min_speed` and moved it by at least `MOVED` |
| `hours` | hours of rows above `min_speed` with no attack in them, what the false alarms are counted over |
| `versions` | Python, NumPy, torch and the platform |
| `commit`, `uncommitted` | the commit of this repository it ran from, and any uncommitted files |
| `started`, `finished` | when it started and ended |

## When an alarm counts as catching an attack

A detector flags a row when a rule fires on it, or when the model's score on it is
over the threshold.

An alarm is raised once `HOLD` rows in a row are flagged, inside one segment. At
`HOLD` 10 that is a second of them, and the alarm is raised on the tenth row.

An attack is caught when one of its rows raises an alarm.

## How much an attack changed the data

`moved` is how far an attack took a row from the row the bus really produced. An
attack changes several rows, and `moved` is the largest of them:

    || (attacked row - original row) / std ||

The original rows come from the [grid](../../assemble/docs/grid.md), and `std` from
the train set. A replay can copy values close to the ones it overwrote, and then
`moved` is near zero.

`attacks.json` keeps `moved` for every attack.

## What each entry of `detection.json` holds

| key | holds |
|---|---|
| `detector` | `rules`, on the first entry only. Every other entry is a model, written as the thresholds record it |
| `threshold` | the score above which the model flags a row |
| `false_positive_rate` | the share of rows with no attack and no rule on them that the model flags. Read it against `TARGET` |
| `"1"`, `"10"` | what it caught at each `HOLD`, below |

Under each `HOLD`:

| key | holds |
|---|---|
| `found` | attacks caught, of all the attacks injected |
| `found_scorable` | the same over the attacks that reach a row above `MIN_SPEED` and moved it by at least `MOVED` |
| `alarms_per_hour` | false alarms an hour |
| `caught` | which attacks were caught, numbered as `attacks.json` lists them |

`caught` lists which attacks they were, so `found` can be worked out again over any
part of them, such as the attacks above some `moved`, or the attacks of one kind once
there is more than one kind. `attacks.json` holds what to select on.
