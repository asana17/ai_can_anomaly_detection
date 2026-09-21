# generate_model_for_board

The board runs C code that ST Edge AI Core generates from an ONNX file.
`generate_model_for_board` generates that code from every float file of one
[export](export.md), and keeps it in the runs repository, where it records the code the
board ran.

## Running it

```
python3 -u -m deploy.generate_model_for_board stedgeai runs_repo revision onnx/<time> runs_dir [--rebuild]
```

| argument | what it is |
|---|---|
| `stedgeai` | the ST Edge AI Core command line tool |
| `runs_repo` | Hugging Face model repo holding the export and uploaded to, needs `hf auth login` |
| `revision` | commit of `runs_repo` to read the export at, as [export](export.md) printed it |
| `onnx/<time>` | the export to generate from |
| `runs_dir` | local folder the export is downloaded to and `board/<time>/` is written to |
| `--rebuild` | generate again even if `runs_repo` already holds a directory with the same `inputs` |

The export's directory is downloaded into `runs_dir`. Which models are generated is not
an argument. Every model the export's `meta.json` lists is generated.

## What it writes

It writes `runs_dir/board/<time>/` and uploads that directory to `runs_repo` as
`board/<time>/`.

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
| `inputs` | the export and the `--target` passed to the generator. A later call with the same `inputs` reuses this directory |
| `onnx` | the export the float files came from, as a repo, a revision and a path |
| `models` | the models directory the export's weights came from |
| `exported` | every model in the directory, as the export lists it |
| `versions` | Python and ST Edge AI Core |
| `commit`, `uncommitted` | the commit of this repository it ran from, and any uncommitted files |
| `started`, `finished` | when it started and ended |

The threshold to compile in is not here. It is in the `thresholds.json` of [calibrate](../../evaluate/docs/calibrate.md).
