#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "stm32h5xx_hal.h"
#include "slots.h"
#include "frame_ring.h"
#include "report_input.h"
#include "flash_store.h"
#include "store_alarm_frames_input.h"
#include "store_alarm_frames_task.h"
#include "stored_record_input.h"
#include "can_sender.h"
#include "report_can_task.h"
#include "stored_record_can_task.h"
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
LOCAL ReportInput window_report_input;
LOCAL StoredRecordInput stored_record_input;
LOCAL StoreAlarmFramesInput store_alarm_frames_input;
LOCAL FlashStoreState flash_store;
LOCAL StoreAlarmFramesTask store_alarm_frames_task;
LOCAL CanSender can_sender;
LOCAL ReportCanTask report_can_task;
LOCAL ReportCanTask window_report_can_task;
LOCAL StoredRecordCanTask stored_record_can_task;

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
	error = report_input_create(&window_report_input);
	if (error < E_OK) {
		return error;
	}
	error = stored_record_input_create(&stored_record_input);
	if (error < E_OK) {
		return error;
	}
	error = store_alarm_frames_input_create(&store_alarm_frames_input);
	if (error < E_OK) {
		return error;
	}
	error = flash_store_init(&flash_store);
	if (error < E_OK) {
		tm_printf((UB*)"flash store init error %d\n", error);
		return error;
	}
	/* above score and detect by window at 12, so the window model never holds back Flash */
	error = store_alarm_frames_task_create(&store_alarm_frames_task, 11,
		&store_alarm_frames_input, &flash_store, &stored_record_input);
	if (error < E_OK) {
		return error;
	}
	error = ai_can_anomaly_detection_tasks_create(&slots, &frame_ring, &report_input,
		&window_report_input, &store_alarm_frames_input);
	if (error < E_OK) {
		return error;
	}
	error = can_sender_create(&can_sender, &hfdcan1);
	if (error < E_OK) {
		return error;
	}
	/* between score and detect by row at 8 and the copy of the alarm frames at 10 */
	error = report_can_task_create(&report_can_task, 9, &report_input, &can_sender,
		ALARM_ID);
	if (error < E_OK) {
		return error;
	}
	/* above score and detect by window at 12, and below the alarm's report */
	error = report_can_task_create(&window_report_can_task, 10, &window_report_input,
		&can_sender, WINDOW_ALARM_ID);
	if (error < E_OK) {
		return error;
	}
	/* above the store at 11, so a record goes out as soon as it is written */
	error = stored_record_can_task_create(&stored_record_can_task, 10, &stored_record_input,
		&can_sender, STORED_RECORD_ID);
	if (error < E_OK) {
		return error;
	}
	/* sends only on an alarm, which needs frames, so it may start before FDCAN1 */
	error = report_can_task_start(&report_can_task);
	if (error < E_OK) {
		return error;
	}
	error = report_can_task_start(&window_report_can_task);
	if (error < E_OK) {
		return error;
	}
	error = stored_record_can_task_start(&stored_record_can_task);
	if (error < E_OK) {
		return error;
	}
	error = store_alarm_frames_task_start(&store_alarm_frames_task);
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
