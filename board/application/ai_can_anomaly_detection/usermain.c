#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "stm32h5xx_hal.h"
#include "slots.h"
#include "frame_ring.h"
#include "report_input.h"
#include "report_can_task.h"
#include "ai_can_anomaly_detection_tasks.h"

#define CAN_BYTES 8u /* a classic CAN frame's payload, which DLC 9 to 15 also mean */

IMPORT FDCAN_HandleTypeDef hfdcan1; /* set up by MX_FDCAN1_Init in the CubeMX main.c */

/* What the CAN receive side writes with slots_store(). */
EXPORT Slots slots;

/* The frames the receive interrupt copies for the cut. */
LOCAL FrameRing frame_ring;

/* The fewest and most cycles one receive callback took, read with the programmer. */
EXPORT UW fewest_receive_cycles = 0xFFFFFFFFu;
EXPORT UW most_receive_cycles = 0;

LOCAL ReportInput report_input;
LOCAL ReportCanTask report_can_task;

/*
 * Store each frame FDCAN received as the latest of its PGN, and copy it into the frame
 * ring. One callback takes every frame waiting in RX FIFO 0.
 */
EXPORT void HAL_FDCAN_RxFifo0Callback(FDCAN_HandleTypeDef *hfdcan, uint32_t RxFifo0ITs)
{
	FDCAN_RxHeaderTypeDef header;
	uint8_t data[CAN_BYTES];
	uint32_t size, time, started, cycles;

	started = DWT->CYCCNT;
	while (HAL_FDCAN_GetRxMessage(hfdcan, FDCAN_RX_FIFO0, &header, data) == HAL_OK) {
		if (header.IdType != FDCAN_EXTENDED_ID) {
			continue; /* J1939 uses 29-bit IDs only */
		}
		size = header.DataLength;
		if (size > CAN_BYTES) {
			size = CAN_BYTES;
		}
		/* DWT counts cycles once model_init has run, which is before reception starts */
		time = DWT->CYCCNT;
		slots_store(&slots, header.Identifier, data, size, time);
		frame_ring_push(&frame_ring, header.Identifier, data, size, time);
	}
	cycles = DWT->CYCCNT - started;
	if (cycles < fewest_receive_cycles) {
		fewest_receive_cycles = cycles;
	}
	if (cycles > most_receive_cycles) {
		most_receive_cycles = cycles;
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

EXPORT INT usermain(void)
{
	INT error;

	tm_printf((UB*)"reading FDCAN1\n");
	frame_ring_clear(&frame_ring, SystemCoreClock / 1000000u);
	error = report_input_create(&report_input);
	if (error < E_OK) {
		return error;
	}
	error = ai_can_anomaly_detection_tasks_create(&slots, &report_input);
	if (error < E_OK) {
		return error;
	}
	/* between score and detect by row at 8 and the windowed model at 11 */
	error = report_can_task_create(&report_can_task, 9, &report_input, &hfdcan1);
	if (error < E_OK) {
		return error;
	}
	/* sends only on an alarm, which needs frames, so it may start before FDCAN1 */
	error = report_can_task_start(&report_can_task);
	if (error < E_OK) {
		return error;
	}
	error = ai_can_anomaly_detection_tasks_start();
	if (error < E_OK) {
		return error;
	}
	if (can_start() != 0) {
		tm_printf((UB*)"FDCAN start error\n");
		return -13;
	}
	tk_slp_tsk(TMO_FEVR);
	return 0;
}
