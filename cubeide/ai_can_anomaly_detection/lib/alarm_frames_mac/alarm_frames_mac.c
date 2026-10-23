#include <string.h>
#include <tk/tkernel.h>
#include "mbedtls/platform.h"
#include "alarm_frames_mac.h"
#include "alarm_frames_mac_demo_key.h"

/* room for the SHA-256 context and the HMAC pads mbedtls_md_setup takes */
#define MAC_POOL_BYTES 512

LOCAL ID mac_pool; /* where mbed-crypto's calloc takes memory from */

LOCAL void *mac_pool_calloc(size_t count, size_t size)
{
	void *block;

	if (tk_get_mpl(mac_pool, (SZ)(count * size), &block, TMO_POL) < E_OK) {
		return NULL;
	}
	memset(block, 0, count * size);
	return block;
}

LOCAL void mac_pool_free(void *block)
{
	if (block != NULL) {
		tk_rel_mpl(mac_pool, block);
	}
}

EXPORT ER alarm_frames_mac_create(AlarmFramesMac *mac)
{
	T_CMPL cmpl = {
		.mplatr = TA_TFIFO, .mplsz = MAC_POOL_BYTES,
	};

	mac_pool = tk_cre_mpl(&cmpl);
	if (mac_pool < E_OK) {
		return mac_pool;
	}
	mbedtls_platform_set_calloc_free(mac_pool_calloc, mac_pool_free);
	mbedtls_md_init(&mac->md);
	if (mbedtls_md_setup(&mac->md, mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), 1) != 0) {
		return E_SYS;
	}
	if (mbedtls_md_hmac_starts(&mac->md, alarm_frames_mac_demo_key,
		sizeof(alarm_frames_mac_demo_key)) != 0) {
		return E_SYS;
	}
	return E_OK;
}

EXPORT ER alarm_frames_mac_compute(AlarmFramesMac *mac, CONST void *head, UW head_size,
	CONST void *frames, UW frames_size, UB out[ALARM_FRAMES_MAC_BYTES])
{
	if (mbedtls_md_hmac_reset(&mac->md) != 0 ||
		mbedtls_md_hmac_update(&mac->md, head, head_size) != 0 ||
		mbedtls_md_hmac_update(&mac->md, frames, frames_size) != 0 ||
		mbedtls_md_hmac_finish(&mac->md, out) != 0) {
		return E_SYS;
	}
	return E_OK;
}
