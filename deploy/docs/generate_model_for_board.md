# generate_model_for_board

The board runs C code that ST Edge AI Core generates from an ONNX file.
`generate_model_for_board` generates that code from every float file of one
[export](export.md), and keeps it in the runs repository, where it records the code the
board ran.

## Running it

```
python3 -u -m deploy.generate_model_for_board stedgeai runs_repo runs_dir onnx/<time>
```

| argument | what it is |
|---|---|
| `stedgeai` | the ST Edge AI Core command line tool |
| `runs_repo`, `runs_dir` | the [runs repository](../../evaluate/docs/run_record.md) the export went into, and its local copy |
| `onnx/<time>` | the export to generate from |

The export's directory is downloaded into `runs_dir`. Which models are generated is not
an argument. Every model the export's `meta.json` lists is generated.

## What it writes

Each call writes `board/<generate time>/` into `runs_dir` and uploads it to `runs_repo`
in one commit, the way a [run](../../evaluate/docs/run_record.md) does.

Every model gets its own `nonlinear_ae_k{k}_h{h}/` inside. The generator names every
file `network`, so the board application includes the same names for any model. The
directory and `meta.json` say which model it is.

| file | holds |
|---|---|
| `network.c`, `network.h` | the model's runtime entry points |
| `network_data.c`, `network_data.h` | the weights |
| `network_details.h` | the layers |
| `network_c_info.json`, `network_generate_report.txt` | the flash and RAM the model takes, as the generator reports it |
| `LICENSE.txt` | SLA0104, the licence the generator writes for the code |

| key in `meta.json` | holds |
|---|---|
| `export` | the export the ONNX files came from, as `onnx/<time>` |
| `models` | the models directory the export's weights came from |
| `target` | the `--target` passed to the generator |
| `exported` | every model in the directory, as the export lists it |
| `commit` | the commit of this repository `generate_model_for_board` ran from |
| `uncommitted` | `git status --porcelain` at the start, empty when nothing was changed |
| `versions` | Python and ST Edge AI Core |
| `generated` | when `generate_model_for_board` started |

The threshold to compile in is not here. It is in the `thresholds.json` of [calibrate](../../evaluate/docs/calibrate.md).
