#ifndef MBF_H
#define MBF_H

#include <tk/tkernel.h>

/**
 * @brief Return the message-buffer storage consumed by one message.
 *
 * The T-Kernel message buffer stores an INT-sized length immediately before each
 * message payload. Use this macro when calculating T_CMBF::bufsz.
 *
 * @param payload_size Maximum payload size in bytes.
 */
#define MBF_MESSAGE_STORAGE_SIZE(payload_size) \
	(sizeof(INT) + (payload_size))

/**
 * @brief Send without waiting, discarding oldest messages while the buffer is full.
 *
 * The function retries when another task consumes the message between the failed
 * send and receive. Each caller therefore supplies its own discard buffer.
 *
 * @param[in] mbfid Message-buffer ID.
 * @param[in] msg Message payload to send.
 * @param[in] msgsize Payload size in bytes.
 * @param[out] old Buffer large enough for one maximum-size message; receives each
 *                 discarded message in turn.
 * @param[out] dropped Number of messages discarded before the send completed.
 * @retval E_OK The message was sent.
 * @return A T-Kernel error returned by tk_snd_mbf() or tk_rcv_mbf().
 * @pre msg, old and dropped are non-NULL, and old does not alias msg.
 */
IMPORT ER mbf_send_drop_oldest(ID mbfid, CONST void *msg, INT msgsize, void *old, INT *dropped);

#endif
