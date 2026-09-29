# Third-party software and data

This repo's own code is under the [MIT License](LICENSE). The software and data below
belong to others and keep their own licenses.

## Bundled in this repo

| what | used for | license |
|---|---|---|
| C code and ONNX files that ST Edge AI Core generated, in [board/lib/active_model](board/lib/active_model), [board/lib/deployed_model](board/lib/deployed_model) and [board/lib/deployed_window_model](board/lib/deployed_window_model) | the models the board runs | STMicroelectronics SLA0104, in the `LICENSE.txt` next to them |
| [mtk3bsp2_samples](https://github.com/mox692/mtk3bsp2_samples), a git submodule on branch `can_driver`, forked from [tron-forum/mtk3bsp2_samples](https://github.com/tron-forum/mtk3bsp2_samples) | the CAN task in `board/application/can_bus_debug` is modelled on its `task_can` | as its README states, μT-Kernel 3.0 under T-License 2.2 and IDE generated code under the terms in its archive |

## Fetched or generated when a board project is prepared

[board/prepare](board/prepare) clones the BSP and Unity into the STM32CubeIDE project
and links the ST Edge AI runtime from where ST Edge AI Core is installed. It links the
mbed-crypto sources from the STM32Cube FW_H5 repository. CubeMX
generates the drivers and CMSIS there.

| what | version | used for | license |
|---|---|---|---|
| [μT-Kernel 3.0 BSP2](https://github.com/tron-forum/mtk3_bsp2) with μT-Kernel 3.0 | `1ab52cc`, μT-Kernel v3.00.07, with [board/patches](board/patches) applied | the kernel every board application runs on | T-License 2.2 |
| [Unity](https://github.com/ThrowTheSwitch/Unity) | `b6763fb` | the board unit tests | MIT |
| STM32H5xx HAL and BSP STM32H5xx_Nucleo | STM32Cube FW_H5 V1.6.0 | drivers | BSD-3-Clause |
| CMSIS and CMSIS Device | STM32Cube FW_H5 V1.6.0 | Cortex-M33 core and device headers | Apache-2.0 |
| mbed-crypto, `md.c`, `platform.c`, `platform_util.c` and `sha256.c` and its headers | Mbed TLS 3.6.4 in STM32Cube FW_H5 V1.6.0 | the HMAC-SHA256 on the alarm frames | Apache-2.0 |
| ST Edge AI Core runtime, `NetworkRuntime1201_CM33_GCC.a` and its headers | 4.0.1 | runs the model on the board | STMicroelectronics SLA0104 |

## Python packages

Installed from [requirements.txt](requirements.txt).

| package | license |
|---|---|
| numpy | BSD-3-Clause |
| torch | BSD-3-Clause |
| safetensors | Apache-2.0 |
| huggingface_hub | Apache-2.0 |
| onnx | Apache-2.0 |
| onnxruntime | MIT |
| pyarrow | Apache-2.0 |
| scikit-learn | BSD-3-Clause |
| jsonschema | MIT |
| pytest | MIT |
| gs_usb | MIT |
| pyusb | BSD-3-Clause |

`send_test_frames.py` in
[board/application/ai_can_anomaly_detection](board/application/ai_can_anomaly_detection)
loads [libusb](https://libusb.info) 1.0, LGPL-2.1-or-later, installed on its own, at run
time through pyusb.

## Data

The CAN logs are the [University of Turku J1939 truck dataset](https://etsin.fairdata.fi/dataset/7586f24f-c91b-41df-92af-283524de8b3e/data),
under CC BY 4.0. They are not in this repo.
