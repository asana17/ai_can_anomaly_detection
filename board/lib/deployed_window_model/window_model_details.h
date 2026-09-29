/**
  ******************************************************************************
  * @file    window_model.h
  * @date    2026-09-29T11:31:17+0900
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
  .tensors = (const stai_tensor[28]) {
   { .size_bytes = 850, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {2, (const int32_t[2]){1, 850}}, .scale = {1, (const float[1]){0.10375061631202698}}, .zeropoint = {1, (const int16_t[1]){-9}}, .name = "row_output" },
   { .size_bytes = 850, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 17, 50}}, .scale = {1, (const float[1]){0.10375061631202698}}, .zeropoint = {1, (const int16_t[1]){-9}}, .name = "_Reshape_output_0_to_chfirst_output" },
   { .size_bytes = 833, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 17, 49}}, .scale = {1, (const float[1]){0.10375061631202698}}, .zeropoint = {1, (const int16_t[1]){-9}}, .name = "_Slice_output_0_output" },
   { .size_bytes = 3332, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_FLOAT32, .shape = {3, (const int32_t[3]){1, 17, 49}}, .scale = {0, NULL}, .zeropoint = {0, NULL}, .name = "_Slice_output_0_0_conversion_output" },
   { .size_bytes = 833, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 17, 49}}, .scale = {1, (const float[1]){0.10375061631202698}}, .zeropoint = {1, (const int16_t[1]){-9}}, .name = "_Slice_1_output_0_output" },
   { .size_bytes = 3332, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_FLOAT32, .shape = {3, (const int32_t[3]){1, 17, 49}}, .scale = {0, NULL}, .zeropoint = {0, NULL}, .name = "_Slice_1_output_0_0_1__Sub_output_0_conversion_output" },
   { .size_bytes = 3332, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_FLOAT32, .shape = {3, (const int32_t[3]){1, 17, 49}}, .scale = {0, NULL}, .zeropoint = {0, NULL}, .name = "_Sub_output_0_output" },
   { .size_bytes = 3332, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_FLOAT32, .shape = {3, (const int32_t[3]){1, 17, 49}}, .scale = {0, NULL}, .zeropoint = {0, NULL}, .name = "_Div_output_0_output" },
   { .size_bytes = 833, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 17, 49}}, .scale = {1, (const float[1]){0.471759170293808}}, .zeropoint = {1, (const int16_t[1]){24}}, .name = "_Div_output_0_0_0__Transpose_output_0_conversion_output" },
   { .size_bytes = 833, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 49, 17}}, .scale = {1, (const float[1]){0.471759170293808}}, .zeropoint = {1, (const int16_t[1]){24}}, .name = "_Transpose_output_0_output" },
   { .size_bytes = 901, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 53, 17}}, .scale = {1, (const float[1]){0.471759170293808}}, .zeropoint = {1, (const int16_t[1]){24}}, .name = "_encoder_encoder_1_Relu_output_0_pad_before_output" },
   { .size_bytes = 1600, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 25, 64}}, .scale = {1, (const float[1]){0.5419297814369202}}, .zeropoint = {1, (const int16_t[1]){-128}}, .name = "_encoder_encoder_1_Relu_output_0_output" },
   { .size_bytes = 1856, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 29, 64}}, .scale = {1, (const float[1]){0.5419297814369202}}, .zeropoint = {1, (const int16_t[1]){-128}}, .name = "_decoder_decoder_0_Relu_output_0_pad_before_output" },
   { .size_bytes = 208, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 13, 16}}, .scale = {1, (const float[1]){0.7686384916305542}}, .zeropoint = {1, (const int16_t[1]){-128}}, .name = "_decoder_decoder_0_Relu_output_0_output" },
   { .size_bytes = 400, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 25, 16}}, .scale = {1, (const float[1]){0.7686384916305542}}, .zeropoint = {1, (const int16_t[1]){-128}}, .name = "_decoder_decoder_2_Relu_output_0_upsample_output" },
   { .size_bytes = 480, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 30, 16}}, .scale = {1, (const float[1]){0.7686384916305542}}, .zeropoint = {1, (const int16_t[1]){-128}}, .name = "_decoder_decoder_2_Relu_output_0_pad_before_output" },
   { .size_bytes = 1664, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 26, 64}}, .scale = {1, (const float[1]){1.0637110471725464}}, .zeropoint = {1, (const int16_t[1]){-128}}, .name = "_decoder_decoder_2_Relu_output_0_output" },
   { .size_bytes = 3264, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 51, 64}}, .scale = {1, (const float[1]){1.0637110471725464}}, .zeropoint = {1, (const int16_t[1]){-128}}, .name = "_decoder_decoder_3_ConvTranspose_output_0_upsample_output" },
   { .size_bytes = 3584, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 56, 64}}, .scale = {1, (const float[1]){1.0637110471725464}}, .zeropoint = {1, (const int16_t[1]){-128}}, .name = "_decoder_decoder_3_ConvTranspose_output_0_pad_before_output" },
   { .size_bytes = 884, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 52, 17}}, .scale = {1, (const float[1]){0.4818134307861328}}, .zeropoint = {1, (const int16_t[1]){18}}, .name = "_decoder_decoder_3_ConvTranspose_output_0_output" },
   { .size_bytes = 833, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 49, 17}}, .scale = {1, (const float[1]){0.4818134307861328}}, .zeropoint = {1, (const int16_t[1]){18}}, .name = "_Slice_2_output_0_output" },
   { .size_bytes = 833, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 17, 49}}, .scale = {1, (const float[1]){0.4818134307861328}}, .zeropoint = {1, (const int16_t[1]){18}}, .name = "_Transpose_1_output_0_output" },
   { .size_bytes = 3332, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_FLOAT32, .shape = {3, (const int32_t[3]){1, 17, 49}}, .scale = {0, NULL}, .zeropoint = {0, NULL}, .name = "_Transpose_1_output_0_0_0__Sub_1_output_0_conversion_output" },
   { .size_bytes = 3332, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_FLOAT32, .shape = {3, (const int32_t[3]){1, 17, 49}}, .scale = {0, NULL}, .zeropoint = {0, NULL}, .name = "_Sub_1_output_0_output" },
   { .size_bytes = 833, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 17, 49}}, .scale = {1, (const float[1]){0.3594858944416046}}, .zeropoint = {1, (const int16_t[1]){-2}}, .name = "_Sub_1_output_0_0_0__Flatten_output_0_conversion_output" },
   { .size_bytes = 833, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {3, (const int32_t[3]){1, 49, 17}}, .scale = {1, (const float[1]){0.3594858944416046}}, .zeropoint = {1, (const int16_t[1]){-2}}, .name = "_Flatten_output_0_to_chlast_output" },
   { .size_bytes = 850, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {2, (const int32_t[2]){1, 850}}, .scale = {1, (const float[1]){0.3594858944416046}}, .zeropoint = {1, (const int16_t[1]){-2}}, .name = "_Concat_output_0_output" },
   { .size_bytes = 850, .flags = (STAI_FLAG_HAS_BATCH|STAI_FLAG_CHANNEL_LAST), .format = STAI_FORMAT_S8, .shape = {2, (const int32_t[2]){1, 850}}, .scale = {1, (const float[1]){0.34493157267570496}}, .zeropoint = {1, (const int16_t[1]){-9}}, .name = "out_QuantizeLinear_Input_output" }
  },
  .nodes = (const stai_node_details[27]){
    {.id = 12, .type = AI_LAYER_TRANSPOSE_TYPE, .input_tensors = {1, (const int32_t[1]){0}}, .output_tensors = {1, (const int32_t[1]){1}} }, /* _Reshape_output_0_to_chfirst */
    {.id = 15, .type = AI_LAYER_SLICE_TYPE, .input_tensors = {1, (const int32_t[1]){1}}, .output_tensors = {1, (const int32_t[1]){2}} }, /* _Slice_output_0 */
    {.id = 15, .type = AI_LAYER_NL_TYPE, .input_tensors = {1, (const int32_t[1]){2}}, .output_tensors = {1, (const int32_t[1]){3}} }, /* _Slice_output_0_0_conversion */
    {.id = 14, .type = AI_LAYER_SLICE_TYPE, .input_tensors = {1, (const int32_t[1]){1}}, .output_tensors = {1, (const int32_t[1]){4}} }, /* _Slice_1_output_0 */
    {.id = 14, .type = AI_LAYER_NL_TYPE, .input_tensors = {1, (const int32_t[1]){4}}, .output_tensors = {1, (const int32_t[1]){5}} }, /* _Slice_1_output_0_0_1__Sub_output_0_conversion */
    {.id = 17, .type = AI_LAYER_ELTWISE_TYPE, .input_tensors = {2, (const int32_t[2]){3, 5}}, .output_tensors = {1, (const int32_t[1]){6}} }, /* _Sub_output_0 */
    {.id = 19, .type = AI_LAYER_ELTWISE_TYPE, .input_tensors = {1, (const int32_t[1]){6}}, .output_tensors = {1, (const int32_t[1]){7}} }, /* _Div_output_0 */
    {.id = 19, .type = AI_LAYER_NL_TYPE, .input_tensors = {1, (const int32_t[1]){7}}, .output_tensors = {1, (const int32_t[1]){8}} }, /* _Div_output_0_0_0__Transpose_output_0_conversion */
    {.id = 21, .type = AI_LAYER_TRANSPOSE_TYPE, .input_tensors = {1, (const int32_t[1]){8}}, .output_tensors = {1, (const int32_t[1]){9}} }, /* _Transpose_output_0 */
    {.id = 24, .type = AI_LAYER_PAD_TYPE, .input_tensors = {1, (const int32_t[1]){9}}, .output_tensors = {1, (const int32_t[1]){10}} }, /* _encoder_encoder_1_Relu_output_0_pad_before */
    {.id = 24, .type = AI_LAYER_CONV2D_TYPE, .input_tensors = {1, (const int32_t[1]){10}}, .output_tensors = {1, (const int32_t[1]){11}} }, /* _encoder_encoder_1_Relu_output_0 */
    {.id = 27, .type = AI_LAYER_PAD_TYPE, .input_tensors = {1, (const int32_t[1]){11}}, .output_tensors = {1, (const int32_t[1]){12}} }, /* _decoder_decoder_0_Relu_output_0_pad_before */
    {.id = 27, .type = AI_LAYER_CONV2D_TYPE, .input_tensors = {1, (const int32_t[1]){12}}, .output_tensors = {1, (const int32_t[1]){13}} }, /* _decoder_decoder_0_Relu_output_0 */
    {.id = 30, .type = AI_LAYER_UPSAMPLE_TYPE, .input_tensors = {1, (const int32_t[1]){13}}, .output_tensors = {1, (const int32_t[1]){14}} }, /* _decoder_decoder_2_Relu_output_0_upsample */
    {.id = 30, .type = AI_LAYER_PAD_TYPE, .input_tensors = {1, (const int32_t[1]){14}}, .output_tensors = {1, (const int32_t[1]){15}} }, /* _decoder_decoder_2_Relu_output_0_pad_before */
    {.id = 30, .type = AI_LAYER_CONV2D_TYPE, .input_tensors = {1, (const int32_t[1]){15}}, .output_tensors = {1, (const int32_t[1]){16}} }, /* _decoder_decoder_2_Relu_output_0 */
    {.id = 33, .type = AI_LAYER_UPSAMPLE_TYPE, .input_tensors = {1, (const int32_t[1]){16}}, .output_tensors = {1, (const int32_t[1]){17}} }, /* _decoder_decoder_3_ConvTranspose_output_0_upsample */
    {.id = 33, .type = AI_LAYER_PAD_TYPE, .input_tensors = {1, (const int32_t[1]){17}}, .output_tensors = {1, (const int32_t[1]){18}} }, /* _decoder_decoder_3_ConvTranspose_output_0_pad_before */
    {.id = 33, .type = AI_LAYER_CONV2D_TYPE, .input_tensors = {1, (const int32_t[1]){18}}, .output_tensors = {1, (const int32_t[1]){19}} }, /* _decoder_decoder_3_ConvTranspose_output_0 */
    {.id = 36, .type = AI_LAYER_SLICE_TYPE, .input_tensors = {1, (const int32_t[1]){19}}, .output_tensors = {1, (const int32_t[1]){20}} }, /* _Slice_2_output_0 */
    {.id = 37, .type = AI_LAYER_TRANSPOSE_TYPE, .input_tensors = {1, (const int32_t[1]){20}}, .output_tensors = {1, (const int32_t[1]){21}} }, /* _Transpose_1_output_0 */
    {.id = 37, .type = AI_LAYER_NL_TYPE, .input_tensors = {1, (const int32_t[1]){21}}, .output_tensors = {1, (const int32_t[1]){22}} }, /* _Transpose_1_output_0_0_0__Sub_1_output_0_conversion */
    {.id = 38, .type = AI_LAYER_ELTWISE_TYPE, .input_tensors = {2, (const int32_t[2]){22, 7}}, .output_tensors = {1, (const int32_t[1]){23}} }, /* _Sub_1_output_0 */
    {.id = 38, .type = AI_LAYER_NL_TYPE, .input_tensors = {1, (const int32_t[1]){23}}, .output_tensors = {1, (const int32_t[1]){24}} }, /* _Sub_1_output_0_0_0__Flatten_output_0_conversion */
    {.id = 39, .type = AI_LAYER_TRANSPOSE_TYPE, .input_tensors = {1, (const int32_t[1]){24}}, .output_tensors = {1, (const int32_t[1]){25}} }, /* _Flatten_output_0_to_chlast */
    {.id = 42, .type = AI_LAYER_CONCAT_TYPE, .input_tensors = {1, (const int32_t[1]){25}}, .output_tensors = {1, (const int32_t[1]){26}} }, /* _Concat_output_0 */
    {.id = 45, .type = AI_LAYER_ELTWISE_INTEGER_TYPE, .input_tensors = {2, (const int32_t[2]){0, 26}}, .output_tensors = {1, (const int32_t[1]){27}} } /* out_QuantizeLinear_Input */
  },
  .n_nodes = 27
};
#endif

