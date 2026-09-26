#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "stm32h5xx_hal.h"
#include "slots.h"
#include "ai_can_anomaly_detection_tasks.h"

#define CAN_BYTES 8u /* a classic CAN frame's payload, which DLC 9 to 15 also mean */

IMPORT FDCAN_HandleTypeDef hfdcan1; /* set up by MX_FDCAN1_Init in the CubeMX main.c */

/* What the CAN receive side writes with slots_store(). */
EXPORT Slots slots;

/* Store each frame FDCAN received as the latest of its PGN. */
EXPORT void HAL_FDCAN_RxFifo0Callback(FDCAN_HandleTypeDef *hfdcan, uint32_t RxFifo0ITs)
{
	FDCAN_RxHeaderTypeDef header;
	uint8_t data[CAN_BYTES];
	uint32_t size;

	while(HAL_FDCAN_GetRxMessage(hfdcan, FDCAN_RX_FIFO0, &header, data) == HAL_OK) {
		if(header.IdType != FDCAN_EXTENDED_ID) {
			continue; /* J1939 uses 29-bit IDs only */
		}
		size = header.DataLength;
		if(size > CAN_BYTES) {
			size = CAN_BYTES;
		}
		/* DWT counts cycles once model_init has run, which is before reception starts */
		slots_store(&slots, header.Identifier, data, size, DWT->CYCCNT);
	}
}

/* Accept every frame into RX FIFO 0, interrupt on each, and start the bus. */
LOCAL INT can_start(void)
{
	if(HAL_FDCAN_ConfigGlobalFilter(&hfdcan1, FDCAN_ACCEPT_IN_RX_FIFO0,
		FDCAN_ACCEPT_IN_RX_FIFO0, FDCAN_REJECT_REMOTE, FDCAN_REJECT_REMOTE) != HAL_OK) {
		return -1;
	}
	if(HAL_FDCAN_ActivateNotification(&hfdcan1, FDCAN_IT_RX_FIFO0_NEW_MESSAGE, 0)
		!= HAL_OK) {
		return -2;
	}
	if(HAL_FDCAN_Start(&hfdcan1) != HAL_OK) {
		return -3;
	}
	return 0;
}

EXPORT INT usermain(void)
{
	INT error;

	tm_printf((UB*)"reading FDCAN1\n");
	error = ai_can_anomaly_detection_tasks_create(&slots);
	if(error < E_OK) {
		return error;
	}
	error = ai_can_anomaly_detection_tasks_start();
	if(error < E_OK) {
		return error;
	}
	if(can_start() != 0) {
		tm_printf((UB*)"FDCAN start error\n");
		return -13;
	}
	tk_slp_tsk(TMO_FEVR);
	return 0;
}
