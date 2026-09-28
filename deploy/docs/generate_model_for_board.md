# generate_model_for_board

The board runs C code that ST Edge AI Core generates from an ONNX file.
`generate_model_for_board` generates that code from every float file of one
[export](export.md) or [export_windows](export_windows.md), or from every int8 file
[quantize](quantize.md) made of one, and keeps it in the runs repository, where it records the code the
board ran.

## Running it

```
python3 -u -m deploy.generate_model_for_board stedgeai runs_repo revision onnx/<time> runs_dir [--rebuild]
```

| argument | what it is |
|---|---|
| `stedgeai` | the ST Edge AI Core command line tool |
| `runs_repo` | Hugging Face model repo holding the export and uploaded to, needs `hf auth login` |
| `revision` | commit of `runs_repo` to read the export at, as the export printed it |
| `onnx/<time>` | the export to generate from, `window_onnx/<time>` for the window models, or `quantize/<time>` or `window_quantize/<time>` for their int8 files |
| `runs_dir` | local folder the export is downloaded to and the code is written to |
| `--rebuild` | generate again even if `runs_repo` already holds a directory with the same `inputs` |

The export's directory is downloaded into `runs_dir`. Which models are generated is not
an argument. Every model the export's `meta.json` lists is generated. For int8 files
that is the export their `meta.json` names.

## What it writes

From an `onnx/<time>` export or its `quantize/<time>` it writes `runs_dir/board/<time>/`
and uploads that directory to `runs_repo` as `board/<time>/`. From a
`window_onnx/<time>` export or its `window_quantize/<time>` it does the same under
`window_board/<time>/`.

Every model gets its own directory inside, named like its ONNX file without
`_float.onnx` or `_int8.onnx`. The generator names the files and the C functions after the model's
kind, `instant_model` for a row model and `window_model` for a window model. The board
application includes the same names for any model of a kind, and a row model and a
window model do not share names. The directory and `meta.json` say which model it is.

| file | holds |
|---|---|
| `{name}.c`, `{name}.h` | the model's runtime entry points |
| `{name}_data.c`, `{name}_data.h` | the weights |
| `{name}_details.h` | the layers |
| `{name}_c_info.json`, `{name}_generate_report.txt` | the flash and RAM the model takes, as the generator reports it |
| `LICENSE.txt` | SLA0104, the licence the generator writes for the code |
| `meta.json` | where the export came from, as [meta.board.schema.json](../../common/schemas/meta.board.schema.json) or [meta.window_board.schema.json](../../common/schemas/meta.window_board.schema.json) describes |

The threshold to compile in is not here. It is in the `thresholds.json` of [calibrate](../../models/docs/calibrate.md), or of
[calibrate_windows](../../models/docs/calibrate_windows.md) for a window model.
