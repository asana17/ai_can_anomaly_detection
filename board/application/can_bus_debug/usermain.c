#include <string.h>
#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "stm32h5xx_hal.h"

#define CAN_BYTES 8u /* a classic CAN frame's payload, which DLC 9 to 15 also mean */
#define CAN_DEBUG_ID 0x18FEF100u /* a J1939 29-bit PGN used by the debug TX task */

IMPORT FDCAN_HandleTypeDef hfdcan1; /* set up by MX_FDCAN1_Init in the CubeMX main.c */

LOCAL ID can_debug_id;

/* A lock-free ring the RX interrupt fills and the debug task drains to print.
 * Single writer (ISR) / single reader (task), so head and tail need no lock. */
#define CAN_DEBUG_LOG_DEPTH 16u /* power of two; masks the head/tail */
typedef struct {
	UW id;
	UW len;
	INT ext; /* true: 29-bit extended ID; false: 11-bit standard ID */
	uint8_t data[CAN_BYTES];
} CanDebugFrame;
LOCAL CanDebugFrame can_debug_log[CAN_DEBUG_LOG_DEPTH];
LOCAL volatile UW can_debug_head, can_debug_tail; /* head: ISR writes, tail: task reads */
LOCAL volatile UW can_debug_dropped; /* frames the ring could not hold */

/* Copy every frame into the debug ring for the debug task to print,
 * regardless of ID type, so standard-ID frames are visible too. */
EXPORT void HAL_FDCAN_RxFifo0Callback(FDCAN_HandleTypeDef *hfdcan, uint32_t RxFifo0ITs)
{
	FDCAN_RxHeaderTypeDef header;
	uint8_t data[CAN_BYTES];
	uint32_t size;

	while (HAL_FDCAN_GetRxMessage(hfdcan, FDCAN_RX_FIFO0, &header, data) == HAL_OK) {
		size = header.DataLength;
		if (size > CAN_BYTES) {
			size = CAN_BYTES;
		}
		if (can_debug_head - can_debug_tail < CAN_DEBUG_LOG_DEPTH) {
			CanDebugFrame *slot = &can_debug_log[can_debug_head & (CAN_DEBUG_LOG_DEPTH - 1)];
			slot->id = header.Identifier;
			slot->ext = 0;
			if (header.IdType == FDCAN_EXTENDED_ID) {
				slot->ext = 1;
			}
			slot->len = size;
			memcpy(slot->data, data, size);
			can_debug_head++; /* publish only after the slot is filled */
		} else {
			can_debug_dropped++;
		}
	}
}

/* Accept every frame into RX FIFO 0, interrupt on each, and start the bus. */
LOCAL INT can_start(void)
{
	if (HAL_FDCAN_ConfigGlobalFilter(&hfdcan1, FDCAN_ACCEPT_IN_RX_FIFO0,
		FDCAN_ACCEPT_IN_RX_FIFO0, FDCAN_REJECT_REMOTE, FDCAN_REJECT_REMOTE) != HAL_OK) {
		return -1;
	}
	if (HAL_FDCAN_ActivateNotification(&hfdcan1, FDCAN_IT_RX_FIFO0_NEW_MESSAGE, 0)
		!= HAL_OK) {
		return -2;
	}
	if (HAL_FDCAN_Start(&hfdcan1) != HAL_OK) {
		return -3;
	}
	return 0;
}

/* Queue one classic-CAN frame on FDCAN1. Mirrors samples' can_try_send. */
LOCAL INT can_send(uint32_t id, const uint8_t *data, uint32_t len)
{
	FDCAN_TxHeaderTypeDef header = {
		.Identifier          = id,
		.IdType              = FDCAN_EXTENDED_ID,   /* J1939: 29-bit */
		.TxFrameType         = FDCAN_DATA_FRAME,
		.DataLength          = len,                 /* DLC code; 0..8 == byte count */
		.ErrorStateIndicator = FDCAN_ESI_ACTIVE,
		.BitRateSwitch       = FDCAN_BRS_OFF,       /* classic CAN */
		.FDFormat            = FDCAN_CLASSIC_CAN,
		.TxEventFifoControl  = FDCAN_NO_TX_EVENTS,
		.MessageMarker       = 0,
	};

	if (HAL_FDCAN_AddMessageToTxFifoQ(&hfdcan1, &header, (uint8_t *)data) != HAL_OK) {
		return -1;   /* TX FIFO full or not started */
	}
	return 0;
}

/* Send a frame every second and print whatever the bus received.
 * Modelled on app_main.c's task_can in mtk3bsp2_samples. */
LOCAL void can_debug_task(INT stacd, void *exinf)
{
	uint8_t tx[CAN_BYTES] = { 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88 };

	while (1) {
		/* Drain and print every frame the RX interrupt logged. */
		while (can_debug_tail != can_debug_head) {
			CanDebugFrame *slot = &can_debug_log[can_debug_tail & (CAN_DEBUG_LOG_DEPTH - 1)];
			UB *kind = (UB*)"std";
			UW i;
			if (slot->ext) {
				kind = (UB*)"ext";
			}
			tm_printf((UB*)"CAN RX: ID=0x%08x (%s) DLC=%u data=", slot->id, kind, slot->len);
			for (i = 0; i < slot->len; i++) {
				tm_printf((UB*)"%02x ", slot->data[i]);
			}
			tm_printf((UB*)"\n");
			can_debug_tail++;
		}
		if (can_debug_dropped) {
			tm_printf((UB*)"CAN RX debug log dropped %u frames\n", can_debug_dropped);
			can_debug_dropped = 0;
		}

		/* Send one test frame, varying the payload so successive frames differ. */
		tx[0]++;
		if (can_send(CAN_DEBUG_ID, tx, sizeof(tx)) == 0) {
			tm_printf((UB*)"CAN TX: ID=0x%08x queued\n", CAN_DEBUG_ID);
		} else {
			tm_printf((UB*)"CAN TX: ID=0x%08x send failed\n", CAN_DEBUG_ID);
		}

		tk_dly_tsk(1000);
	}
}

LOCAL T_CTSK can_debug_ctsk = {
	.itskpri = 11, .stksz = 1024, .task = can_debug_task,
	.tskatr = TA_HLNG | TA_RNG3,
};

EXPORT INT usermain(void)
{
	can_debug_id = tk_cre_tsk(&can_debug_ctsk);
	if (can_debug_id < E_OK) {
		return -11;
	}
	if (can_start() != 0) {
		tm_printf((UB*)"FDCAN start error\n");
		return -13;
	}
	tk_sta_tsk(can_debug_id, 0); /* after the bus is running, so TX can queue */
	tk_slp_tsk(TMO_FEVR);
	return 0;
}
