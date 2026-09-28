#ifndef ALARM_FRAMES_MAC_H
#define ALARM_FRAMES_MAC_H

#include <tk/tkernel.h>
#include "mbedtls/md.h"

#define ALARM_FRAMES_MAC_BYTES 32u /* HMAC-SHA256 */

/* HMAC-SHA256 with the key written in alarm_frames_mac.c. */
typedef struct {
	mbedtls_md_context_t md; /* the key is set once, at create */
} AlarmFramesMac;

/**
 * @brief Make the MAC and set its key.
 *
 * It makes the memory pool mbed-crypto takes its calloc from, so call it once.
 *
 * @param[out] mac The MAC.
 * @return E_OK, the error T-Kernel gave while making the pool, or E_SYS when
 *         mbed-crypto fails.
 */
IMPORT ER alarm_frames_mac_create(AlarmFramesMac *mac);

/**
 * @brief Give the HMAC-SHA256 of head then frames.
 *
 * @param[in,out] mac The MAC.
 * @param[in] head The first bytes.
 * @param[in] head_size Bytes in @p head.
 * @param[in] frames The bytes after head.
 * @param[in] frames_size Bytes in @p frames.
 * @param[out] out The MAC.
 * @return E_OK, or E_SYS when mbed-crypto fails.
 */
IMPORT ER alarm_frames_mac_compute(AlarmFramesMac *mac, CONST void *head, UW head_size,
	CONST void *frames, UW frames_size, UB out[ALARM_FRAMES_MAC_BYTES]);

#endif
