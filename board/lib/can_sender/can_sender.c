#include <tk/tkernel.h>
#include "stm32h5xx_hal.h"
#include "can_sender.h"

/* The number of the transmit buffer whose bit HAL gives, FDCAN_TX_BUFFER0 as 0. */
LOCAL UW buffer_number_from_bit(UW bit)
{
	UW number = 0;

	while (bit > 1u) {
		bit >>= 1;
		number++;
	}
	return number;
}

EXPORT ER can_sender_create(CanSender *sender, FDCAN_HandleTypeDef *can)
{
	T_CMTX cmtx = {
		.mtxatr = TA_INHERIT,
	};
	UW buffer;

	sender->can = can;
	for (buffer = 0; buffer < CAN_SENDER_TX_BUFFERS; buffer++) {
		sender->buffer_ids[buffer] = 0;
	}
	sender->mutex = tk_cre_mtx(&cmtx);
	if (sender->mutex < E_OK) {
		return sender->mutex;
	}
	return E_OK;
}

/*
 * The mutex is held from reading buffer_ids to updating it, so no other task puts a
 * frame in between.
 */
EXPORT void can_sender_send(CanSender *sender,
	CONST FDCAN_TxHeaderTypeDef *header, CONST UB *data)
{
	UW buffer, bit;

	tk_loc_mtx(sender->mutex, TMO_FEVR);
	for (buffer = 0; buffer < CAN_SENDER_TX_BUFFERS; buffer++) {
		bit = 1u << buffer;
		if (sender->buffer_ids[buffer] == header->Identifier
			&& HAL_FDCAN_IsTxBufferMessagePending(sender->can, bit)) {
			HAL_FDCAN_AbortTxRequest(sender->can, bit);
		}
	}
	if (HAL_FDCAN_AddMessageToTxFifoQ(sender->can, header, data) == HAL_OK) {
		bit = HAL_FDCAN_GetLatestTxFifoQRequestBuffer(sender->can);
		sender->buffer_ids[buffer_number_from_bit(bit)] = header->Identifier;
	}
	tk_unl_mtx(sender->mutex);
}
