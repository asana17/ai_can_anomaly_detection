# run test set

`run_test_set` counts the attacks each detector catches on the attacked test rows.
A detector is the instant rules, or the rules together with one model. The rate rules
are left out, since neither model reads a window either. The models and their
thresholds come from a directory [calibrate](../../models/docs/calibrate.md) wrote,
so nothing is fitted or thresholded here. It scores the test set with those models by
running [score](../../scoring/docs/score.md), or reuses the scores the runs repository
holds for them already.

A [test set](../../assemble/docs/test_set.md) holds two things: the attacked test
logs as rows on the grid, and the same logs as CAN frames. The rows are scored. The
frames are there to replay the attacks on a real bus, which is what the board does.

It writes one directory of the runs repository, `test_runs/<time>/`.

## Running it

```
python3 -m evaluate.run_test_set repo revision test_sets/<time> local_dir runs_repo revision thresholds/<time> runs_dir [--rebuild]
```

| argument | |
|---|---|
| `repo` | Hugging Face dataset repo holding `test_sets/<time>/` |
| `revision` | commit of `repo` to read it at, as [test_set](../../assemble/docs/test_set.md) printed it |
| `test_sets/<time>` | the test set the detectors are run over. The log split and grid it names are read too |
| `local_dir` | local folder the dataset directories are downloaded to |
| `runs_repo` | Hugging Face model repo holding the thresholds and uploaded to, needs `hf auth login` |
| `revision` | commit of `runs_repo` to read the thresholds at, as [calibrate](../../models/docs/calibrate.md) printed it |
| `thresholds/<time>` | the thresholds the models run at. The models they name are read too, and scored with |
| `runs_dir` | local folder `scores/<time>/` and `test_runs/<time>/` are written to, kept after the upload |
| `--rebuild` | count again even if `runs_repo` already holds a directory with the same `inputs`. The scores are still reused |

It writes these files into `runs_dir/test_runs/<time>/` and uploads that directory to
`runs_repo` as `test_runs/<time>/`.

| file | holds |
|---|---|
| `detection.json` | one entry per detector, the rules first, then each model as the thresholds record it, as [detection.schema.json](../../common/schemas/detection.schema.json) describes |
| `attacks.json` | one entry per attack, its log, the rows it reaches, and its `moved`, as [attacks.schema.json](../../common/schemas/attacks.schema.json) describes |
| `meta.json` | where the scores, the thresholds and the rows came from, as [meta.test_runs.schema.json](../../common/schemas/meta.test_runs.schema.json) describes |

## What int8 costs

Run `pc.run_test_set` twice on the same test set, once with thresholds calibrate took
in torch and once with those it took with the int8 files of the same fit. The rows, the rules
and the counting are the same for both. The arithmetic that scores a row is the only
difference, so the gap between the two is what the quantization costs.

## When an alarm counts as catching an attack

A detector flags a row when a rule fires on it, or when the model's score on it is
over the threshold.

An alarm is raised once `HOLD` rows in a row are flagged, inside one segment. At
`HOLD` 10 that is a second of them, and the alarm is raised on the tenth row.

`alarmed_rows` in [alarm](../../detect/docs/alarm.md) raises the alarms. An attack is
caught when one of its rows raises an alarm.

## How much an attack changed the data

`moved` is how far an attack took a row from the row the bus really produced. An
attack changes several rows, and `moved` is the largest of them:

    || (attacked row - original row) / std ||

The original rows come from the [grid](../../assemble/docs/grid.md), and `std` from
the train set. A replay can copy values close to the ones it overwrote, and then
`moved` is near zero.

`attacks.json` keeps `moved` for every attack.

## Which attacks a detector could catch

Some attacks no detector could be asked to find, so each run reports two numbers, one
over every attack injected and one over the attacks worth catching. An attack is worth
catching when it reaches a row above `MIN_SPEED` and its `moved` is at least `MOVED`.

`MOVED` 1.0 drops the replays whose copied values nearly match the ones they
overwrote. A detector reads the rows, and those rows barely changed.

Whether an attack reaches a row above `MIN_SPEED` is read off the row's speed before
the attack. An attack that fakes a stop is still worth catching. The detectors read the
attacked speed, so one that skips the row misses the attack.

False alarms are the alarms raised on rows with no attack, over the hours those rows
cover.

[settings](../../common/docs/settings.md) says how `MIN_SPEED` and the rest were set.

## What each entry of `detection.json` holds

[detection.schema.json](../../common/schemas/detection.schema.json) describes each entry.

`caught` lists which attacks they were, so `found` can be worked out again over any
part of them, such as the attacks above some `moved`, or the attacks of one kind once
there is more than one kind. `attacks.json` holds what to select on.
