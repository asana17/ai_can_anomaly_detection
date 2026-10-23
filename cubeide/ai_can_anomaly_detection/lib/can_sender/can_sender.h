#ifndef CAN_SENDER_H
#define CAN_SENDER_H

#include <tk/tkernel.h>
#include "stm32h5xx_hal.h"

#define CAN_SENDER_TX_BUFFERS 3u /* the elements of the transmit FIFO */

/* Sends frames on one FDCAN for every report over CAN on it, one at a time. */
typedef struct {
	FDCAN_HandleTypeDef *can; /* the FDCAN, started by the caller */
	ID mutex;                 /* held while a frame is put in the transmit FIFO */
	UW buffer_ids[CAN_SENDER_TX_BUFFERS]; /* the ID of the frame put in each buffer last */
} CanSender;

/**
 * @brief Make the sender of can, with no frame put in yet.
 *
 * @param[out] sender The sender.
 * @param[in] can The FDCAN.
 * @return E_OK, or the error T-Kernel gave while making its mutex.
 */
IMPORT ER can_sender_create(CanSender *sender, FDCAN_HandleTypeDef *can);

/**
 * @brief Put a frame in the transmit FIFO, over the last frame with its ID.
 *
 * A frame with the same ID that has not gone out yet holds an older state. It is
 * cancelled first. Frames with other IDs are left alone. If the FIFO is full, this
 * frame is dropped.
 *
 * @param[in,out] sender The sender.
 * @param[in] header The frame's header.
 * @param[in] data The frame's data.
 */
IMPORT void can_sender_send(CanSender *sender,
	CONST FDCAN_TxHeaderTypeDef *header, CONST UB *data);

#endif
