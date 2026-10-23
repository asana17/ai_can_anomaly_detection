/**
  ******************************************************************************
  * @file    window_model.c
  * @author  AST Embedded Analytics Research Platform
  * @date    2026-09-29T11:31:17+0900
  * @brief   AI Tool Automatic Code Generator for Embedded NN computing
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

#include "ai_lite_inspect.h"
#include "ai_platform_interface.h"
#include "layers.h"
#include "core_convert.h"
#include "window_model.h"
#include "window_model_details.h"
#include "window_model_data.h"
#include "stai_events.h"

#include "lite_operators.h"

#include "ai_lite_inspect.h"
/*****************************************************************************/
#define STAI_INTERNAL_API_MAJOR               (1)
#define STAI_INTERNAL_API_MINOR               (0)
#define STAI_INTERNAL_API_MICRO               (0)

#define STAI_MAGIC                            (0xB1C00100)

/*****************************************************************************/
#define _STAI_CONCAT_ARG(a, b)     a ## b
#define STAI_CONCAT(a, b)         _STAI_CONCAT_ARG(a, b)

/*!  STAI_CAST SECTION                       *********************************/
#define STAI_CAST(type, expr) \
  ((type)(expr))


/*****************************************************************************/
#define STAI_SIZE(_size) \
  ((stai_size)(_size))

/*****************************************************************************/
#define STAI_INIT_BUFFER(_flags, _size, _address) \
  { \
    .size = (_size), \
    .address = (uintptr_t)(_address), \
    .flags = (_flags), \
  }

#define STAI_INIT_TENSOR(_name, _flags, _fmt, _size_bytes, _shape, _scale, _zeropoint) \
  { \
    .size_bytes = (_size_bytes), \
    .flags = (_flags), \
    .format = (stai_format)(_fmt), \
    .shape = STAI_PACK(_shape), \
    .scale = STAI_PACK(_scale), \
    .zeropoint = STAI_PACK(_zeropoint), \
    .name = (_name) \
  }

#define STAI_INIT_ARRAY(_size, _ptr) \
  { .size = STAI_SIZE(_size), .data = STAI_PACK(_ptr) }


#define STAI_CAST_ARRAY(_type, _size, _ptr) \
  { .size = STAI_SIZE(_size), .data = (_type)STAI_PACK(_ptr) }


#define STAI_DECLARE_ARRAY(_type, _size, ...) \
  { .size = STAI_SIZE(_size), .data = (_type[_size]) { STAI_PACK(__VA_ARGS__) } }


#define STAI_EMPTY_ARRAY() \
  { .size = 0, .data = NULL }


#define STAI_INIT_VERSION(_major, _minor, _micro) \
  { .major = (_major), .minor = (_minor), .micro = (_micro), .reserved = 0x0 }

/*****************************************************************************/
/**  Getters and setters  **/

#define STAI_GET_ARRAY_SIZE(nd_array) \
  (nd_array.size)


#define STAI_GET_ARRAY_ELEM(nd_array, pos) \
  (nd_array.data[(pos)])

#define _STAI_SET_ERROR(net_ctx, cond, value, exit) { \
  if (!(net_ctx)) { return STAI_ERROR_NETWORK_INVALID_CONTEXT_HANDLE; } \
  if (((uintptr_t)net_ctx) & (_STAI_CONTEXT_ALIGNMENT-1)) { return STAI_ERROR_NETWORK_INVALID_CONTEXT_ALIGNMENT; } \
  if (((value) >= STAI_ERROR_GENERIC) && (cond)) { \
    if ((net_ctx)->_return_code == STAI_SUCCESS) { \
      (net_ctx)->_return_code = (value); \
    } \
    return (exit); \
  } \
}

/*****************************************************************************/
/* TODO REMOVE THESE TWO MACROS */
#define STAI_EVENT_NODE_START_CB
#define STAI_EVENT_NODE_STOP_CB

#ifdef STAI_EVENT_NODE_START_CB
#ifndef _STAI_WINDOW_MODEL_EVENT_NODE_START_CB
  #define _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(_node_id, _buffers_size, ...) \
  if (net_ctx->_callback) { \
    const stai_event_node_start_stop _start_event = { \
      .node_id=(_node_id), \
      .buffers={ \
        .size=(_buffers_size), \
        .data=(stai_ptr const*)(const stai_ptr[_buffers_size])STAI_PACK(__VA_ARGS__) \
      } \
    }; \
    net_ctx->_callback(net_ctx->_callback_cookie, STAI_EVENT_NODE_START, (const void*)&_start_event); \
  }
#endif
#else
  #define _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(_node_id, _buffers_size, ...) \
    do { /* _STAI_WINDOW_MODEL_EVENT_NODE_START_CB() */ } while(0);
#endif      /* STAI_EVENT_NODE_START_CB */

#ifdef STAI_EVENT_NODE_STOP_CB
#ifndef _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB
  #define _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(_node_id, _buffers_size, ...) \
  if (net_ctx->_callback) { \
    const stai_event_node_start_stop _stop_event = { \
      .node_id=(_node_id), \
      .buffers={ \
        .size=(_buffers_size), \
        .data=(stai_ptr const*)(stai_ptr[_buffers_size])STAI_PACK(__VA_ARGS__) \
      } \
    }; \
    net_ctx->_callback(net_ctx->_callback_cookie, STAI_EVENT_NODE_STOP, (const void*)&_stop_event); \
  }
#endif
#else
  #define _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(_node_id, _buffers_size, ...) \
    do { /* _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB() */ } while(0);
#endif      /* STAI_EVENT_NODE_STOP_CB */


/*****************************************************************************/
#define _STAI_WINDOW_MODEL_MODEL_SIGNATURE     "0x4c05937e1f5400ad8f94a7c63dfe1241"
#define _STAI_WINDOW_MODEL_DATETIME            "2026-09-29T11:31:17+0900"
#define _STAI_WINDOW_MODEL_COMPILE_DATETIME    __DATE__ " " __TIME__

#define _STAI_CONTEXT_ALIGNMENT        STAI_WINDOW_MODEL_CONTEXT_ALIGNMENT

/*****************************************************************************/
#define g_window_model_activations_1     (NULL)




#if defined(HAVE_WINDOW_MODEL_INFO)
/*****************************************************************************/
static const stai_network_info g_window_model_info = {
  .model_signature = _STAI_WINDOW_MODEL_MODEL_SIGNATURE,
  .c_compile_datetime = _STAI_WINDOW_MODEL_COMPILE_DATETIME,
  .c_model_name = STAI_WINDOW_MODEL_MODEL_NAME,
  .c_model_datetime = _STAI_WINDOW_MODEL_DATETIME,
  .c_model_signature = 0x0,
  .runtime_version = STAI_INIT_VERSION(12, 0, 1),
  .tool_version = STAI_INIT_VERSION(4, 0, 1),
  .api_version = STAI_INIT_VERSION(1, 0, 0),
  .n_macc = STAI_WINDOW_MODEL_MACC_NUM,
  .n_nodes = STAI_WINDOW_MODEL_NODES_NUM,
  .flags = STAI_WINDOW_MODEL_FLAGS,
  .n_inputs = STAI_WINDOW_MODEL_IN_NUM,
  .n_outputs = STAI_WINDOW_MODEL_OUT_NUM,
  .n_activations = STAI_WINDOW_MODEL_ACTIVATIONS_NUM,
  .n_weights = STAI_WINDOW_MODEL_WEIGHTS_NUM,
  .n_states = STAI_WINDOW_MODEL_STATES_NUM,
  .inputs = (stai_tensor[STAI_WINDOW_MODEL_IN_NUM]) {
    STAI_INIT_TENSOR(
      STAI_WINDOW_MODEL_IN_1_NAME,
      STAI_WINDOW_MODEL_IN_1_FLAGS,
      STAI_WINDOW_MODEL_IN_1_FORMAT,
      STAI_WINDOW_MODEL_IN_1_SIZE_BYTES,
      STAI_DECLARE_ARRAY(int32_t, 2, 1, 850),
      STAI_DECLARE_ARRAY(float, 1, 0.10375061631202698f),
      STAI_DECLARE_ARRAY(int16_t, 1, -9)),
    },
    .outputs = (stai_tensor[STAI_WINDOW_MODEL_OUT_NUM]) {
    STAI_INIT_TENSOR(
      STAI_WINDOW_MODEL_OUT_1_NAME,
      STAI_WINDOW_MODEL_OUT_1_FLAGS,
      STAI_WINDOW_MODEL_OUT_1_FORMAT,
      STAI_WINDOW_MODEL_OUT_1_SIZE_BYTES,
      STAI_DECLARE_ARRAY(int32_t, 2, 1, 850),
      STAI_DECLARE_ARRAY(float, 1, 0.34493157267570496f),
      STAI_DECLARE_ARRAY(int16_t, 1, -9)),
    },
  .activations = (stai_tensor[STAI_WINDOW_MODEL_ACTIVATIONS_NUM]) {
    STAI_INIT_TENSOR(
      (NULL),
      STAI_WINDOW_MODEL_ACTIVATION_1_FLAGS,
      STAI_FORMAT_U8,
      STAI_WINDOW_MODEL_ACTIVATION_1_SIZE_BYTES,
      STAI_DECLARE_ARRAY(int32_t, 1, 16912),
      STAI_EMPTY_ARRAY(),
      STAI_EMPTY_ARRAY()),
    },
  .weights = (stai_tensor[STAI_WINDOW_MODEL_WEIGHTS_NUM]) {
    STAI_INIT_TENSOR(
      (NULL),
      STAI_WINDOW_MODEL_WEIGHT_1_FLAGS,
      STAI_FORMAT_U8,
      STAI_WINDOW_MODEL_WEIGHT_1_SIZE_BYTES,
      STAI_DECLARE_ARRAY(int32_t, 1, 21852),
      STAI_EMPTY_ARRAY(),
      STAI_EMPTY_ARRAY()),
    },

  .states = NULL
};
#endif

#define _STAI_CONTEXT_ACQUIRE(_net_ctx, _net_handle) \
  _stai_window_model_context* _net_ctx = (_stai_window_model_context*)(_net_handle); \
  STAI_ASSERT(_net_ctx != NULL) \
  _STAI_SET_ERROR(_net_ctx, _net_ctx->_magic != STAI_MAGIC, \
                  STAI_ERROR_NETWORK_INVALID_CONTEXT_HANDLE, _net_ctx->_return_code)


/*****************************************************************************/
static
void _stai_window_model_check(_stai_window_model_context* net_ctx)
{
  stai_size idx;

// Check activations status
  for (idx=0; idx<STAI_WINDOW_MODEL_ACTIVATIONS_NUM; idx++) {
    if (net_ctx->_activations[idx] == NULL) break;
  }
  net_ctx->_flags |= (idx == STAI_WINDOW_MODEL_ACTIVATIONS_NUM) ? STAI_FLAG_ACTIVATIONS : STAI_FLAG_NONE;
// Check inputs status
  for (idx=0; idx<STAI_WINDOW_MODEL_IN_NUM; idx++) {
    if (net_ctx->_inputs[idx] == NULL) break;
  }
  net_ctx->_flags |= (idx == STAI_WINDOW_MODEL_IN_NUM) ? STAI_FLAG_INPUTS : STAI_FLAG_NONE;

  // Check outputs status
  for (idx=0; idx<STAI_WINDOW_MODEL_OUT_NUM; idx++) {
    if (net_ctx->_outputs[idx] == NULL) break;
  }
  net_ctx->_flags |= (idx == STAI_WINDOW_MODEL_OUT_NUM) ? STAI_FLAG_OUTPUTS : STAI_FLAG_NONE;

// Check weights status
  for (idx=0; idx<STAI_WINDOW_MODEL_WEIGHTS_NUM; idx++) {
    if (net_ctx->_weights[idx] == NULL) break;
  }
  net_ctx->_flags |= (idx == STAI_WINDOW_MODEL_WEIGHTS_NUM) ? STAI_FLAG_WEIGHTS : STAI_FLAG_NONE;
STAI_PRINT("  [_stai_network_check] flags: 0x%08x\n", net_ctx->_flags)
}


/*****************************************************************************/
STAI_API_ENTRY
stai_return_code stai_window_model_init(
  stai_network* network)
{
  /* Memory where to store internal context is provided by applications as a raw byte buffer */
  _stai_window_model_context* net_ctx = (_stai_window_model_context*)(network);
  net_ctx->_return_code = STAI_SUCCESS;
  STAI_PRINT("[Entering Network Init] network(%p) context_size(%d)\n", net_ctx, (int32_t)sizeof(_stai_window_model_context))

  _STAI_SET_ERROR(net_ctx, STAI_WINDOW_MODEL_CONTEXT_SIZE != sizeof(_stai_window_model_context),
                 STAI_ERROR_NETWORK_INVALID_CONTEXT_SIZE, net_ctx->_return_code)

  {
    const _stai_window_model_context _window_model_context = {
      ._magic = STAI_MAGIC,
      ._signature = STAI_WINDOW_MODEL_MODEL_SIGNATURE,
      ._flags = STAI_WINDOW_MODEL_FLAGS,
      ._return_code = STAI_SUCCESS,
      ._callback = NULL,
      ._callback_cookie = NULL,
      ._activations = {
      (stai_ptr)g_window_model_activations_1
      },
      ._weights = {
      (stai_ptr)g_window_model_weights_array
      },
      ._inputs = {
    NULL},
      ._outputs = {
    NULL},
    };

    // Deep copy of internal context to opaque buffer provided by app
    *net_ctx = _window_model_context;

    _stai_window_model_check(net_ctx);
  }

  return net_ctx->_return_code;
}


STAI_API_ENTRY
stai_return_code stai_window_model_deinit(
  stai_network* network)
{
  _STAI_CONTEXT_ACQUIRE(net_ctx, network)

  /*  Reset flags to initial state  */
  net_ctx->_flags = STAI_WINDOW_MODEL_FLAGS;
  return net_ctx->_return_code;
}

/*****************************************************************************/



/* Int quant #0 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(row_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(0.10375061631202698f),
    AI_PACK_INTQ_ZP(-9)))

/* Int quant #1 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(_Reshape_output_0_to_chfirst_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(0.10375061631202698f),
    AI_PACK_INTQ_ZP(-9)))

/* Int quant #2 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(_Slice_output_0_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(0.10375061631202698f),
    AI_PACK_INTQ_ZP(-9)))

/* Int quant #3 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(_Slice_1_output_0_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(0.10375061631202698f),
    AI_PACK_INTQ_ZP(-9)))

/* Int quant #4 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(_Div_output_0_0_0__Transpose_output_0_conversion_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(0.471759170293808f),
    AI_PACK_INTQ_ZP(24)))

/* Int quant #5 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(_Transpose_output_0_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(0.471759170293808f),
    AI_PACK_INTQ_ZP(24)))

/* Int quant #6 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(_decoder_decoder_0_Relu_output_0_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(0.7686384916305542f),
    AI_PACK_INTQ_ZP(-128)))

/* Int quant #7 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(_decoder_decoder_2_Relu_output_0_upsample_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(0.7686384916305542f),
    AI_PACK_INTQ_ZP(-128)))

/* Int quant #8 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(_decoder_decoder_2_Relu_output_0_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(1.0637110471725464f),
    AI_PACK_INTQ_ZP(-128)))

/* Int quant #9 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(_decoder_decoder_3_ConvTranspose_output_0_upsample_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(1.0637110471725464f),
    AI_PACK_INTQ_ZP(-128)))

/* Int quant #10 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(_decoder_decoder_3_ConvTranspose_output_0_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(0.4818134307861328f),
    AI_PACK_INTQ_ZP(18)))

/* Int quant #11 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(_Slice_2_output_0_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(0.4818134307861328f),
    AI_PACK_INTQ_ZP(18)))

/* Int quant #12 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(_Transpose_1_output_0_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(0.4818134307861328f),
    AI_PACK_INTQ_ZP(18)))

/* Int quant #13 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(_Sub_1_output_0_0_0__Flatten_output_0_conversion_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(0.3594858944416046f),
    AI_PACK_INTQ_ZP(-2)))

/* Int quant #14 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(_Flatten_output_0_to_chlast_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(0.3594858944416046f),
    AI_PACK_INTQ_ZP(-2)))

/* Int quant #15 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(_Concat_output_0_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(0.3594858944416046f),
    AI_PACK_INTQ_ZP(-2)))

/* Int quant #16 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(_ConstantOfShape_output_0_DequantizeLinear_Output_const_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(1.0f),
    AI_PACK_INTQ_ZP(0)))

/* Int quant #17 */
AI_INTQ_INFO_LIST_OBJ_DECLARE(out_QuantizeLinear_Input_output_array_intq, AI_STATIC,
  AI_BUFFER_META_FLAG_SCALE_FLOAT|AI_BUFFER_META_FLAG_ZEROPOINT_S8, 1,
  AI_PACK_INTQ_INFO(
    AI_PACK_INTQ_SCALE(0.34493157267570496f),
    AI_PACK_INTQ_ZP(-9)))



/* Array#0 */
AI_ARRAY_OBJ_DECLARE(
  row_output_array, AI_ARRAY_FORMAT_S8|AI_FMT_FLAG_IS_IO,
  NULL, NULL, 850, AI_STATIC)

/* Array#1 */
AI_ARRAY_OBJ_DECLARE(
  _Reshape_output_0_to_chfirst_output_array, AI_ARRAY_FORMAT_S8,
  NULL, NULL, 850, AI_STATIC)

/* Array#2 */
AI_ARRAY_OBJ_DECLARE(
  _Slice_output_0_output_array, AI_ARRAY_FORMAT_S8,
  NULL, NULL, 833, AI_STATIC)

/* Array#3 */
AI_ARRAY_OBJ_DECLARE(
  _Slice_1_output_0_output_array, AI_ARRAY_FORMAT_S8,
  NULL, NULL, 833, AI_STATIC)

/* Array#4 */
AI_ARRAY_OBJ_DECLARE(
  _Slice_output_0_0_conversion_output_array, AI_ARRAY_FORMAT_FLOAT,
  NULL, NULL, 833, AI_STATIC)

/* Array#5 */
AI_ARRAY_OBJ_DECLARE(
  _Slice_1_output_0_0_1__Sub_output_0_conversion_output_array, AI_ARRAY_FORMAT_FLOAT,
  NULL, NULL, 833, AI_STATIC)

/* Array#6 */
AI_ARRAY_OBJ_DECLARE(
  _Sub_output_0_output_array, AI_ARRAY_FORMAT_FLOAT,
  NULL, NULL, 833, AI_STATIC)

/* Array#7 */
AI_ARRAY_OBJ_DECLARE(
  _Div_output_0_output_array, AI_ARRAY_FORMAT_FLOAT,
  NULL, NULL, 833, AI_STATIC)

/* Array#8 */
AI_ARRAY_OBJ_DECLARE(
  step_std_3D_array, AI_ARRAY_FORMAT_FLOAT,
  NULL, NULL, 17, AI_STATIC)

/* Array#9 */
AI_ARRAY_OBJ_DECLARE(
  _Div_output_0_0_0__Transpose_output_0_conversion_output_array, AI_ARRAY_FORMAT_S8,
  NULL, NULL, 833, AI_STATIC)

/* Array#10 */
AI_ARRAY_OBJ_DECLARE(
  _Transpose_output_0_output_array, AI_ARRAY_FORMAT_S8,
  NULL, NULL, 833, AI_STATIC)

/* Array#11 */
AI_ARRAY_OBJ_DECLARE(
  _decoder_decoder_0_Relu_output_0_output_array, AI_ARRAY_FORMAT_S8,
  NULL, NULL, 208, AI_STATIC)

/* Array#12 */
AI_ARRAY_OBJ_DECLARE(
  _decoder_decoder_2_Relu_output_0_upsample_output_array, AI_ARRAY_FORMAT_S8,
  NULL, NULL, 400, AI_STATIC)

/* Array#13 */
AI_ARRAY_OBJ_DECLARE(
  _decoder_decoder_2_Relu_output_0_output_array, AI_ARRAY_FORMAT_S8,
  NULL, NULL, 1664, AI_STATIC)

/* Array#14 */
AI_ARRAY_OBJ_DECLARE(
  _decoder_decoder_3_ConvTranspose_output_0_upsample_output_array, AI_ARRAY_FORMAT_S8,
  NULL, NULL, 3264, AI_STATIC)

/* Array#15 */
AI_ARRAY_OBJ_DECLARE(
  _decoder_decoder_3_ConvTranspose_output_0_output_array, AI_ARRAY_FORMAT_S8,
  NULL, NULL, 884, AI_STATIC)

/* Array#16 */
AI_ARRAY_OBJ_DECLARE(
  _Slice_2_output_0_output_array, AI_ARRAY_FORMAT_S8,
  NULL, NULL, 833, AI_STATIC)

/* Array#17 */
AI_ARRAY_OBJ_DECLARE(
  _Transpose_1_output_0_output_array, AI_ARRAY_FORMAT_S8,
  NULL, NULL, 833, AI_STATIC)

/* Array#18 */
AI_ARRAY_OBJ_DECLARE(
  _Transpose_1_output_0_0_0__Sub_1_output_0_conversion_output_array, AI_ARRAY_FORMAT_FLOAT,
  NULL, NULL, 833, AI_STATIC)

/* Array#19 */
AI_ARRAY_OBJ_DECLARE(
  _Sub_1_output_0_output_array, AI_ARRAY_FORMAT_FLOAT,
  NULL, NULL, 833, AI_STATIC)

/* Array#20 */
AI_ARRAY_OBJ_DECLARE(
  _Sub_1_output_0_0_0__Flatten_output_0_conversion_output_array, AI_ARRAY_FORMAT_S8,
  NULL, NULL, 833, AI_STATIC)

/* Array#21 */
AI_ARRAY_OBJ_DECLARE(
  _Flatten_output_0_to_chlast_output_array, AI_ARRAY_FORMAT_S8,
  NULL, NULL, 833, AI_STATIC)

/* Array#22 */
AI_ARRAY_OBJ_DECLARE(
  _Concat_output_0_output_array, AI_ARRAY_FORMAT_S8,
  NULL, NULL, 850, AI_STATIC)

/* Array#23 */
AI_ARRAY_OBJ_DECLARE(
  _ConstantOfShape_output_0_DequantizeLinear_Output_const_array, AI_ARRAY_FORMAT_S8,
  NULL, NULL, 17, AI_STATIC)

/* Array#24 */
AI_ARRAY_OBJ_DECLARE(
  out_QuantizeLinear_Input_output_array, AI_ARRAY_FORMAT_S8|AI_FMT_FLAG_IS_IO,
  NULL, NULL, 850, AI_STATIC)



/* Tensor #0 */
AI_TENSOR_OBJ_DECLARE(
  _Reshape_output_0_to_chfirst_output, AI_STATIC,
  6, 0x1,
  AI_SHAPE_INIT(4, 1, 50, 1, 17), AI_STRIDE_INIT(4, 1, 1, 50, 50),
  1, &_Reshape_output_0_to_chfirst_output_array, &_Reshape_output_0_to_chfirst_output_array_intq)

/* Tensor #1 */
AI_TENSOR_OBJ_DECLARE(
  row_output0, AI_STATIC,
  42, 0x1,
  AI_SHAPE_INIT(4, 1, 17, 1, 50), AI_STRIDE_INIT(4, 1, 1, 17, 17),
  1, &row_output_array, &row_output_array_intq)

/* Tensor #2 */
AI_TENSOR_OBJ_DECLARE(
  _Slice_output_0_output, AI_STATIC,
  11, 0x1,
  AI_SHAPE_INIT(4, 1, 49, 1, 17), AI_STRIDE_INIT(4, 1, 1, 49, 49),
  1, &_Slice_output_0_output_array, &_Slice_output_0_output_array_intq)

/* Tensor #3 */
AI_TENSOR_OBJ_DECLARE(
  _Slice_1_output_0_output, AI_STATIC,
  8, 0x1,
  AI_SHAPE_INIT(4, 1, 49, 1, 17), AI_STRIDE_INIT(4, 1, 1, 49, 49),
  1, &_Slice_1_output_0_output_array, &_Slice_1_output_0_output_array_intq)

/* Tensor #4 */
AI_TENSOR_OBJ_DECLARE(
  _Slice_1_output_0_0_1__Sub_output_0_conversion_output, AI_STATIC,
  7, 0x0,
  AI_SHAPE_INIT(4, 1, 49, 1, 17), AI_STRIDE_INIT(4, 4, 4, 196, 196),
  1, &_Slice_1_output_0_0_1__Sub_output_0_conversion_output_array, NULL)

/* Tensor #5 */
AI_TENSOR_OBJ_DECLARE(
  _Slice_output_0_0_conversion_output, AI_STATIC,
  10, 0x0,
  AI_SHAPE_INIT(4, 1, 49, 1, 17), AI_STRIDE_INIT(4, 4, 4, 196, 196),
  1, &_Slice_output_0_0_conversion_output_array, NULL)

/* Tensor #6 */
AI_TENSOR_OBJ_DECLARE(
  _Sub_output_0_output, AI_STATIC,
  14, 0x0,
  AI_SHAPE_INIT(4, 1, 49, 1, 17), AI_STRIDE_INIT(4, 4, 4, 196, 196),
  1, &_Sub_output_0_output_array, NULL)

/* Tensor #7 */
AI_TENSOR_OBJ_DECLARE(
  _Div_output_0_output, AI_STATIC,
  3, 0x0,
  AI_SHAPE_INIT(4, 1, 49, 1, 17), AI_STRIDE_INIT(4, 4, 4, 196, 196),
  1, &_Div_output_0_output_array, NULL)

/* Tensor #8 */
AI_TENSOR_OBJ_DECLARE(
  step_std_3D, AI_STATIC,
  43, 0x0,
  AI_SHAPE_INIT(4, 1, 1, 1, 17), AI_STRIDE_INIT(4, 4, 4, 4, 4),
  1, &step_std_3D_array, NULL)

/* Tensor #9 */
AI_TENSOR_OBJ_DECLARE(
  _Div_output_0_0_0__Transpose_output_0_conversion_output, AI_STATIC,
  2, 0x1,
  AI_SHAPE_INIT(4, 1, 49, 1, 17), AI_STRIDE_INIT(4, 1, 1, 49, 49),
  1, &_Div_output_0_0_0__Transpose_output_0_conversion_output_array, &_Div_output_0_0_0__Transpose_output_0_conversion_output_array_intq)

/* Tensor #10 */
AI_TENSOR_OBJ_DECLARE(
  _Transpose_output_0_output, AI_STATIC,
  17, 0x1,
  AI_SHAPE_INIT(4, 1, 17, 1, 49), AI_STRIDE_INIT(4, 1, 1, 17, 17),
  1, &_Transpose_output_0_output_array, &_Transpose_output_0_output_array_intq)

/* Tensor #11 */
AI_TENSOR_OBJ_DECLARE(
  _decoder_decoder_0_Relu_output_0_output, AI_STATIC,
  19, 0x1,
  AI_SHAPE_INIT(4, 1, 16, 1, 13), AI_STRIDE_INIT(4, 1, 1, 16, 16),
  1, &_decoder_decoder_0_Relu_output_0_output_array, &_decoder_decoder_0_Relu_output_0_output_array_intq)

/* Tensor #12 */
AI_TENSOR_OBJ_DECLARE(
  _decoder_decoder_2_Relu_output_0_upsample_output, AI_STATIC,
  27, 0x1,
  AI_SHAPE_INIT(4, 1, 16, 1, 25), AI_STRIDE_INIT(4, 1, 1, 16, 16),
  1, &_decoder_decoder_2_Relu_output_0_upsample_output_array, &_decoder_decoder_2_Relu_output_0_upsample_output_array_intq)

/* Tensor #13 */
AI_TENSOR_OBJ_DECLARE(
  _decoder_decoder_2_Relu_output_0_output, AI_STATIC,
  24, 0x1,
  AI_SHAPE_INIT(4, 1, 64, 1, 26), AI_STRIDE_INIT(4, 1, 1, 64, 64),
  1, &_decoder_decoder_2_Relu_output_0_output_array, &_decoder_decoder_2_Relu_output_0_output_array_intq)

/* Tensor #14 */
AI_TENSOR_OBJ_DECLARE(
  _decoder_decoder_3_ConvTranspose_output_0_upsample_output, AI_STATIC,
  33, 0x1,
  AI_SHAPE_INIT(4, 1, 64, 1, 51), AI_STRIDE_INIT(4, 1, 1, 64, 64),
  1, &_decoder_decoder_3_ConvTranspose_output_0_upsample_output_array, &_decoder_decoder_3_ConvTranspose_output_0_upsample_output_array_intq)

/* Tensor #15 */
AI_TENSOR_OBJ_DECLARE(
  _Slice_2_output_0_output, AI_STATIC,
  9, 0x1,
  AI_SHAPE_INIT(4, 1, 17, 1, 49), AI_STRIDE_INIT(4, 1, 1, 17, 17),
  1, &_Slice_2_output_0_output_array, &_Slice_2_output_0_output_array_intq)

/* Tensor #16 */
AI_TENSOR_OBJ_DECLARE(
  _decoder_decoder_3_ConvTranspose_output_0_output, AI_STATIC,
  30, 0x1,
  AI_SHAPE_INIT(4, 1, 17, 1, 52), AI_STRIDE_INIT(4, 1, 1, 17, 17),
  1, &_decoder_decoder_3_ConvTranspose_output_0_output_array, &_decoder_decoder_3_ConvTranspose_output_0_output_array_intq)

/* Tensor #17 */
AI_TENSOR_OBJ_DECLARE(
  _Transpose_1_output_0_output, AI_STATIC,
  16, 0x1,
  AI_SHAPE_INIT(4, 1, 49, 1, 17), AI_STRIDE_INIT(4, 1, 1, 49, 49),
  1, &_Transpose_1_output_0_output_array, &_Transpose_1_output_0_output_array_intq)

/* Tensor #18 */
AI_TENSOR_OBJ_DECLARE(
  _Sub_1_output_0_output, AI_STATIC,
  13, 0x0,
  AI_SHAPE_INIT(4, 1, 49, 1, 17), AI_STRIDE_INIT(4, 4, 4, 196, 196),
  1, &_Sub_1_output_0_output_array, NULL)

/* Tensor #19 */
AI_TENSOR_OBJ_DECLARE(
  _Transpose_1_output_0_0_0__Sub_1_output_0_conversion_output, AI_STATIC,
  15, 0x0,
  AI_SHAPE_INIT(4, 1, 49, 1, 17), AI_STRIDE_INIT(4, 4, 4, 196, 196),
  1, &_Transpose_1_output_0_0_0__Sub_1_output_0_conversion_output_array, NULL)

/* Tensor #20 */
AI_TENSOR_OBJ_DECLARE(
  _Flatten_output_0_to_chlast_output, AI_STATIC,
  4, 0x1,
  AI_SHAPE_INIT(4, 1, 17, 1, 49), AI_STRIDE_INIT(4, 1, 1, 17, 17),
  1, &_Flatten_output_0_to_chlast_output_array, &_Flatten_output_0_to_chlast_output_array_intq)

/* Tensor #21 */
AI_TENSOR_OBJ_DECLARE(
  _Sub_1_output_0_0_0__Flatten_output_0_conversion_output, AI_STATIC,
  12, 0x1,
  AI_SHAPE_INIT(4, 1, 49, 1, 17), AI_STRIDE_INIT(4, 1, 1, 49, 49),
  1, &_Sub_1_output_0_0_0__Flatten_output_0_conversion_output_array, &_Sub_1_output_0_0_0__Flatten_output_0_conversion_output_array_intq)

/* Tensor #22 */
AI_TENSOR_OBJ_DECLARE(
  _Concat_output_0_output, AI_STATIC,
  0, 0x1,
  AI_SHAPE_INIT(4, 1, 850, 1, 1), AI_STRIDE_INIT(4, 1, 1, 850, 850),
  1, &_Concat_output_0_output_array, &_Concat_output_0_output_array_intq)

/* Tensor #23 */
AI_TENSOR_OBJ_DECLARE(
  _ConstantOfShape_output_0_DequantizeLinear_Output_const, AI_STATIC,
  1, 0x1,
  AI_SHAPE_INIT(4, 1, 17, 1, 1), AI_STRIDE_INIT(4, 1, 1, 17, 17),
  1, &_ConstantOfShape_output_0_DequantizeLinear_Output_const_array, &_ConstantOfShape_output_0_DequantizeLinear_Output_const_array_intq)

/* Tensor #24 */
AI_TENSOR_OBJ_DECLARE(
  _Flatten_output_0_to_chlast_output0, AI_STATIC,
  5, 0x1,
  AI_SHAPE_INIT(4, 1, 833, 1, 1), AI_STRIDE_INIT(4, 1, 1, 833, 833),
  1, &_Flatten_output_0_to_chlast_output_array, &_Flatten_output_0_to_chlast_output_array_intq)

/* Tensor #25 */
AI_TENSOR_OBJ_DECLARE(
  out_QuantizeLinear_Input_output, AI_STATIC,
  40, 0x1,
  AI_SHAPE_INIT(4, 1, 850, 1, 1), AI_STRIDE_INIT(4, 1, 1, 850, 850),
  1, &out_QuantizeLinear_Input_output_array, &out_QuantizeLinear_Input_output_array_intq)

/* Tensor #26 */
AI_TENSOR_OBJ_DECLARE(
  row_output, AI_STATIC,
  41, 0x1,
  AI_SHAPE_INIT(4, 1, 850, 1, 1), AI_STRIDE_INIT(4, 1, 1, 850, 850),
  1, &row_output_array, &row_output_array_intq)


AI_TENSOR_CHAIN_OBJ_DECLARE(
  _Reshape_output_0_to_chfirst_chain, AI_STATIC_CONST, 4,
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &row_output0),
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_Reshape_output_0_to_chfirst_output),
  AI_TENSOR_LIST_OBJ_EMPTY,
  AI_TENSOR_LIST_OBJ_EMPTY
)

AI_LAYER_OBJ_DECLARE(
  _Reshape_output_0_to_chfirst_layer, 12,
  TRANSPOSE_TYPE, 0x0, NULL,
  transpose, forward_transpose,
  &_Reshape_output_0_to_chfirst_chain,
  NULL, &_Reshape_output_0_to_chfirst_layer, AI_STATIC, 
  .out_mapping = AI_SHAPE_INIT(6, AI_SHAPE_IN_CHANNEL, AI_SHAPE_HEIGHT, AI_SHAPE_WIDTH, AI_SHAPE_CHANNEL, AI_SHAPE_DEPTH, AI_SHAPE_EXTENSION), 
)


AI_STATIC_CONST ai_u8 _Slice_output_0_axes_data[] = { 2 };
AI_ARRAY_OBJ_DECLARE(
    _Slice_output_0_axes, AI_ARRAY_FORMAT_U8,
    _Slice_output_0_axes_data, _Slice_output_0_axes_data, 1, AI_STATIC_CONST)

AI_STATIC_CONST ai_i16 _Slice_output_0_starts_data[] = { 1 };
AI_ARRAY_OBJ_DECLARE(
    _Slice_output_0_starts, AI_ARRAY_FORMAT_S16,
    _Slice_output_0_starts_data, _Slice_output_0_starts_data, 1, AI_STATIC_CONST)

AI_STATIC_CONST ai_i16 _Slice_output_0_ends_data[] = { 50 };
AI_ARRAY_OBJ_DECLARE(
    _Slice_output_0_ends, AI_ARRAY_FORMAT_S16,
    _Slice_output_0_ends_data, _Slice_output_0_ends_data, 1, AI_STATIC_CONST)
AI_TENSOR_CHAIN_OBJ_DECLARE(
  _Slice_output_0_chain, AI_STATIC_CONST, 4,
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_Reshape_output_0_to_chfirst_output),
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_Slice_output_0_output),
  AI_TENSOR_LIST_OBJ_EMPTY,
  AI_TENSOR_LIST_OBJ_EMPTY
)

AI_LAYER_OBJ_DECLARE(
  _Slice_output_0_layer, 15,
  SLICE_TYPE, 0x0, NULL,
  slice, forward_slice,
  &_Slice_output_0_chain,
  NULL, &_Slice_output_0_layer, AI_STATIC, 
  .axes = &_Slice_output_0_axes, 
  .starts = &_Slice_output_0_starts, 
  .ends = &_Slice_output_0_ends, 
)


AI_STATIC_CONST ai_u8 _Slice_1_output_0_axes_data[] = { 2 };
AI_ARRAY_OBJ_DECLARE(
    _Slice_1_output_0_axes, AI_ARRAY_FORMAT_U8,
    _Slice_1_output_0_axes_data, _Slice_1_output_0_axes_data, 1, AI_STATIC_CONST)

AI_STATIC_CONST ai_i16 _Slice_1_output_0_starts_data[] = { 0 };
AI_ARRAY_OBJ_DECLARE(
    _Slice_1_output_0_starts, AI_ARRAY_FORMAT_S16,
    _Slice_1_output_0_starts_data, _Slice_1_output_0_starts_data, 1, AI_STATIC_CONST)

AI_STATIC_CONST ai_i16 _Slice_1_output_0_ends_data[] = { 49 };
AI_ARRAY_OBJ_DECLARE(
    _Slice_1_output_0_ends, AI_ARRAY_FORMAT_S16,
    _Slice_1_output_0_ends_data, _Slice_1_output_0_ends_data, 1, AI_STATIC_CONST)
AI_TENSOR_CHAIN_OBJ_DECLARE(
  _Slice_1_output_0_chain, AI_STATIC_CONST, 4,
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_Reshape_output_0_to_chfirst_output),
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_Slice_1_output_0_output),
  AI_TENSOR_LIST_OBJ_EMPTY,
  AI_TENSOR_LIST_OBJ_EMPTY
)

AI_LAYER_OBJ_DECLARE(
  _Slice_1_output_0_layer, 14,
  SLICE_TYPE, 0x0, NULL,
  slice, forward_slice,
  &_Slice_1_output_0_chain,
  NULL, &_Slice_1_output_0_layer, AI_STATIC, 
  .axes = &_Slice_1_output_0_axes, 
  .starts = &_Slice_1_output_0_starts, 
  .ends = &_Slice_1_output_0_ends, 
)

AI_TENSOR_CHAIN_OBJ_DECLARE(
  _Sub_output_0_chain, AI_STATIC_CONST, 4,
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 2, &_Slice_output_0_0_conversion_output, &_Slice_1_output_0_0_1__Sub_output_0_conversion_output),
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_Sub_output_0_output),
  AI_TENSOR_LIST_OBJ_EMPTY,
  AI_TENSOR_LIST_OBJ_EMPTY
)

AI_LAYER_OBJ_DECLARE(
  _Sub_output_0_layer, 17,
  ELTWISE_TYPE, 0x0, NULL,
  eltwise, forward_eltwise,
  &_Sub_output_0_chain,
  NULL, &_Sub_output_0_layer, AI_STATIC, 
  .operation = ai_sub_f32, 
  .buffer_operation = ai_sub_buffer_f32, 
)

AI_TENSOR_CHAIN_OBJ_DECLARE(
  _Div_output_0_chain, AI_STATIC_CONST, 4,
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 2, &_Sub_output_0_output, &step_std_3D),
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_Div_output_0_output),
  AI_TENSOR_LIST_OBJ_EMPTY,
  AI_TENSOR_LIST_OBJ_EMPTY
)

AI_LAYER_OBJ_DECLARE(
  _Div_output_0_layer, 19,
  ELTWISE_TYPE, 0x0, NULL,
  eltwise, forward_eltwise,
  &_Div_output_0_chain,
  NULL, &_Div_output_0_layer, AI_STATIC, 
  .operation = ai_div_f32, 
  .buffer_operation = ai_div_buffer_f32, 
)

AI_TENSOR_CHAIN_OBJ_DECLARE(
  _Transpose_output_0_chain, AI_STATIC_CONST, 4,
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_Div_output_0_0_0__Transpose_output_0_conversion_output),
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_Transpose_output_0_output),
  AI_TENSOR_LIST_OBJ_EMPTY,
  AI_TENSOR_LIST_OBJ_EMPTY
)

AI_LAYER_OBJ_DECLARE(
  _Transpose_output_0_layer, 21,
  TRANSPOSE_TYPE, 0x0, NULL,
  transpose, forward_transpose,
  &_Transpose_output_0_chain,
  NULL, &_Transpose_output_0_layer, AI_STATIC, 
  .out_mapping = AI_SHAPE_INIT(6, AI_SHAPE_IN_CHANNEL, AI_SHAPE_HEIGHT, AI_SHAPE_WIDTH, AI_SHAPE_CHANNEL, AI_SHAPE_DEPTH, AI_SHAPE_EXTENSION), 
)


AI_STATIC_CONST ai_float _decoder_decoder_2_Relu_output_0_upsample_scales_data[] = { 2, 1.0, 1.0, 1.0 };
AI_ARRAY_OBJ_DECLARE(
    _decoder_decoder_2_Relu_output_0_upsample_scales, AI_ARRAY_FORMAT_FLOAT,
    _decoder_decoder_2_Relu_output_0_upsample_scales_data, _decoder_decoder_2_Relu_output_0_upsample_scales_data, 4, AI_STATIC_CONST)
AI_TENSOR_CHAIN_OBJ_DECLARE(
  _decoder_decoder_2_Relu_output_0_upsample_chain, AI_STATIC_CONST, 4,
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_decoder_decoder_0_Relu_output_0_output),
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_decoder_decoder_2_Relu_output_0_upsample_output),
  AI_TENSOR_LIST_OBJ_EMPTY,
  AI_TENSOR_LIST_OBJ_EMPTY
)

AI_LAYER_OBJ_DECLARE(
  _decoder_decoder_2_Relu_output_0_upsample_layer, 30,
  UPSAMPLE_TYPE, 0x0, NULL,
  upsample, forward_upsample_zeros_is8os8,
  &_decoder_decoder_2_Relu_output_0_upsample_chain,
  NULL, &_decoder_decoder_2_Relu_output_0_upsample_layer, AI_STATIC, 
  .scales = &_decoder_decoder_2_Relu_output_0_upsample_scales, 
  .center = false, 
  .mode = AI_UPSAMPLE_ZEROS, 
  .nearest_mode = AI_ROUND_PREFER_CEIL, 
)


AI_STATIC_CONST ai_float _decoder_decoder_3_ConvTranspose_output_0_upsample_scales_data[] = { 2, 1.0, 1.0, 1.0 };
AI_ARRAY_OBJ_DECLARE(
    _decoder_decoder_3_ConvTranspose_output_0_upsample_scales, AI_ARRAY_FORMAT_FLOAT,
    _decoder_decoder_3_ConvTranspose_output_0_upsample_scales_data, _decoder_decoder_3_ConvTranspose_output_0_upsample_scales_data, 4, AI_STATIC_CONST)
AI_TENSOR_CHAIN_OBJ_DECLARE(
  _decoder_decoder_3_ConvTranspose_output_0_upsample_chain, AI_STATIC_CONST, 4,
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_decoder_decoder_2_Relu_output_0_output),
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_decoder_decoder_3_ConvTranspose_output_0_upsample_output),
  AI_TENSOR_LIST_OBJ_EMPTY,
  AI_TENSOR_LIST_OBJ_EMPTY
)

AI_LAYER_OBJ_DECLARE(
  _decoder_decoder_3_ConvTranspose_output_0_upsample_layer, 33,
  UPSAMPLE_TYPE, 0x0, NULL,
  upsample, forward_upsample_zeros_is8os8,
  &_decoder_decoder_3_ConvTranspose_output_0_upsample_chain,
  NULL, &_decoder_decoder_3_ConvTranspose_output_0_upsample_layer, AI_STATIC, 
  .scales = &_decoder_decoder_3_ConvTranspose_output_0_upsample_scales, 
  .center = false, 
  .mode = AI_UPSAMPLE_ZEROS, 
  .nearest_mode = AI_ROUND_PREFER_CEIL, 
)


AI_STATIC_CONST ai_u8 _Slice_2_output_0_axes_data[] = { 0 };
AI_ARRAY_OBJ_DECLARE(
    _Slice_2_output_0_axes, AI_ARRAY_FORMAT_U8,
    _Slice_2_output_0_axes_data, _Slice_2_output_0_axes_data, 1, AI_STATIC_CONST)

AI_STATIC_CONST ai_i16 _Slice_2_output_0_starts_data[] = { 0 };
AI_ARRAY_OBJ_DECLARE(
    _Slice_2_output_0_starts, AI_ARRAY_FORMAT_S16,
    _Slice_2_output_0_starts_data, _Slice_2_output_0_starts_data, 1, AI_STATIC_CONST)

AI_STATIC_CONST ai_i16 _Slice_2_output_0_ends_data[] = { 49 };
AI_ARRAY_OBJ_DECLARE(
    _Slice_2_output_0_ends, AI_ARRAY_FORMAT_S16,
    _Slice_2_output_0_ends_data, _Slice_2_output_0_ends_data, 1, AI_STATIC_CONST)
AI_TENSOR_CHAIN_OBJ_DECLARE(
  _Slice_2_output_0_chain, AI_STATIC_CONST, 4,
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_decoder_decoder_3_ConvTranspose_output_0_output),
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_Slice_2_output_0_output),
  AI_TENSOR_LIST_OBJ_EMPTY,
  AI_TENSOR_LIST_OBJ_EMPTY
)

AI_LAYER_OBJ_DECLARE(
  _Slice_2_output_0_layer, 36,
  SLICE_TYPE, 0x0, NULL,
  slice, forward_slice,
  &_Slice_2_output_0_chain,
  NULL, &_Slice_2_output_0_layer, AI_STATIC, 
  .axes = &_Slice_2_output_0_axes, 
  .starts = &_Slice_2_output_0_starts, 
  .ends = &_Slice_2_output_0_ends, 
)

AI_TENSOR_CHAIN_OBJ_DECLARE(
  _Transpose_1_output_0_chain, AI_STATIC_CONST, 4,
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_Slice_2_output_0_output),
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_Transpose_1_output_0_output),
  AI_TENSOR_LIST_OBJ_EMPTY,
  AI_TENSOR_LIST_OBJ_EMPTY
)

AI_LAYER_OBJ_DECLARE(
  _Transpose_1_output_0_layer, 37,
  TRANSPOSE_TYPE, 0x0, NULL,
  transpose, forward_transpose,
  &_Transpose_1_output_0_chain,
  NULL, &_Transpose_1_output_0_layer, AI_STATIC, 
  .out_mapping = AI_SHAPE_INIT(6, AI_SHAPE_IN_CHANNEL, AI_SHAPE_HEIGHT, AI_SHAPE_WIDTH, AI_SHAPE_CHANNEL, AI_SHAPE_DEPTH, AI_SHAPE_EXTENSION), 
)

AI_TENSOR_CHAIN_OBJ_DECLARE(
  _Sub_1_output_0_chain, AI_STATIC_CONST, 4,
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 2, &_Transpose_1_output_0_0_0__Sub_1_output_0_conversion_output, &_Div_output_0_output),
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_Sub_1_output_0_output),
  AI_TENSOR_LIST_OBJ_EMPTY,
  AI_TENSOR_LIST_OBJ_EMPTY
)

AI_LAYER_OBJ_DECLARE(
  _Sub_1_output_0_layer, 38,
  ELTWISE_TYPE, 0x0, NULL,
  eltwise, forward_eltwise,
  &_Sub_1_output_0_chain,
  NULL, &_Sub_1_output_0_layer, AI_STATIC, 
  .operation = ai_sub_f32, 
  .buffer_operation = ai_sub_buffer_f32, 
)

AI_TENSOR_CHAIN_OBJ_DECLARE(
  _Flatten_output_0_to_chlast_chain, AI_STATIC_CONST, 4,
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_Sub_1_output_0_0_0__Flatten_output_0_conversion_output),
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_Flatten_output_0_to_chlast_output),
  AI_TENSOR_LIST_OBJ_EMPTY,
  AI_TENSOR_LIST_OBJ_EMPTY
)

AI_LAYER_OBJ_DECLARE(
  _Flatten_output_0_to_chlast_layer, 39,
  TRANSPOSE_TYPE, 0x0, NULL,
  transpose, forward_transpose,
  &_Flatten_output_0_to_chlast_chain,
  NULL, &_Flatten_output_0_to_chlast_layer, AI_STATIC, 
  .out_mapping = AI_SHAPE_INIT(6, AI_SHAPE_IN_CHANNEL, AI_SHAPE_HEIGHT, AI_SHAPE_WIDTH, AI_SHAPE_CHANNEL, AI_SHAPE_DEPTH, AI_SHAPE_EXTENSION), 
)

AI_TENSOR_CHAIN_OBJ_DECLARE(
  _Concat_output_0_chain, AI_STATIC_CONST, 4,
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 2, &_ConstantOfShape_output_0_DequantizeLinear_Output_const, &_Flatten_output_0_to_chlast_output0),
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &_Concat_output_0_output),
  AI_TENSOR_LIST_OBJ_EMPTY,
  AI_TENSOR_LIST_OBJ_EMPTY
)

AI_LAYER_OBJ_DECLARE(
  _Concat_output_0_layer, 42,
  CONCAT_TYPE, 0x0, NULL,
  concat, forward_concat,
  &_Concat_output_0_chain,
  NULL, &_Concat_output_0_layer, AI_STATIC, 
  .axis = AI_SHAPE_CHANNEL, 
)

AI_TENSOR_CHAIN_OBJ_DECLARE(
  out_QuantizeLinear_Input_chain, AI_STATIC_CONST, 4,
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 2, &row_output, &_Concat_output_0_output),
  AI_TENSOR_LIST_OBJ_INIT(AI_FLAG_NONE, 1, &out_QuantizeLinear_Input_output),
  AI_TENSOR_LIST_OBJ_EMPTY,
  AI_TENSOR_LIST_OBJ_EMPTY
)

AI_LAYER_OBJ_DECLARE(
  out_QuantizeLinear_Input_layer, 45,
  ELTWISE_INTEGER_TYPE, 0x0, NULL,
  eltwise_integer, forward_eltwise_integer_INT8,
  &out_QuantizeLinear_Input_chain,
  NULL, &out_QuantizeLinear_Input_layer, AI_STATIC, 
  .operation = ai_sum_f32, 
  .buffer_operation = ai_sum_buffer_INT8, 
)
/**  Hybrid layers declarations section  *************************************/
void forward_lite_transpose__Reshape_output_0_to_chfirst(_stai_window_model_context* net_ctx)
{
  row_output_array.data = AI_PTR(net_ctx->_inputs[0] + 0);
  row_output_array.data_start = AI_PTR(net_ctx->_inputs[0] + 0);
  _Reshape_output_0_to_chfirst_output_array.data = AI_PTR(net_ctx->_activations[0] + 9372);
  _Reshape_output_0_to_chfirst_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 9372);
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(12, 1, { row_output0.data->data});
  forward_transpose(&_Reshape_output_0_to_chfirst_layer);
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(12, 1, { _Reshape_output_0_to_chfirst_output.data->data});
}
void forward_lite_slice__Slice_output_0(_stai_window_model_context* net_ctx)
{
  _Reshape_output_0_to_chfirst_output_array.data = AI_PTR(net_ctx->_activations[0] + 9372);
  _Reshape_output_0_to_chfirst_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 9372);
  _Slice_output_0_output_array.data = AI_PTR(net_ctx->_activations[0] + 11076);
  _Slice_output_0_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 11076);
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(15, 1, { _Reshape_output_0_to_chfirst_output.data->data});
  forward_slice(&_Slice_output_0_layer);
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(15, 1, { _Slice_output_0_output.data->data});
}
void forward_lite_slice__Slice_1_output_0(_stai_window_model_context* net_ctx)
{
  _Reshape_output_0_to_chfirst_output_array.data = AI_PTR(net_ctx->_activations[0] + 9372);
  _Reshape_output_0_to_chfirst_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 9372);
  _Slice_1_output_0_output_array.data = AI_PTR(net_ctx->_activations[0] + 11076);
  _Slice_1_output_0_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 11076);
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(14, 1, { _Reshape_output_0_to_chfirst_output.data->data});
  forward_slice(&_Slice_1_output_0_layer);
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(14, 1, { _Slice_1_output_0_output.data->data});
}
void forward_lite_eltwise__Sub_output_0(_stai_window_model_context* net_ctx)
{
  _Slice_output_0_0_conversion_output_array.data = AI_PTR(net_ctx->_activations[0] + 11912);
  _Slice_output_0_0_conversion_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 11912);
  _Slice_1_output_0_0_1__Sub_output_0_conversion_output_array.data = AI_PTR(net_ctx->_activations[0] + 6892);
  _Slice_1_output_0_0_1__Sub_output_0_conversion_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 6892);
  _Sub_output_0_output_array.data = AI_PTR(net_ctx->_activations[0] + 6892);
  _Sub_output_0_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 6892);
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(17, 2, { _Slice_output_0_0_conversion_output.data->data,_Slice_1_output_0_0_1__Sub_output_0_conversion_output.data->data});
  forward_eltwise(&_Sub_output_0_layer);
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(17, 1, { _Sub_output_0_output.data->data});
}
void forward_lite_eltwise__Div_output_0(_stai_window_model_context* net_ctx)
{
  _Sub_output_0_output_array.data = AI_PTR(net_ctx->_activations[0] + 6892);
  _Sub_output_0_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 6892);
  step_std_3D_array.data = AI_PTR(net_ctx->_weights[0] + 0);
  step_std_3D_array.data_start = AI_PTR(net_ctx->_weights[0] + 0);
  _Div_output_0_output_array.data = AI_PTR(net_ctx->_activations[0] + 11076);
  _Div_output_0_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 11076);
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(19, 2, { _Sub_output_0_output.data->data,step_std_3D.data->data});
  forward_eltwise(&_Div_output_0_layer);
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(19, 1, { _Div_output_0_output.data->data});
}
void forward_lite_transpose__Transpose_output_0(_stai_window_model_context* net_ctx)
{
  _Div_output_0_0_0__Transpose_output_0_conversion_output_array.data = AI_PTR(net_ctx->_activations[0] + 14408);
  _Div_output_0_0_0__Transpose_output_0_conversion_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 14408);
  _Transpose_output_0_output_array.data = AI_PTR(net_ctx->_activations[0] + 9388);
  _Transpose_output_0_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 9388);
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(21, 1, { _Div_output_0_0_0__Transpose_output_0_conversion_output.data->data});
  forward_transpose(&_Transpose_output_0_layer);
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(21, 1, { _Transpose_output_0_output.data->data});
}
void forward_lite_upsample_zeros_is8os8__decoder_decoder_2_Relu_output_0_upsample(_stai_window_model_context* net_ctx)
{
  _decoder_decoder_0_Relu_output_0_output_array.data = AI_PTR(net_ctx->_activations[0] + 15040);
  _decoder_decoder_0_Relu_output_0_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 15040);
  _decoder_decoder_2_Relu_output_0_upsample_output_array.data = AI_PTR(net_ctx->_activations[0] + 16512);
  _decoder_decoder_2_Relu_output_0_upsample_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 16512);
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(30, 1, { _decoder_decoder_0_Relu_output_0_output.data->data});
  forward_upsample_zeros_is8os8(&_decoder_decoder_2_Relu_output_0_upsample_layer);
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(30, 1, { _decoder_decoder_2_Relu_output_0_upsample_output.data->data});
}
void forward_lite_upsample_zeros_is8os8__decoder_decoder_3_ConvTranspose_output_0_upsample(_stai_window_model_context* net_ctx)
{
  _decoder_decoder_2_Relu_output_0_output_array.data = AI_PTR(net_ctx->_activations[0] + 15248);
  _decoder_decoder_2_Relu_output_0_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 15248);
  _decoder_decoder_3_ConvTranspose_output_0_upsample_output_array.data = AI_PTR(net_ctx->_activations[0] + 6960);
  _decoder_decoder_3_ConvTranspose_output_0_upsample_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 6960);
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(33, 1, { _decoder_decoder_2_Relu_output_0_output.data->data});
  forward_upsample_zeros_is8os8(&_decoder_decoder_3_ConvTranspose_output_0_upsample_layer);
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(33, 1, { _decoder_decoder_3_ConvTranspose_output_0_upsample_output.data->data});
}
void forward_lite_slice__Slice_2_output_0(_stai_window_model_context* net_ctx)
{
  _decoder_decoder_3_ConvTranspose_output_0_output_array.data = AI_PTR(net_ctx->_activations[0] + 14408);
  _decoder_decoder_3_ConvTranspose_output_0_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 14408);
  _Slice_2_output_0_output_array.data = AI_PTR(net_ctx->_activations[0] + 0);
  _Slice_2_output_0_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 0);
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(36, 1, { _decoder_decoder_3_ConvTranspose_output_0_output.data->data});
  forward_slice(&_Slice_2_output_0_layer);
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(36, 1, { _Slice_2_output_0_output.data->data});
}
void forward_lite_transpose__Transpose_1_output_0(_stai_window_model_context* net_ctx)
{
  _Slice_2_output_0_output_array.data = AI_PTR(net_ctx->_activations[0] + 0);
  _Slice_2_output_0_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 0);
  _Transpose_1_output_0_output_array.data = AI_PTR(net_ctx->_activations[0] + 836);
  _Transpose_1_output_0_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 836);
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(37, 1, { _Slice_2_output_0_output.data->data});
  forward_transpose(&_Transpose_1_output_0_layer);
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(37, 1, { _Transpose_1_output_0_output.data->data});
}
void forward_lite_eltwise__Sub_1_output_0(_stai_window_model_context* net_ctx)
{
  _Transpose_1_output_0_0_0__Sub_1_output_0_conversion_output_array.data = AI_PTR(net_ctx->_activations[0] + 1672);
  _Transpose_1_output_0_0_0__Sub_1_output_0_conversion_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 1672);
  _Div_output_0_output_array.data = AI_PTR(net_ctx->_activations[0] + 11076);
  _Div_output_0_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 11076);
  _Sub_1_output_0_output_array.data = AI_PTR(net_ctx->_activations[0] + 5004);
  _Sub_1_output_0_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 5004);
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(38, 2, { _Transpose_1_output_0_0_0__Sub_1_output_0_conversion_output.data->data,_Div_output_0_output.data->data});
  forward_eltwise(&_Sub_1_output_0_layer);
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(38, 1, { _Sub_1_output_0_output.data->data});
}
void forward_lite_transpose__Flatten_output_0_to_chlast(_stai_window_model_context* net_ctx)
{
  _Sub_1_output_0_0_0__Flatten_output_0_conversion_output_array.data = AI_PTR(net_ctx->_activations[0] + 0);
  _Sub_1_output_0_0_0__Flatten_output_0_conversion_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 0);
  _Flatten_output_0_to_chlast_output_array.data = AI_PTR(net_ctx->_activations[0] + 836);
  _Flatten_output_0_to_chlast_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 836);
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(39, 1, { _Sub_1_output_0_0_0__Flatten_output_0_conversion_output.data->data});
  forward_transpose(&_Flatten_output_0_to_chlast_layer);
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(39, 1, { _Flatten_output_0_to_chlast_output.data->data});
}
void forward_lite_concat__Concat_output_0(_stai_window_model_context* net_ctx)
{
  _ConstantOfShape_output_0_DequantizeLinear_Output_const_array.data = AI_PTR(net_ctx->_weights[0] + 68);
  _ConstantOfShape_output_0_DequantizeLinear_Output_const_array.data_start = AI_PTR(net_ctx->_weights[0] + 68);
  _Flatten_output_0_to_chlast_output_array.data = AI_PTR(net_ctx->_activations[0] + 836);
  _Flatten_output_0_to_chlast_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 836);
  _Concat_output_0_output_array.data = AI_PTR(net_ctx->_activations[0] + 1672);
  _Concat_output_0_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 1672);
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(42, 2, { _ConstantOfShape_output_0_DequantizeLinear_Output_const.data->data,_Flatten_output_0_to_chlast_output0.data->data});
  forward_concat(&_Concat_output_0_layer);
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(42, 1, { _Concat_output_0_output.data->data});
}
void forward_lite_eltwise_integer_INT8_out_QuantizeLinear_Input(_stai_window_model_context* net_ctx)
{
  row_output_array.data = AI_PTR(net_ctx->_inputs[0] + 0);
  row_output_array.data_start = AI_PTR(net_ctx->_inputs[0] + 0);
  _Concat_output_0_output_array.data = AI_PTR(net_ctx->_activations[0] + 1672);
  _Concat_output_0_output_array.data_start = AI_PTR(net_ctx->_activations[0] + 1672);
  out_QuantizeLinear_Input_output_array.data = AI_PTR(net_ctx->_outputs[0] + 0);
  out_QuantizeLinear_Input_output_array.data_start = AI_PTR(net_ctx->_outputs[0] + 0);
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(45, 2, { row_output.data->data,_Concat_output_0_output.data->data});
  forward_eltwise_integer_INT8(&out_QuantizeLinear_Input_layer);
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(45, 1, { out_QuantizeLinear_Input_output.data->data});
}

/*****************************************************************************/




static const ai_u32 _Slice_output_0_0_conversion_t_out_0_shape_h_w_ch_d_prod_const_u32 = 833;
static const ai_float _Slice_output_0_0_conversion_t_in_0_fmt_scale_const_f32 = 0.10375061631202698f;
static const ai_i8 _Slice_output_0_0_conversion_t_in_0_fmt_zero_const_s8 = -9;


static const ai_u32 _Slice_1_output_0_0_1__Sub_output_0_conversion_t_out_0_shape_h_w_ch_d_prod_const_u32 = 833;
static const ai_float _Slice_1_output_0_0_1__Sub_output_0_conversion_t_in_0_fmt_scale_const_f32 = 0.10375061631202698f;
static const ai_i8 _Slice_1_output_0_0_1__Sub_output_0_conversion_t_in_0_fmt_zero_const_s8 = -9;



static const ai_u32 _Div_output_0_0_0__Transpose_output_0_conversion_t_out_0_shape_h_w_ch_d_prod_const_u32 = 833;
static const ai_float _Div_output_0_0_0__Transpose_output_0_conversion_t_out_0_fmt_scale_const_f32 = 0.471759170293808f;
static const ai_i8 _Div_output_0_0_0__Transpose_output_0_conversion_t_out_0_fmt_zero_const_s8 = 24;


static const ai_i8 _encoder_encoder_1_Relu_output_0_pad_before_v_pad_constant_value_const_s8[] = LITE_ARRAY_VALUES(24);
static const ai_i16 _encoder_encoder_1_Relu_output_0_pad_before_t_in_0_fmt_bitsize_const_s16 = 8;
static const ai_u32 _encoder_encoder_1_Relu_output_0_pad_before_t_in_0_shape_h_const_u32 = 49;

static const ai_u16 _encoder_encoder_1_Relu_output_0_t_in_0_shape_w_const_u16 = 1;
static const ai_u16 _encoder_encoder_1_Relu_output_0_t_in_0_shape_h_const_u16 = 53;
static const ai_u16 _encoder_encoder_1_Relu_output_0_t_in_0_shape_ch_const_u16 = 17;
static const ai_u16 _encoder_encoder_1_Relu_output_0_t_out_0_shape_ch_const_u16 = 64;
static const ai_u16 _encoder_encoder_1_Relu_output_0_t_weight_0_shape_w_const_u16 = 1;
static const ai_u16 _encoder_encoder_1_Relu_output_0_t_weight_0_shape_h_const_u16 = 5;
static const ai_u16 _encoder_encoder_1_Relu_output_0_l_stride_1_const_u16 = 1;
static const ai_u16 _encoder_encoder_1_Relu_output_0_l_stride_0_const_u16 = 2;
static const ai_i8 _encoder_encoder_1_Relu_output_0_t_in_0_fmt_zero_const_s8 = 24;
static const ai_i8 _encoder_encoder_1_Relu_output_0_t_out_0_fmt_zero_const_s8 = -128;
static const ai_float _encoder_encoder_1_Relu_output_0_t_in_0_fmt_scale_const_f32 = 0.471759170293808f;
static const ai_float _encoder_encoder_1_Relu_output_0_t_out_0_fmt_scale_const_f32 = 0.5419297814369202f;
static const ai_float _encoder_encoder_1_Relu_output_0_t_weight_0_fmt_scale_const_f32[] = LITE_ARRAY_VALUES(0.004507720470428467f, 0.008659862913191319f, 0.007287140469998121f, 0.005874252878129482f, 0.009654035791754723f, 0.0060300626792013645f, 0.005277801305055618f, 0.01469135470688343f, 0.005256200674921274f, 0.005005266517400742f, 0.0033663136418908834f, 0.019123658537864685f, 0.010028915479779243f, 0.006481649819761515f, 0.0052950941026210785f, 0.009079499170184135f, 0.009657233953475952f, 0.003563173348084092f, 0.0061360914260149f, 0.007437450811266899f, 0.005302152130752802f, 0.008861172012984753f, 0.006022811401635408f, 0.008625723421573639f, 0.007233724929392338f, 0.02117783948779106f, 0.014748059213161469f, 0.010722603648900986f, 0.007781835272908211f, 0.005569185595959425f, 0.01993815414607525f, 0.006013892125338316f, 0.006122416816651821f, 0.003888309933245182f, 0.006264640484005213f, 0.008271249942481518f, 0.019820749759674072f, 0.013326041400432587f, 0.005534632597118616f, 0.003815975273028016f, 0.006740966811776161f, 0.008249754086136818f, 0.006832781247794628f, 0.029827401041984558f, 0.007130045909434557f, 0.010848050005733967f, 0.0032872469164431095f, 0.014951865188777447f, 0.005447111092507839f, 0.0036722442600876093f, 0.00791944470256567f, 0.0048806373961269855f, 0.006223605014383793f, 0.006029446143656969f, 0.005249718204140663f, 0.005421109031885862f, 0.00846812967211008f, 0.011713609099388123f, 0.004081577528268099f, 0.0068305423483252525f, 0.01089159119874239f, 0.004309599753469229f, 0.0058563873171806335f, 0.004973613657057285f);
static const ai_layer_format_type _encoder_encoder_1_Relu_output_0_l_out_ch_format_const_layer_format_type = AI_LAYER_FORMAT_CHANNEL_LAST_VALID;
static const ai_u16 _encoder_encoder_1_Relu_output_0_t_out_0_shape_w_const_u16 = 1;
static const ai_u16 _encoder_encoder_1_Relu_output_0_t_out_0_shape_h_const_u16 = 25;

static const ai_i8 _decoder_decoder_0_Relu_output_0_pad_before_v_pad_constant_value_const_s8[] = LITE_ARRAY_VALUES(-128);
static const ai_i16 _decoder_decoder_0_Relu_output_0_pad_before_t_in_0_fmt_bitsize_const_s16 = 8;
static const ai_u32 _decoder_decoder_0_Relu_output_0_pad_before_t_in_0_shape_h_const_u32 = 25;

static const ai_u16 _decoder_decoder_0_Relu_output_0_t_in_0_shape_w_const_u16 = 1;
static const ai_u16 _decoder_decoder_0_Relu_output_0_t_in_0_shape_h_const_u16 = 29;
static const ai_u16 _decoder_decoder_0_Relu_output_0_t_in_0_shape_ch_const_u16 = 64;
static const ai_u16 _decoder_decoder_0_Relu_output_0_t_out_0_shape_ch_const_u16 = 16;
static const ai_u16 _decoder_decoder_0_Relu_output_0_t_weight_0_shape_w_const_u16 = 1;
static const ai_u16 _decoder_decoder_0_Relu_output_0_t_weight_0_shape_h_const_u16 = 5;
static const ai_u16 _decoder_decoder_0_Relu_output_0_l_stride_1_const_u16 = 1;
static const ai_u16 _decoder_decoder_0_Relu_output_0_l_stride_0_const_u16 = 2;
static const ai_i8 _decoder_decoder_0_Relu_output_0_t_in_0_fmt_zero_const_s8 = -128;
static const ai_i8 _decoder_decoder_0_Relu_output_0_t_out_0_fmt_zero_const_s8 = -128;
static const ai_float _decoder_decoder_0_Relu_output_0_t_in_0_fmt_scale_const_f32 = 0.5419297814369202f;
static const ai_float _decoder_decoder_0_Relu_output_0_t_out_0_fmt_scale_const_f32 = 0.7686384916305542f;
static const ai_float _decoder_decoder_0_Relu_output_0_t_weight_0_fmt_scale_const_f32[] = LITE_ARRAY_VALUES(0.003948892001062632f, 0.003927211742848158f, 0.004562347661703825f, 0.006810904946178198f, 0.004145975690335035f, 0.004380472935736179f, 0.004161998629570007f, 0.006144536659121513f, 0.004522803705185652f, 0.0069500659592449665f, 0.004586977884173393f, 0.005825793370604515f, 0.00545166339725256f, 0.004547529388219118f, 0.003970485180616379f, 0.004602461587637663f);
static const ai_layer_format_type _decoder_decoder_0_Relu_output_0_l_out_ch_format_const_layer_format_type = AI_LAYER_FORMAT_CHANNEL_LAST_VALID;
static const ai_u16 _decoder_decoder_0_Relu_output_0_t_out_0_shape_w_const_u16 = 1;
static const ai_u16 _decoder_decoder_0_Relu_output_0_t_out_0_shape_h_const_u16 = 13;


static const ai_i8 _decoder_decoder_2_Relu_output_0_pad_before_v_pad_constant_value_const_s8[] = LITE_ARRAY_VALUES(-128);
static const ai_i16 _decoder_decoder_2_Relu_output_0_pad_before_t_in_0_fmt_bitsize_const_s16 = 8;
static const ai_u32 _decoder_decoder_2_Relu_output_0_pad_before_t_in_0_shape_h_const_u32 = 25;

static const ai_u16 _decoder_decoder_2_Relu_output_0_t_in_0_shape_w_const_u16 = 1;
static const ai_u16 _decoder_decoder_2_Relu_output_0_t_in_0_shape_h_const_u16 = 30;
static const ai_u16 _decoder_decoder_2_Relu_output_0_t_in_0_shape_ch_const_u16 = 16;
static const ai_u16 _decoder_decoder_2_Relu_output_0_t_out_0_shape_ch_const_u16 = 64;
static const ai_u16 _decoder_decoder_2_Relu_output_0_t_weight_0_shape_w_const_u16 = 1;
static const ai_u16 _decoder_decoder_2_Relu_output_0_t_weight_0_shape_h_const_u16 = 5;
static const ai_u16 _decoder_decoder_2_Relu_output_0_l_stride_1_const_u16 = 1;
static const ai_u16 _decoder_decoder_2_Relu_output_0_l_stride_0_const_u16 = 1;
static const ai_i8 _decoder_decoder_2_Relu_output_0_t_in_0_fmt_zero_const_s8 = -128;
static const ai_i8 _decoder_decoder_2_Relu_output_0_t_out_0_fmt_zero_const_s8 = -128;
static const ai_float _decoder_decoder_2_Relu_output_0_t_in_0_fmt_scale_const_f32 = 0.7686384916305542f;
static const ai_float _decoder_decoder_2_Relu_output_0_t_out_0_fmt_scale_const_f32 = 1.0637110471725464f;
static const ai_float _decoder_decoder_2_Relu_output_0_t_weight_0_fmt_scale_const_f32[] = LITE_ARRAY_VALUES(0.00567776570096612f, 0.004769477527588606f, 0.003835864132270217f, 0.00340586481615901f, 0.004436056595295668f, 0.0034227774012833834f, 0.003079045098274946f, 0.004518520552664995f, 0.0035664525348693132f, 0.006635146215558052f, 0.005299079231917858f, 0.0050933100283145905f, 0.006487263832241297f, 0.004091586451977491f, 0.012809257954359055f, 0.0032608311157673597f, 0.004570463206619024f, 0.0035963875707238913f, 0.005541094578802586f, 0.004928682465106249f, 0.004877930041402578f, 0.0037235405761748552f, 0.00869941059499979f, 0.0045450120232999325f, 0.006276002153754234f, 0.005197771824896336f, 0.006855009589344263f, 0.003250822192057967f, 0.004925575107336044f, 0.003987619653344154f, 0.004497241694480181f, 0.003218830795958638f, 0.004063776694238186f, 0.003953325562179089f, 0.0067918561398983f, 0.0032870080322027206f, 0.00533269764855504f, 0.004776885733008385f, 0.004541817121207714f, 0.00457736337557435f, 0.007519276812672615f, 0.004988387692719698f, 0.0031235171481966972f, 0.004854309838265181f, 0.004475842230021954f, 0.004058009944856167f, 0.00249302014708519f, 0.003352554515004158f, 0.004516899585723877f, 0.0029517097864300013f, 0.005376411601901054f, 0.004330785945057869f, 0.00304843345656991f, 0.004745548591017723f, 0.002411442808806896f, 0.0036163432523608208f, 0.004223247058689594f, 0.0006569207180291414f, 0.00438661128282547f, 0.0028185094706714153f, 0.004873309750109911f, 0.002315745921805501f, 0.004018853418529034f, 0.003637260291725397f);
static const ai_layer_format_type _decoder_decoder_2_Relu_output_0_l_out_ch_format_const_layer_format_type = AI_LAYER_FORMAT_CHANNEL_LAST_VALID;
static const ai_u16 _decoder_decoder_2_Relu_output_0_t_out_0_shape_w_const_u16 = 1;
static const ai_u16 _decoder_decoder_2_Relu_output_0_t_out_0_shape_h_const_u16 = 26;


static const ai_i8 _decoder_decoder_3_ConvTranspose_output_0_pad_before_v_pad_constant_value_const_s8[] = LITE_ARRAY_VALUES(-128);
static const ai_i16 _decoder_decoder_3_ConvTranspose_output_0_pad_before_t_in_0_fmt_bitsize_const_s16 = 8;
static const ai_u32 _decoder_decoder_3_ConvTranspose_output_0_pad_before_t_in_0_shape_h_const_u32 = 51;

static const ai_u16 _decoder_decoder_3_ConvTranspose_output_0_t_in_0_shape_w_const_u16 = 1;
static const ai_u16 _decoder_decoder_3_ConvTranspose_output_0_t_in_0_shape_h_const_u16 = 56;
static const ai_u16 _decoder_decoder_3_ConvTranspose_output_0_t_in_0_shape_ch_const_u16 = 64;
static const ai_u16 _decoder_decoder_3_ConvTranspose_output_0_t_out_0_shape_ch_const_u16 = 17;
static const ai_u16 _decoder_decoder_3_ConvTranspose_output_0_t_weight_0_shape_w_const_u16 = 1;
static const ai_u16 _decoder_decoder_3_ConvTranspose_output_0_t_weight_0_shape_h_const_u16 = 5;
static const ai_u16 _decoder_decoder_3_ConvTranspose_output_0_l_stride_1_const_u16 = 1;
static const ai_u16 _decoder_decoder_3_ConvTranspose_output_0_l_stride_0_const_u16 = 1;
static const ai_i8 _decoder_decoder_3_ConvTranspose_output_0_t_in_0_fmt_zero_const_s8 = -128;
static const ai_i8 _decoder_decoder_3_ConvTranspose_output_0_t_out_0_fmt_zero_const_s8 = 18;
static const ai_float _decoder_decoder_3_ConvTranspose_output_0_t_in_0_fmt_scale_const_f32 = 1.0637110471725464f;
static const ai_float _decoder_decoder_3_ConvTranspose_output_0_t_out_0_fmt_scale_const_f32 = 0.4818134307861328f;
static const ai_float _decoder_decoder_3_ConvTranspose_output_0_t_weight_0_fmt_scale_const_f32[] = LITE_ARRAY_VALUES(0.005247607361525297f, 0.003385861637070775f, 0.010901224799454212f, 0.007699187844991684f, 0.008548980578780174f, 0.006523168180137873f, 0.0042844186536967754f, 0.00327678257599473f, 0.013179134577512741f, 0.009880641475319862f, 0.01434401236474514f, 0.01037674956023693f, 0.0032483565155416727f, 0.010688120499253273f, 0.0025787127669900656f, 0.005558416713029146f, 0.006109355483204126f);
static const ai_layer_format_type _decoder_decoder_3_ConvTranspose_output_0_l_out_ch_format_const_layer_format_type = AI_LAYER_FORMAT_CHANNEL_LAST_VALID;
static const ai_u16 _decoder_decoder_3_ConvTranspose_output_0_t_out_0_shape_w_const_u16 = 1;
static const ai_u16 _decoder_decoder_3_ConvTranspose_output_0_t_out_0_shape_h_const_u16 = 52;



static const ai_u32 _Transpose_1_output_0_0_0__Sub_1_output_0_conversion_t_out_0_shape_h_w_ch_d_prod_const_u32 = 833;
static const ai_float _Transpose_1_output_0_0_0__Sub_1_output_0_conversion_t_in_0_fmt_scale_const_f32 = 0.4818134307861328f;
static const ai_i8 _Transpose_1_output_0_0_0__Sub_1_output_0_conversion_t_in_0_fmt_zero_const_s8 = 18;


static const ai_u32 _Sub_1_output_0_0_0__Flatten_output_0_conversion_t_out_0_shape_h_w_ch_d_prod_const_u32 = 833;
static const ai_float _Sub_1_output_0_0_0__Flatten_output_0_conversion_t_out_0_fmt_scale_const_f32 = 0.3594858944416046f;
static const ai_i8 _Sub_1_output_0_0_0__Flatten_output_0_conversion_t_out_0_fmt_zero_const_s8 = -2;



STAI_API_ENTRY
stai_return_code stai_window_model_run(
  stai_network* network,
  const stai_run_mode mode)
{
   STAI_UNUSED(mode)
  _STAI_CONTEXT_ACQUIRE(net_ctx, network)

  _STAI_SET_ERROR(net_ctx, (net_ctx->_flags & STAI_FLAG_ACTIVATIONS) != STAI_FLAG_ACTIVATIONS,
        STAI_ERROR_NETWORK_INVALID_ACTIVATIONS_PTR, net_ctx->_return_code)

  _STAI_SET_ERROR(net_ctx, (net_ctx->_flags & STAI_FLAG_INPUTS) != STAI_FLAG_INPUTS,
                  STAI_ERROR_NETWORK_INVALID_IN_PTR, net_ctx->_return_code)
  _STAI_SET_ERROR(net_ctx, (net_ctx->_flags & STAI_FLAG_OUTPUTS) != STAI_FLAG_OUTPUTS,
                  STAI_ERROR_NETWORK_INVALID_OUT_PTR, net_ctx->_return_code)

  _STAI_SET_ERROR(net_ctx, (net_ctx->_flags & STAI_FLAG_WEIGHTS) != STAI_FLAG_WEIGHTS,
                  STAI_ERROR_NETWORK_INVALID_WEIGHTS_PTR, net_ctx->_return_code)


  /* LITE_KERNEL_SECTION BEGIN _Reshape_output_0_to_chfirst */
  {
    
  forward_lite_transpose__Reshape_output_0_to_chfirst(net_ctx);
  }
  /* LITE_KERNEL_SECTION END _Reshape_output_0_to_chfirst */
  /* LITE_KERNEL_SECTION BEGIN _Slice_output_0 */
  {
    
  forward_lite_slice__Slice_output_0(net_ctx);
  }
  /* LITE_KERNEL_SECTION END _Slice_output_0 */
  /* LITE_KERNEL_SECTION BEGIN _Slice_output_0_0_conversion */
  {
      const ai_i8* _Slice_output_0_0_conversion_t_in_0_ptr_const_s8 = (ai_i8*)(net_ctx->_activations[0] + 11076);
    ai_float* _Slice_output_0_0_conversion_t_out_0_ptr_f32 = (ai_float*)(net_ctx->_activations[0] + 11912);
  
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(15, 1, {(stai_ptr) _Slice_output_0_0_conversion_t_in_0_ptr_const_s8});
    
  forward_lite_node_convert_integer_is8of32(_Slice_output_0_0_conversion_t_in_0_ptr_const_s8, _Slice_output_0_0_conversion_t_out_0_ptr_f32, _Slice_output_0_0_conversion_t_out_0_shape_h_w_ch_d_prod_const_u32, _Slice_output_0_0_conversion_t_in_0_fmt_scale_const_f32, _Slice_output_0_0_conversion_t_in_0_fmt_zero_const_s8);
    
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(15, 1, {(stai_ptr) _Slice_output_0_0_conversion_t_out_0_ptr_f32});
  }
  /* LITE_KERNEL_SECTION END _Slice_output_0_0_conversion */
  /* LITE_KERNEL_SECTION BEGIN _Slice_1_output_0 */
  {
    
  forward_lite_slice__Slice_1_output_0(net_ctx);
  }
  /* LITE_KERNEL_SECTION END _Slice_1_output_0 */
  /* LITE_KERNEL_SECTION BEGIN _Slice_1_output_0_0_1__Sub_output_0_conversion */
  {
      const ai_i8* _Slice_1_output_0_0_1__Sub_output_0_conversion_t_in_0_ptr_const_s8 = (ai_i8*)(net_ctx->_activations[0] + 11076);
    ai_float* _Slice_1_output_0_0_1__Sub_output_0_conversion_t_out_0_ptr_f32 = (ai_float*)(net_ctx->_activations[0] + 6892);
  
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(14, 1, {(stai_ptr) _Slice_1_output_0_0_1__Sub_output_0_conversion_t_in_0_ptr_const_s8});
    
  forward_lite_node_convert_integer_is8of32(_Slice_1_output_0_0_1__Sub_output_0_conversion_t_in_0_ptr_const_s8, _Slice_1_output_0_0_1__Sub_output_0_conversion_t_out_0_ptr_f32, _Slice_1_output_0_0_1__Sub_output_0_conversion_t_out_0_shape_h_w_ch_d_prod_const_u32, _Slice_1_output_0_0_1__Sub_output_0_conversion_t_in_0_fmt_scale_const_f32, _Slice_1_output_0_0_1__Sub_output_0_conversion_t_in_0_fmt_zero_const_s8);
    
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(14, 1, {(stai_ptr) _Slice_1_output_0_0_1__Sub_output_0_conversion_t_out_0_ptr_f32});
  }
  /* LITE_KERNEL_SECTION END _Slice_1_output_0_0_1__Sub_output_0_conversion */
  /* LITE_KERNEL_SECTION BEGIN _Sub_output_0 */
  {
    
  forward_lite_eltwise__Sub_output_0(net_ctx);
  }
  /* LITE_KERNEL_SECTION END _Sub_output_0 */
  /* LITE_KERNEL_SECTION BEGIN _Div_output_0 */
  {
    
  forward_lite_eltwise__Div_output_0(net_ctx);
  }
  /* LITE_KERNEL_SECTION END _Div_output_0 */
  /* LITE_KERNEL_SECTION BEGIN _Div_output_0_0_0__Transpose_output_0_conversion */
  {
      const ai_float* _Div_output_0_0_0__Transpose_output_0_conversion_t_in_0_ptr_const_f32 = (ai_float*)(net_ctx->_activations[0] + 11076);
    ai_i8* _Div_output_0_0_0__Transpose_output_0_conversion_t_out_0_ptr_s8 = (ai_i8*)(net_ctx->_activations[0] + 14408);
  
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(19, 1, {(stai_ptr) _Div_output_0_0_0__Transpose_output_0_conversion_t_in_0_ptr_const_f32});
    
  forward_lite_node_convert_integer_if32os8(_Div_output_0_0_0__Transpose_output_0_conversion_t_in_0_ptr_const_f32, _Div_output_0_0_0__Transpose_output_0_conversion_t_out_0_ptr_s8, _Div_output_0_0_0__Transpose_output_0_conversion_t_out_0_shape_h_w_ch_d_prod_const_u32, _Div_output_0_0_0__Transpose_output_0_conversion_t_out_0_fmt_scale_const_f32, _Div_output_0_0_0__Transpose_output_0_conversion_t_out_0_fmt_zero_const_s8);
    
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(19, 1, {(stai_ptr) _Div_output_0_0_0__Transpose_output_0_conversion_t_out_0_ptr_s8});
  }
  /* LITE_KERNEL_SECTION END _Div_output_0_0_0__Transpose_output_0_conversion */
  /* LITE_KERNEL_SECTION BEGIN _Transpose_output_0 */
  {
    
  forward_lite_transpose__Transpose_output_0(net_ctx);
  }
  /* LITE_KERNEL_SECTION END _Transpose_output_0 */
  /* LITE_KERNEL_SECTION BEGIN _encoder_encoder_1_Relu_output_0_pad_before */
  {
      const ai_ptr _encoder_encoder_1_Relu_output_0_pad_before_t_in_0_ptr_const_ptr = (ai_ptr)(net_ctx->_activations[0] + 9388);
    ai_ptr _encoder_encoder_1_Relu_output_0_pad_before_t_out_0_ptr_ptr = (ai_ptr)(net_ctx->_activations[0] + 14408);
  
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(24, 1, {(stai_ptr) _encoder_encoder_1_Relu_output_0_pad_before_t_in_0_ptr_const_ptr});
    
  forward_lite_pad_constant(_encoder_encoder_1_Relu_output_0_pad_before_t_in_0_ptr_const_ptr, _encoder_encoder_1_Relu_output_0_pad_before_t_out_0_ptr_ptr, (ai_handle)(_encoder_encoder_1_Relu_output_0_pad_before_v_pad_constant_value_const_s8), _encoder_encoder_1_Relu_output_0_pad_before_t_in_0_fmt_bitsize_const_s16, _encoder_encoder_1_Relu_output_0_pad_before_t_in_0_shape_h_const_u32, (ai_i32)(1), (ai_i32)(17), (ai_i32)(34), (ai_i32)(34), (ai_i32)(0), (ai_i32)(0));
    
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(24, 1, {(stai_ptr) _encoder_encoder_1_Relu_output_0_pad_before_t_out_0_ptr_ptr});
  }
  /* LITE_KERNEL_SECTION END _encoder_encoder_1_Relu_output_0_pad_before */
  /* LITE_KERNEL_SECTION BEGIN _encoder_encoder_1_Relu_output_0 */
  {
      const ai_i8* _encoder_encoder_1_Relu_output_0_t_in_0_ptr_const_s8 = (ai_i8*)(net_ctx->_activations[0] + 14408);
    const ai_i8* _encoder_encoder_1_Relu_output_0_t_weight_0_ptr_const_s8 = (ai_i8*)(net_ctx->_weights[0] + 88);
    const ai_i32* _encoder_encoder_1_Relu_output_0_t_weight_1_ptr_const_s32 = (ai_i32*)(net_ctx->_weights[0] + 5528);
    ai_i8* _encoder_encoder_1_Relu_output_0_t_out_0_ptr_s8 = (ai_i8*)(net_ctx->_activations[0] + 15312);
    ai_i16* _encoder_encoder_1_Relu_output_0_t_scratch_0_ptr_s16 = (ai_i16*)(net_ctx->_activations[0] + 3868);
  
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(24, 1, {(stai_ptr) _encoder_encoder_1_Relu_output_0_t_in_0_ptr_const_s8});
    
  forward_lite_conv2d_deep_sssa8_ch(_encoder_encoder_1_Relu_output_0_t_in_0_ptr_const_s8, _encoder_encoder_1_Relu_output_0_t_in_0_shape_w_const_u16, _encoder_encoder_1_Relu_output_0_t_in_0_shape_h_const_u16, _encoder_encoder_1_Relu_output_0_t_in_0_shape_ch_const_u16, _encoder_encoder_1_Relu_output_0_t_weight_0_ptr_const_s8, _encoder_encoder_1_Relu_output_0_t_out_0_shape_ch_const_u16, _encoder_encoder_1_Relu_output_0_t_weight_0_shape_w_const_u16, _encoder_encoder_1_Relu_output_0_t_weight_0_shape_h_const_u16, _encoder_encoder_1_Relu_output_0_l_stride_1_const_u16, _encoder_encoder_1_Relu_output_0_l_stride_0_const_u16, _encoder_encoder_1_Relu_output_0_t_weight_1_ptr_const_s32, _encoder_encoder_1_Relu_output_0_t_in_0_fmt_zero_const_s8, _encoder_encoder_1_Relu_output_0_t_out_0_fmt_zero_const_s8, _encoder_encoder_1_Relu_output_0_t_in_0_fmt_scale_const_f32, _encoder_encoder_1_Relu_output_0_t_out_0_fmt_scale_const_f32, _encoder_encoder_1_Relu_output_0_t_weight_0_fmt_scale_const_f32, _encoder_encoder_1_Relu_output_0_l_out_ch_format_const_layer_format_type, _encoder_encoder_1_Relu_output_0_t_out_0_ptr_s8, _encoder_encoder_1_Relu_output_0_t_out_0_shape_w_const_u16, _encoder_encoder_1_Relu_output_0_t_out_0_shape_h_const_u16, 1, 1, 6356, _encoder_encoder_1_Relu_output_0_t_scratch_0_ptr_s16);
    
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(24, 1, {(stai_ptr) _encoder_encoder_1_Relu_output_0_t_out_0_ptr_s8});
  }
  /* LITE_KERNEL_SECTION END _encoder_encoder_1_Relu_output_0 */
  /* LITE_KERNEL_SECTION BEGIN _decoder_decoder_0_Relu_output_0_pad_before */
  {
      const ai_ptr _decoder_decoder_0_Relu_output_0_pad_before_t_in_0_ptr_const_ptr = (ai_ptr)(net_ctx->_activations[0] + 15312);
    ai_ptr _decoder_decoder_0_Relu_output_0_pad_before_t_out_0_ptr_ptr = (ai_ptr)(net_ctx->_activations[0] + 15056);
  
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(27, 1, {(stai_ptr) _decoder_decoder_0_Relu_output_0_pad_before_t_in_0_ptr_const_ptr});
    
  forward_lite_pad_constant(_decoder_decoder_0_Relu_output_0_pad_before_t_in_0_ptr_const_ptr, _decoder_decoder_0_Relu_output_0_pad_before_t_out_0_ptr_ptr, (ai_handle)(_decoder_decoder_0_Relu_output_0_pad_before_v_pad_constant_value_const_s8), _decoder_decoder_0_Relu_output_0_pad_before_t_in_0_fmt_bitsize_const_s16, _decoder_decoder_0_Relu_output_0_pad_before_t_in_0_shape_h_const_u32, (ai_i32)(1), (ai_i32)(64), (ai_i32)(128), (ai_i32)(128), (ai_i32)(0), (ai_i32)(0));
    
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(27, 1, {(stai_ptr) _decoder_decoder_0_Relu_output_0_pad_before_t_out_0_ptr_ptr});
  }
  /* LITE_KERNEL_SECTION END _decoder_decoder_0_Relu_output_0_pad_before */
  /* LITE_KERNEL_SECTION BEGIN _decoder_decoder_0_Relu_output_0 */
  {
      const ai_i8* _decoder_decoder_0_Relu_output_0_t_in_0_ptr_const_s8 = (ai_i8*)(net_ctx->_activations[0] + 15056);
    const ai_i8* _decoder_decoder_0_Relu_output_0_t_weight_0_ptr_const_s8 = (ai_i8*)(net_ctx->_weights[0] + 5784);
    const ai_i32* _decoder_decoder_0_Relu_output_0_t_weight_1_ptr_const_s32 = (ai_i32*)(net_ctx->_weights[0] + 10904);
    ai_i8* _decoder_decoder_0_Relu_output_0_t_out_0_ptr_s8 = (ai_i8*)(net_ctx->_activations[0] + 15040);
    ai_i16* _decoder_decoder_0_Relu_output_0_t_scratch_0_ptr_s16 = (ai_i16*)(net_ctx->_activations[0] + 3600);
  
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(27, 1, {(stai_ptr) _decoder_decoder_0_Relu_output_0_t_in_0_ptr_const_s8});
    
  forward_lite_conv2d_deep_sssa8_ch(_decoder_decoder_0_Relu_output_0_t_in_0_ptr_const_s8, _decoder_decoder_0_Relu_output_0_t_in_0_shape_w_const_u16, _decoder_decoder_0_Relu_output_0_t_in_0_shape_h_const_u16, _decoder_decoder_0_Relu_output_0_t_in_0_shape_ch_const_u16, _decoder_decoder_0_Relu_output_0_t_weight_0_ptr_const_s8, _decoder_decoder_0_Relu_output_0_t_out_0_shape_ch_const_u16, _decoder_decoder_0_Relu_output_0_t_weight_0_shape_w_const_u16, _decoder_decoder_0_Relu_output_0_t_weight_0_shape_h_const_u16, _decoder_decoder_0_Relu_output_0_l_stride_1_const_u16, _decoder_decoder_0_Relu_output_0_l_stride_0_const_u16, _decoder_decoder_0_Relu_output_0_t_weight_1_ptr_const_s32, _decoder_decoder_0_Relu_output_0_t_in_0_fmt_zero_const_s8, _decoder_decoder_0_Relu_output_0_t_out_0_fmt_zero_const_s8, _decoder_decoder_0_Relu_output_0_t_in_0_fmt_scale_const_f32, _decoder_decoder_0_Relu_output_0_t_out_0_fmt_scale_const_f32, _decoder_decoder_0_Relu_output_0_t_weight_0_fmt_scale_const_f32, _decoder_decoder_0_Relu_output_0_l_out_ch_format_const_layer_format_type, _decoder_decoder_0_Relu_output_0_t_out_0_ptr_s8, _decoder_decoder_0_Relu_output_0_t_out_0_shape_w_const_u16, _decoder_decoder_0_Relu_output_0_t_out_0_shape_h_const_u16, 1, 1, 6624, _decoder_decoder_0_Relu_output_0_t_scratch_0_ptr_s16);
    
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(27, 1, {(stai_ptr) _decoder_decoder_0_Relu_output_0_t_out_0_ptr_s8});
  }
  /* LITE_KERNEL_SECTION END _decoder_decoder_0_Relu_output_0 */
  /* LITE_KERNEL_SECTION BEGIN _decoder_decoder_2_Relu_output_0_upsample */
  {
    
  forward_lite_upsample_zeros_is8os8__decoder_decoder_2_Relu_output_0_upsample(net_ctx);
  }
  /* LITE_KERNEL_SECTION END _decoder_decoder_2_Relu_output_0_upsample */
  /* LITE_KERNEL_SECTION BEGIN _decoder_decoder_2_Relu_output_0_pad_before */
  {
      const ai_ptr _decoder_decoder_2_Relu_output_0_pad_before_t_in_0_ptr_const_ptr = (ai_ptr)(net_ctx->_activations[0] + 16512);
    ai_ptr _decoder_decoder_2_Relu_output_0_pad_before_t_out_0_ptr_ptr = (ai_ptr)(net_ctx->_activations[0] + 9744);
  
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(30, 1, {(stai_ptr) _decoder_decoder_2_Relu_output_0_pad_before_t_in_0_ptr_const_ptr});
    
  forward_lite_pad_constant(_decoder_decoder_2_Relu_output_0_pad_before_t_in_0_ptr_const_ptr, _decoder_decoder_2_Relu_output_0_pad_before_t_out_0_ptr_ptr, (ai_handle)(_decoder_decoder_2_Relu_output_0_pad_before_v_pad_constant_value_const_s8), _decoder_decoder_2_Relu_output_0_pad_before_t_in_0_fmt_bitsize_const_s16, _decoder_decoder_2_Relu_output_0_pad_before_t_in_0_shape_h_const_u32, (ai_i32)(1), (ai_i32)(16), (ai_i32)(32), (ai_i32)(48), (ai_i32)(0), (ai_i32)(0));
    
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(30, 1, {(stai_ptr) _decoder_decoder_2_Relu_output_0_pad_before_t_out_0_ptr_ptr});
  }
  /* LITE_KERNEL_SECTION END _decoder_decoder_2_Relu_output_0_pad_before */
  /* LITE_KERNEL_SECTION BEGIN _decoder_decoder_2_Relu_output_0 */
  {
      const ai_i8* _decoder_decoder_2_Relu_output_0_t_in_0_ptr_const_s8 = (ai_i8*)(net_ctx->_activations[0] + 9744);
    const ai_i8* _decoder_decoder_2_Relu_output_0_t_weight_0_ptr_const_s8 = (ai_i8*)(net_ctx->_weights[0] + 10968);
    const ai_i32* _decoder_decoder_2_Relu_output_0_t_weight_1_ptr_const_s32 = (ai_i32*)(net_ctx->_weights[0] + 16088);
    ai_i8* _decoder_decoder_2_Relu_output_0_t_out_0_ptr_s8 = (ai_i8*)(net_ctx->_activations[0] + 15248);
    ai_i16* _decoder_decoder_2_Relu_output_0_t_scratch_0_ptr_s16 = (ai_i16*)(net_ctx->_activations[0] + 3408);
  
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(30, 1, {(stai_ptr) _decoder_decoder_2_Relu_output_0_t_in_0_ptr_const_s8});
    
  forward_lite_conv2d_deep_sssa8_ch(_decoder_decoder_2_Relu_output_0_t_in_0_ptr_const_s8, _decoder_decoder_2_Relu_output_0_t_in_0_shape_w_const_u16, _decoder_decoder_2_Relu_output_0_t_in_0_shape_h_const_u16, _decoder_decoder_2_Relu_output_0_t_in_0_shape_ch_const_u16, _decoder_decoder_2_Relu_output_0_t_weight_0_ptr_const_s8, _decoder_decoder_2_Relu_output_0_t_out_0_shape_ch_const_u16, _decoder_decoder_2_Relu_output_0_t_weight_0_shape_w_const_u16, _decoder_decoder_2_Relu_output_0_t_weight_0_shape_h_const_u16, _decoder_decoder_2_Relu_output_0_l_stride_1_const_u16, _decoder_decoder_2_Relu_output_0_l_stride_0_const_u16, _decoder_decoder_2_Relu_output_0_t_weight_1_ptr_const_s32, _decoder_decoder_2_Relu_output_0_t_in_0_fmt_zero_const_s8, _decoder_decoder_2_Relu_output_0_t_out_0_fmt_zero_const_s8, _decoder_decoder_2_Relu_output_0_t_in_0_fmt_scale_const_f32, _decoder_decoder_2_Relu_output_0_t_out_0_fmt_scale_const_f32, _decoder_decoder_2_Relu_output_0_t_weight_0_fmt_scale_const_f32, _decoder_decoder_2_Relu_output_0_l_out_ch_format_const_layer_format_type, _decoder_decoder_2_Relu_output_0_t_out_0_ptr_s8, _decoder_decoder_2_Relu_output_0_t_out_0_shape_w_const_u16, _decoder_decoder_2_Relu_output_0_t_out_0_shape_h_const_u16, 1, 1, 6336, _decoder_decoder_2_Relu_output_0_t_scratch_0_ptr_s16);
    
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(30, 1, {(stai_ptr) _decoder_decoder_2_Relu_output_0_t_out_0_ptr_s8});
  }
  /* LITE_KERNEL_SECTION END _decoder_decoder_2_Relu_output_0 */
  /* LITE_KERNEL_SECTION BEGIN _decoder_decoder_3_ConvTranspose_output_0_upsample */
  {
    
  forward_lite_upsample_zeros_is8os8__decoder_decoder_3_ConvTranspose_output_0_upsample(net_ctx);
  }
  /* LITE_KERNEL_SECTION END _decoder_decoder_3_ConvTranspose_output_0_upsample */
  /* LITE_KERNEL_SECTION BEGIN _decoder_decoder_3_ConvTranspose_output_0_pad_before */
  {
      const ai_ptr _decoder_decoder_3_ConvTranspose_output_0_pad_before_t_in_0_ptr_const_ptr = (ai_ptr)(net_ctx->_activations[0] + 6960);
    ai_ptr _decoder_decoder_3_ConvTranspose_output_0_pad_before_t_out_0_ptr_ptr = (ai_ptr)(net_ctx->_activations[0] + 6640);
  
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(33, 1, {(stai_ptr) _decoder_decoder_3_ConvTranspose_output_0_pad_before_t_in_0_ptr_const_ptr});
    
  forward_lite_pad_constant(_decoder_decoder_3_ConvTranspose_output_0_pad_before_t_in_0_ptr_const_ptr, _decoder_decoder_3_ConvTranspose_output_0_pad_before_t_out_0_ptr_ptr, (ai_handle)(_decoder_decoder_3_ConvTranspose_output_0_pad_before_v_pad_constant_value_const_s8), _decoder_decoder_3_ConvTranspose_output_0_pad_before_t_in_0_fmt_bitsize_const_s16, _decoder_decoder_3_ConvTranspose_output_0_pad_before_t_in_0_shape_h_const_u32, (ai_i32)(1), (ai_i32)(64), (ai_i32)(128), (ai_i32)(192), (ai_i32)(0), (ai_i32)(0));
    
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(33, 1, {(stai_ptr) _decoder_decoder_3_ConvTranspose_output_0_pad_before_t_out_0_ptr_ptr});
  }
  /* LITE_KERNEL_SECTION END _decoder_decoder_3_ConvTranspose_output_0_pad_before */
  /* LITE_KERNEL_SECTION BEGIN _decoder_decoder_3_ConvTranspose_output_0 */
  {
      const ai_i8* _decoder_decoder_3_ConvTranspose_output_0_t_in_0_ptr_const_s8 = (ai_i8*)(net_ctx->_activations[0] + 6640);
    const ai_i8* _decoder_decoder_3_ConvTranspose_output_0_t_weight_0_ptr_const_s8 = (ai_i8*)(net_ctx->_weights[0] + 16344);
    const ai_i32* _decoder_decoder_3_ConvTranspose_output_0_t_weight_1_ptr_const_s32 = (ai_i32*)(net_ctx->_weights[0] + 21784);
    ai_i8* _decoder_decoder_3_ConvTranspose_output_0_t_out_0_ptr_s8 = (ai_i8*)(net_ctx->_activations[0] + 14408);
    ai_i16* _decoder_decoder_3_ConvTranspose_output_0_t_scratch_0_ptr_s16 = (ai_i16*)(net_ctx->_activations[0] + 0);
  
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(33, 1, {(stai_ptr) _decoder_decoder_3_ConvTranspose_output_0_t_in_0_ptr_const_s8});
    
  forward_lite_conv2d_deep_sssa8_ch(_decoder_decoder_3_ConvTranspose_output_0_t_in_0_ptr_const_s8, _decoder_decoder_3_ConvTranspose_output_0_t_in_0_shape_w_const_u16, _decoder_decoder_3_ConvTranspose_output_0_t_in_0_shape_h_const_u16, _decoder_decoder_3_ConvTranspose_output_0_t_in_0_shape_ch_const_u16, _decoder_decoder_3_ConvTranspose_output_0_t_weight_0_ptr_const_s8, _decoder_decoder_3_ConvTranspose_output_0_t_out_0_shape_ch_const_u16, _decoder_decoder_3_ConvTranspose_output_0_t_weight_0_shape_w_const_u16, _decoder_decoder_3_ConvTranspose_output_0_t_weight_0_shape_h_const_u16, _decoder_decoder_3_ConvTranspose_output_0_l_stride_1_const_u16, _decoder_decoder_3_ConvTranspose_output_0_l_stride_0_const_u16, _decoder_decoder_3_ConvTranspose_output_0_t_weight_1_ptr_const_s32, _decoder_decoder_3_ConvTranspose_output_0_t_in_0_fmt_zero_const_s8, _decoder_decoder_3_ConvTranspose_output_0_t_out_0_fmt_zero_const_s8, _decoder_decoder_3_ConvTranspose_output_0_t_in_0_fmt_scale_const_f32, _decoder_decoder_3_ConvTranspose_output_0_t_out_0_fmt_scale_const_f32, _decoder_decoder_3_ConvTranspose_output_0_t_weight_0_fmt_scale_const_f32, _decoder_decoder_3_ConvTranspose_output_0_l_out_ch_format_const_layer_format_type, _decoder_decoder_3_ConvTranspose_output_0_t_out_0_ptr_s8, _decoder_decoder_3_ConvTranspose_output_0_t_out_0_shape_w_const_u16, _decoder_decoder_3_ConvTranspose_output_0_t_out_0_shape_h_const_u16, 1, 1, 6638, _decoder_decoder_3_ConvTranspose_output_0_t_scratch_0_ptr_s16);
    
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(33, 1, {(stai_ptr) _decoder_decoder_3_ConvTranspose_output_0_t_out_0_ptr_s8});
  }
  /* LITE_KERNEL_SECTION END _decoder_decoder_3_ConvTranspose_output_0 */
  /* LITE_KERNEL_SECTION BEGIN _Slice_2_output_0 */
  {
    
  forward_lite_slice__Slice_2_output_0(net_ctx);
  }
  /* LITE_KERNEL_SECTION END _Slice_2_output_0 */
  /* LITE_KERNEL_SECTION BEGIN _Transpose_1_output_0 */
  {
    
  forward_lite_transpose__Transpose_1_output_0(net_ctx);
  }
  /* LITE_KERNEL_SECTION END _Transpose_1_output_0 */
  /* LITE_KERNEL_SECTION BEGIN _Transpose_1_output_0_0_0__Sub_1_output_0_conversion */
  {
      const ai_i8* _Transpose_1_output_0_0_0__Sub_1_output_0_conversion_t_in_0_ptr_const_s8 = (ai_i8*)(net_ctx->_activations[0] + 836);
    ai_float* _Transpose_1_output_0_0_0__Sub_1_output_0_conversion_t_out_0_ptr_f32 = (ai_float*)(net_ctx->_activations[0] + 1672);
  
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(37, 1, {(stai_ptr) _Transpose_1_output_0_0_0__Sub_1_output_0_conversion_t_in_0_ptr_const_s8});
    
  forward_lite_node_convert_integer_is8of32(_Transpose_1_output_0_0_0__Sub_1_output_0_conversion_t_in_0_ptr_const_s8, _Transpose_1_output_0_0_0__Sub_1_output_0_conversion_t_out_0_ptr_f32, _Transpose_1_output_0_0_0__Sub_1_output_0_conversion_t_out_0_shape_h_w_ch_d_prod_const_u32, _Transpose_1_output_0_0_0__Sub_1_output_0_conversion_t_in_0_fmt_scale_const_f32, _Transpose_1_output_0_0_0__Sub_1_output_0_conversion_t_in_0_fmt_zero_const_s8);
    
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(37, 1, {(stai_ptr) _Transpose_1_output_0_0_0__Sub_1_output_0_conversion_t_out_0_ptr_f32});
  }
  /* LITE_KERNEL_SECTION END _Transpose_1_output_0_0_0__Sub_1_output_0_conversion */
  /* LITE_KERNEL_SECTION BEGIN _Sub_1_output_0 */
  {
    
  forward_lite_eltwise__Sub_1_output_0(net_ctx);
  }
  /* LITE_KERNEL_SECTION END _Sub_1_output_0 */
  /* LITE_KERNEL_SECTION BEGIN _Sub_1_output_0_0_0__Flatten_output_0_conversion */
  {
      const ai_float* _Sub_1_output_0_0_0__Flatten_output_0_conversion_t_in_0_ptr_const_f32 = (ai_float*)(net_ctx->_activations[0] + 5004);
    ai_i8* _Sub_1_output_0_0_0__Flatten_output_0_conversion_t_out_0_ptr_s8 = (ai_i8*)(net_ctx->_activations[0] + 0);
  
  _STAI_WINDOW_MODEL_EVENT_NODE_START_CB(38, 1, {(stai_ptr) _Sub_1_output_0_0_0__Flatten_output_0_conversion_t_in_0_ptr_const_f32});
    
  forward_lite_node_convert_integer_if32os8(_Sub_1_output_0_0_0__Flatten_output_0_conversion_t_in_0_ptr_const_f32, _Sub_1_output_0_0_0__Flatten_output_0_conversion_t_out_0_ptr_s8, _Sub_1_output_0_0_0__Flatten_output_0_conversion_t_out_0_shape_h_w_ch_d_prod_const_u32, _Sub_1_output_0_0_0__Flatten_output_0_conversion_t_out_0_fmt_scale_const_f32, _Sub_1_output_0_0_0__Flatten_output_0_conversion_t_out_0_fmt_zero_const_s8);
    
  _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB(38, 1, {(stai_ptr) _Sub_1_output_0_0_0__Flatten_output_0_conversion_t_out_0_ptr_s8});
  }
  /* LITE_KERNEL_SECTION END _Sub_1_output_0_0_0__Flatten_output_0_conversion */
  /* LITE_KERNEL_SECTION BEGIN _Flatten_output_0_to_chlast */
  {
    
  forward_lite_transpose__Flatten_output_0_to_chlast(net_ctx);
  }
  /* LITE_KERNEL_SECTION END _Flatten_output_0_to_chlast */
  /* LITE_KERNEL_SECTION BEGIN _Concat_output_0 */
  {
    
  forward_lite_concat__Concat_output_0(net_ctx);
  }
  /* LITE_KERNEL_SECTION END _Concat_output_0 */
  /* LITE_KERNEL_SECTION BEGIN out_QuantizeLinear_Input */
  {
    
  forward_lite_eltwise_integer_INT8_out_QuantizeLinear_Input(net_ctx);
  }
  /* LITE_KERNEL_SECTION END out_QuantizeLinear_Input */
  return net_ctx->_return_code;
}

/*****************************************************************************/
/*  Getters APIs Section  */
STAI_API_ENTRY
stai_size stai_window_model_get_context_size()
{
  return (stai_size)STAI_WINDOW_MODEL_CONTEXT_SIZE;
}

#if defined(HAVE_WINDOW_MODEL_INFO)
STAI_API_ENTRY
stai_return_code stai_window_model_get_info(
  stai_network* network,
  stai_network_info* info)
{
  _STAI_CONTEXT_ACQUIRE(net_ctx, network)
  _STAI_SET_ERROR(net_ctx, info==NULL, STAI_ERROR_NETWORK_INVALID_INFO, net_ctx->_return_code)

  // Copy of network info struct
  *info = g_window_model_info;

  return STAI_SUCCESS;
}
#endif


STAI_API_ENTRY
stai_return_code stai_window_model_get_activations(
  stai_network* network, stai_ptr* activations, stai_size* n_activations)
{
  _STAI_CONTEXT_ACQUIRE(net_ctx, network)

  _STAI_SET_ERROR(net_ctx, !n_activations, STAI_ERROR_NETWORK_INVALID_API_ARGUMENTS, net_ctx->_return_code)
  *n_activations = STAI_WINDOW_MODEL_ACTIVATIONS_NUM;
for (stai_size idx=0; activations && (idx<STAI_WINDOW_MODEL_ACTIVATIONS_NUM); idx++) {
    // get address of the activations buffers
    activations[idx] = net_ctx->_activations[idx];
  }return net_ctx->_return_code;
}


STAI_API_ENTRY
stai_return_code stai_window_model_get_weights(
  stai_network* network, stai_ptr* weights, stai_size* n_weights)
{
  _STAI_CONTEXT_ACQUIRE(net_ctx, network)
  _STAI_SET_ERROR(net_ctx, !n_weights, STAI_ERROR_NETWORK_INVALID_API_ARGUMENTS, net_ctx->_return_code)
  *n_weights = STAI_WINDOW_MODEL_WEIGHTS_NUM;
for (stai_size idx=0; weights && (idx<STAI_WINDOW_MODEL_WEIGHTS_NUM); idx++) {
    // get address of the weights buffers
    weights[idx] = net_ctx->_weights[idx];
  }return net_ctx->_return_code;
}


STAI_API_ENTRY
stai_return_code stai_window_model_get_inputs(
  stai_network* network, stai_ptr* inputs, stai_size* n_inputs)
{
  _STAI_CONTEXT_ACQUIRE(net_ctx, network)
  _STAI_SET_ERROR(net_ctx, !n_inputs, STAI_ERROR_NETWORK_INVALID_API_ARGUMENTS, net_ctx->_return_code)
  *n_inputs = STAI_WINDOW_MODEL_IN_NUM;
  for (stai_size idx=0; inputs && (idx<STAI_WINDOW_MODEL_IN_NUM); idx++) {
    inputs[idx] = net_ctx->_inputs[idx];
  }
  return net_ctx->_return_code;
}


STAI_API_ENTRY
stai_return_code stai_window_model_get_outputs(
  stai_network* network, stai_ptr* outputs, stai_size* n_outputs)
{
  _STAI_CONTEXT_ACQUIRE(net_ctx, network)
  _STAI_SET_ERROR(net_ctx, !n_outputs, STAI_ERROR_NETWORK_INVALID_API_ARGUMENTS, net_ctx->_return_code)
  *n_outputs = STAI_WINDOW_MODEL_OUT_NUM;
  for (stai_size idx=0; outputs && (idx<STAI_WINDOW_MODEL_OUT_NUM); idx++) {
    outputs[idx] = net_ctx->_outputs[idx];
  }
  return net_ctx->_return_code;
}


STAI_API_ENTRY
stai_return_code stai_window_model_get_error(
  stai_network* network)
{
  _STAI_CONTEXT_ACQUIRE(net_ctx, network)

  /* return 1st generated error or STAI_SUCCESS if no errors so far */
  return net_ctx->_return_code;
}


STAI_API_ENTRY
stai_return_code stai_window_model_get_states(
  stai_network* network, stai_ptr* states, stai_size* n_states)
{
  _STAI_CONTEXT_ACQUIRE(net_ctx, network)
  _STAI_SET_ERROR(net_ctx, !n_states, STAI_ERROR_NETWORK_INVALID_API_ARGUMENTS, net_ctx->_return_code)
  /* get the number of internals states (supporting multi-heap also for internal states) */
  *n_states = STAI_WINDOW_MODEL_STATES_NUM;

  STAI_UNUSED(states)
return net_ctx->_return_code;
}


/*****************************************************************************/
/*  Setters APIs Section  */

STAI_API_ENTRY
stai_return_code stai_window_model_set_activations(
  stai_network* network,
  const stai_ptr* activations,
  const stai_size n_activations)
{
  _STAI_CONTEXT_ACQUIRE(net_ctx, network)
const uintptr_t _activations_alignment[] = STAI_WINDOW_MODEL_ACTIVATIONS_ALIGNMENTS;
  STAI_PRINT("  [stai_window_model_set_activations] network(%p) activations[%d]: %p\n\n", net_ctx, n_activations, activations)
  _STAI_SET_ERROR(net_ctx, !activations,
                  STAI_ERROR_NETWORK_INVALID_API_ARGUMENTS, net_ctx->_return_code)
  _STAI_SET_ERROR(net_ctx, n_activations!=STAI_WINDOW_MODEL_ACTIVATIONS_NUM,
                  STAI_ERROR_NETWORK_INVALID_ACTIVATIONS_NUM, net_ctx->_return_code)

  for (stai_size idx=0; activations && idx<STAI_WINDOW_MODEL_ACTIVATIONS_NUM; idx++) {
    STAI_PRINT("  activation[%d]: %p\n", idx, activations[idx])
    _STAI_SET_ERROR(net_ctx, activations[idx]==NULL,
                    STAI_ERROR_NETWORK_INVALID_ACTIVATIONS_PTR, net_ctx->_return_code)
    _STAI_SET_ERROR(net_ctx, ((uintptr_t)activations[idx]) & (_activations_alignment[idx]-1),
                    STAI_ERROR_INVALID_BUFFER_ALIGNMENT, net_ctx->_return_code)
    net_ctx->_activations[idx] = activations[idx];
  }
  net_ctx->_inputs[0] = activations[0] + 10224;

  net_ctx->_outputs[0] = activations[0] + 0;
_stai_window_model_check(net_ctx);
  return net_ctx->_return_code;
}


STAI_API_ENTRY
stai_return_code stai_window_model_set_weights(
  stai_network* network,
  const stai_ptr* weights,
  const stai_size n_weights)
{
  _STAI_CONTEXT_ACQUIRE(net_ctx, network)
const uintptr_t _weights_alignment[] = STAI_WINDOW_MODEL_WEIGHTS_ALIGNMENTS;
  _STAI_SET_ERROR(net_ctx, !weights,
                  STAI_ERROR_NETWORK_INVALID_API_ARGUMENTS, net_ctx->_return_code)
  _STAI_SET_ERROR(net_ctx, n_weights!=STAI_WINDOW_MODEL_WEIGHTS_NUM,
                  STAI_ERROR_NETWORK_INVALID_WEIGHTS_NUM, net_ctx->_return_code)
  for (stai_size idx=0; weights && idx<STAI_WINDOW_MODEL_WEIGHTS_NUM; idx++) {
    STAI_PRINT("  weight[%d]: %p\n", idx, weights[idx])
    _STAI_SET_ERROR(net_ctx, weights[idx]==NULL,
                    STAI_ERROR_NETWORK_INVALID_WEIGHTS_PTR, net_ctx->_return_code)
    _STAI_SET_ERROR(net_ctx, ((uintptr_t)weights[idx]) & (_weights_alignment[idx]-1),
                    STAI_ERROR_INVALID_BUFFER_ALIGNMENT, net_ctx->_return_code)
    net_ctx->_weights[idx] = weights[idx];
  }_stai_window_model_check(net_ctx);
  return net_ctx->_return_code;
}


STAI_API_ENTRY
stai_return_code stai_window_model_set_inputs(
  stai_network* network,
  const stai_ptr* inputs,
  const stai_size n_inputs)
{
  const uintptr_t _inputs_alignment[] = STAI_WINDOW_MODEL_IN_ALIGNMENTS;
  _STAI_CONTEXT_ACQUIRE(net_ctx, network)
  _STAI_SET_ERROR(net_ctx, !inputs,
                  STAI_ERROR_NETWORK_INVALID_API_ARGUMENTS, net_ctx->_return_code)
  _STAI_SET_ERROR(net_ctx, n_inputs!=STAI_WINDOW_MODEL_IN_NUM,
                  STAI_ERROR_NETWORK_INVALID_IN_NUM, net_ctx->_return_code)

  for (stai_size idx=0; inputs && idx<STAI_WINDOW_MODEL_IN_NUM; idx++) {
    STAI_PRINT("  input[%d]: %p\n", idx, inputs[idx])
    _STAI_SET_ERROR(net_ctx, inputs[idx]==NULL,
                    STAI_ERROR_NETWORK_INVALID_IN_PTR, net_ctx->_return_code)
    _STAI_SET_ERROR(net_ctx, ((uintptr_t)inputs[idx]) & (_inputs_alignment[idx]-1),
                    STAI_ERROR_INVALID_BUFFER_ALIGNMENT, net_ctx->_return_code)
    net_ctx->_inputs[idx] = inputs[idx];
  }

  _stai_window_model_check(net_ctx);
  return net_ctx->_return_code;
}


STAI_API_ENTRY
stai_return_code stai_window_model_set_outputs(
  stai_network* network,
  const stai_ptr* outputs,
  const stai_size n_outputs)
{
  const uintptr_t _outputs_alignment[] = STAI_WINDOW_MODEL_OUT_ALIGNMENTS;
  _STAI_CONTEXT_ACQUIRE(net_ctx, network)
  _STAI_SET_ERROR(net_ctx, !outputs,
                  STAI_ERROR_NETWORK_INVALID_API_ARGUMENTS, net_ctx->_return_code)
  _STAI_SET_ERROR(net_ctx, n_outputs!=STAI_WINDOW_MODEL_OUT_NUM,
                  STAI_ERROR_NETWORK_INVALID_OUT_NUM, net_ctx->_return_code)

  for (stai_size idx=0; outputs && idx<n_outputs; idx++) {
    STAI_PRINT("  output[%d]: %p\n", idx, outputs[idx])
    _STAI_SET_ERROR(net_ctx, outputs[idx]==NULL,
                    STAI_ERROR_NETWORK_INVALID_OUT_PTR, net_ctx->_return_code)
    _STAI_SET_ERROR(net_ctx, ((uintptr_t)outputs[idx]) & (_outputs_alignment[idx]-1),
                    STAI_ERROR_INVALID_BUFFER_ALIGNMENT, net_ctx->_return_code)
    net_ctx->_outputs[idx] = outputs[idx];
  }

  _stai_window_model_check(net_ctx);
  return net_ctx->_return_code;
}


STAI_API_ENTRY
stai_return_code stai_window_model_set_states(
  stai_network* network,
  const stai_ptr* states,
  const stai_size n_states)
{
  _STAI_CONTEXT_ACQUIRE(net_ctx, network)

  STAI_UNUSED(states)
  STAI_UNUSED(n_states)
_stai_window_model_check(net_ctx);
  return net_ctx->_return_code;
}

STAI_API_ENTRY
stai_return_code stai_window_model_set_callback(
  stai_network* network, const stai_event_cb cb, void* cb_cookie)
{
  _STAI_CONTEXT_ACQUIRE(net_ctx, network)
  STAI_PRINT("  set_callback %p cb %p cookie %p\n", net_ctx, cb, cb_cookie)
  // _STAI_SET_ERROR(net_ctx, cb==NULL, STAI_ERROR_NETWORK_INVALID_CALLBACK, net_ctx->_return_code)
  net_ctx->_callback = cb;
  net_ctx->_callback_cookie = cb_cookie;
  return net_ctx->_return_code;
}

#undef _STAI_SET_ERROR
#undef _STAI_CONTEXT_ALIGNMENT
#undef _STAI_CONTEXT_ACQUIRE
#undef _STAI_WINDOW_MODEL_EVENT_NODE_START_CB
#undef _STAI_WINDOW_MODEL_EVENT_NODE_STOP_CB
#undef _STAI_WINDOW_MODEL_MODEL_SIGNATURE
#undef _STAI_WINDOW_MODEL_DATETIME
#undef _STAI_WINDOW_MODEL_COMPILE_DATETIME

