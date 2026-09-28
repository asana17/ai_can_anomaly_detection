/**
  ******************************************************************************
  * @file    window_model.h
  * @date    2026-09-29T07:05:18+0900
  * @brief   ST.AI Tool Automatic Code Generator for Embedded NN computing
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  ******************************************************************************
  */
#ifndef STAI_WINDOW_MODEL_DETAILS_H
#define STAI_WINDOW_MODEL_DETAILS_H

#include "stai.h"
#include "layers.h"

const stai_network_details g_window_model_details = {
  .tensors = (const stai_tensor[15]) {
   { .size_bytes = 340, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {2, (const int32_t[2]){1, 340}}, .scale = {1, (const float[1]){0.10375061631202698}}, .zeropoint = {1, (const int16_t[1]){-9}}, .name = "row_output" },
   { .size_bytes = 323, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 19, 17}}, .scale = {1, (const float[1]){0.10375061631202698}}, .zeropoint = {1, (const int16_t[1]){-9}}, .name = "_Slice_output_0_output" },
   { .size_bytes = 1292, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_FLOAT32, .shape = {3, (const int32_t[3]){1, 19, 17}}, .scale = {0, NULL}, .zeropoint = {0, NULL}, .name = "_Slice_output_0_0_conversion_output" },
   { .size_bytes = 323, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 19, 17}}, .scale = {1, (const float[1]){0.10375061631202698}}, .zeropoint = {1, (const int16_t[1]){-9}}, .name = "_Slice_1_output_0_output" },
   { .size_bytes = 1292, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_FLOAT32, .shape = {3, (const int32_t[3]){1, 19, 17}}, .scale = {0, NULL}, .zeropoint = {0, NULL}, .name = "_Slice_1_output_0_0_1__Sub_output_0_conversion_output" },
   { .size_bytes = 1292, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_FLOAT32, .shape = {3, (const int32_t[3]){1, 19, 17}}, .scale = {0, NULL}, .zeropoint = {0, NULL}, .name = "_Sub_output_0_output" },
   { .size_bytes = 1292, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_FLOAT32, .shape = {3, (const int32_t[3]){1, 19, 17}}, .scale = {0, NULL}, .zeropoint = {0, NULL}, .name = "_Div_output_0_output" },
   { .size_bytes = 323, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 19, 17}}, .scale = {1, (const float[1]){0.4396611154079437}}, .zeropoint = {1, (const int16_t[1]){19}}, .name = "_Div_output_0_0_0__Flatten_output_0_conversion_output" },
   { .size_bytes = 128, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {2, (const int32_t[2]){1, 128}}, .scale = {1, (const float[1]){0.7550769448280334}}, .zeropoint = {1, (const int16_t[1]){-128}}, .name = "_steps_encoder_encoder_1_Relu_output_0_output" },
   { .size_bytes = 24, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {2, (const int32_t[2]){1, 24}}, .scale = {1, (const float[1]){0.39102885127067566}}, .zeropoint = {1, (const int16_t[1]){8}}, .name = "_steps_encoder_encoder_2_Gemm_output_0_output" },
   { .size_bytes = 128, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {2, (const int32_t[2]){1, 128}}, .scale = {1, (const float[1]){0.2435407191514969}}, .zeropoint = {1, (const int16_t[1]){-128}}, .name = "_steps_decoder_decoder_1_Relu_output_0_output" },
   { .size_bytes = 323, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {2, (const int32_t[2]){1, 323}}, .scale = {1, (const float[1]){0.36954763531684875}}, .zeropoint = {1, (const int16_t[1]){46}}, .name = "_steps_decoder_decoder_2_Gemm_output_0_output" },
   { .size_bytes = 323, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {2, (const int32_t[2]){1, 323}}, .scale = {1, (const float[1]){0.3771512806415558}}, .zeropoint = {1, (const int16_t[1]){-11}}, .name = "_Sub_1_output_0_output" },
   { .size_bytes = 340, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {2, (const int32_t[2]){1, 340}}, .scale = {1, (const float[1]){0.3771512806415558}}, .zeropoint = {1, (const int16_t[1]){-11}}, .name = "_Concat_output_0_output" },
   { .size_bytes = 340, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {2, (const int32_t[2]){1, 340}}, .scale = {1, (const float[1]){0.34855908155441284}}, .zeropoint = {1, (const int16_t[1]){-13}}, .name = "out_QuantizeLinear_Input_output" }
  },
  .nodes = (const stai_node_details[14]){
    {.id = 15, .type = AI_LAYER_SLICE_TYPE, .input_tensors = {1, (const int32_t[1]){0}}, .output_tensors = {1, (const int32_t[1]){1}} }, /* _Slice_output_0 */
    {.id = 15, .type = AI_LAYER_NL_TYPE, .input_tensors = {1, (const int32_t[1]){1}}, .output_tensors = {1, (const int32_t[1]){2}} }, /* _Slice_output_0_0_conversion */
    {.id = 14, .type = AI_LAYER_SLICE_TYPE, .input_tensors = {1, (const int32_t[1]){0}}, .output_tensors = {1, (const int32_t[1]){3}} }, /* _Slice_1_output_0 */
    {.id = 14, .type = AI_LAYER_NL_TYPE, .input_tensors = {1, (const int32_t[1]){3}}, .output_tensors = {1, (const int32_t[1]){4}} }, /* _Slice_1_output_0_0_1__Sub_output_0_conversion */
    {.id = 17, .type = AI_LAYER_ELTWISE_TYPE, .input_tensors = {2, (const int32_t[2]){2, 4}}, .output_tensors = {1, (const int32_t[1]){5}} }, /* _Sub_output_0 */
    {.id = 19, .type = AI_LAYER_ELTWISE_TYPE, .input_tensors = {1, (const int32_t[1]){5}}, .output_tensors = {1, (const int32_t[1]){6}} }, /* _Div_output_0 */
    {.id = 19, .type = AI_LAYER_NL_TYPE, .input_tensors = {1, (const int32_t[1]){6}}, .output_tensors = {1, (const int32_t[1]){7}} }, /* _Div_output_0_0_0__Flatten_output_0_conversion */
    {.id = 24, .type = AI_LAYER_DENSE_TYPE, .input_tensors = {1, (const int32_t[1]){7}}, .output_tensors = {1, (const int32_t[1]){8}} }, /* _steps_encoder_encoder_1_Relu_output_0 */
    {.id = 27, .type = AI_LAYER_DENSE_TYPE, .input_tensors = {1, (const int32_t[1]){8}}, .output_tensors = {1, (const int32_t[1]){9}} }, /* _steps_encoder_encoder_2_Gemm_output_0 */
    {.id = 30, .type = AI_LAYER_DENSE_TYPE, .input_tensors = {1, (const int32_t[1]){9}}, .output_tensors = {1, (const int32_t[1]){10}} }, /* _steps_decoder_decoder_1_Relu_output_0 */
    {.id = 33, .type = AI_LAYER_DENSE_TYPE, .input_tensors = {1, (const int32_t[1]){10}}, .output_tensors = {1, (const int32_t[1]){11}} }, /* _steps_decoder_decoder_2_Gemm_output_0 */
    {.id = 36, .type = AI_LAYER_ELTWISE_INTEGER_TYPE, .input_tensors = {2, (const int32_t[2]){11, 7}}, .output_tensors = {1, (const int32_t[1]){12}} }, /* _Sub_1_output_0 */
    {.id = 39, .type = AI_LAYER_CONCAT_TYPE, .input_tensors = {1, (const int32_t[1]){12}}, .output_tensors = {1, (const int32_t[1]){13}} }, /* _Concat_output_0 */
    {.id = 42, .type = AI_LAYER_ELTWISE_INTEGER_TYPE, .input_tensors = {2, (const int32_t[2]){0, 13}}, .output_tensors = {1, (const int32_t[1]){14}} } /* out_QuantizeLinear_Input */
  },
  .n_nodes = 14
};
#endif

