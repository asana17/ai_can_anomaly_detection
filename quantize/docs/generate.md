# generate

The board runs C code that ST Edge AI Core generates from an ONNX file. `generate`
generates that code from every float file of one [export](export.md), and keeps it in
the runs repository, where it records the code the board ran.

## Running it

```
python3 -u -m quantize.generate stedgeai runs_clone exported
```

| argument | what it is |
|---|---|
| `stedgeai` | the ST Edge AI Core command line tool |
| `runs_clone` | a clone of the [runs repository](../../evaluate/docs/run_record.md), the one the export went into |
| `exported` | the export's `<export time>` under `quantize/`, such as `20260916-221145` |

Which models are generated is not an argument. Every model the export's `meta.json`
lists is generated. The int8 files are not, since the board runs float.

## What it writes

Each call adds `board/<generate time>/` to `runs_clone`, then commits and pushes that
directory. It never writes into an existing directory.

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
| `export` | the export the ONNX files came from, as `quantize/<export time>` |
| `run` | the run the export's weights came from |
| `target` | the `--target` passed to the generator |
| `models` | the `k` and `h` of every model in the directory |
| `commit` | the commit of this repository `generate` ran from |
| `uncommitted` | `git status --porcelain` at the start, empty when nothing was changed |
| `versions` | Python and ST Edge AI Core |
| `generated` | when `generate` started |

The threshold to compile in is not here. It is the run's own, in the run's `meta.json`.
