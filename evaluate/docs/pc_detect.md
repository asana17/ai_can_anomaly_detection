# pc detect

`pc.detect` counts the attacks each detector catches on the attacked test rows. A detector
is the instant rules, or the rules together with one model. The models and their thresholds
come from a directory [calibrate](calibrate.md) wrote, so nothing is fitted or
thresholded here. When calibrate took the thresholds with ONNX files, each model is
its ONNX file of the same precision.

A [test set](../../assemble/docs/test_set.md) holds two things: the attacked test
logs as rows on the grid, and the same logs as CAN frames. `pc.detect` reads the rows. The
frames are there to replay the attacks on a real bus, which is what the board does.

It writes one directory of the runs repository, `detections/<time>/`.

## Running it

```
python3 -m evaluate.pc.detect repo revision test_sets/<time> local_dir runs_repo revision thresholds/<time> runs_dir [--rebuild]
```

| argument | |
|---|---|
| `repo` | Hugging Face dataset repo holding `test_sets/<time>/` |
| `revision` | commit of `repo` to read it at, as [test_set](../../assemble/docs/test_set.md) printed it |
| `test_sets/<time>` | the test set whose rows the detectors read. The log split and grid it names are read too |
| `local_dir` | local folder the dataset directories are downloaded to |
| `runs_repo` | Hugging Face model repo holding the thresholds and uploaded to, needs `hf auth login` |
| `revision` | commit of `runs_repo` to read the thresholds at, as [calibrate](calibrate.md) printed it |
| `thresholds/<time>` | the thresholds the models run at. The models themselves are read too |
| `runs_dir` | local folder `detections/<time>/` is written to, kept after the upload |
| `--rebuild` | run again even if `runs_repo` already holds a directory with the same `inputs` |

It writes these files into `runs_dir/detections/<time>/` and uploads that directory to
`runs_repo` as `detections/<time>/`.

| file | holds |
|---|---|
| `detection.json` | one entry per detector, the rules first, then each model as the thresholds record it, as [detection.schema.json](../../common/schemas/detection.schema.json) describes |
| `attacks.json` | one entry per attack, its log, the rows it reaches, and its `moved`, as [attacks.schema.json](../../common/schemas/attacks.schema.json) describes |
| `meta.json` | where the rows, the models and the thresholds came from, as [meta.detections.schema.json](../../common/schemas/meta.detections.schema.json) describes |

## What int8 costs

Score the same test set twice, once with thresholds calibrate took in torch and once
with thresholds it took with the int8 files of the same fit. The rows, the rules and
the counting are the same for both. The arithmetic that scores a
row is the only difference, so the gap between the two is what the quantization costs.

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

## What each entry of `detection.json` holds

[detection.schema.json](../../common/schemas/detection.schema.json) describes each entry.

`caught` lists which attacks they were, so `found` can be worked out again over any
part of them, such as the attacks above some `moved`, or the attacks of one kind once
there is more than one kind. `attacks.json` holds what to select on.
