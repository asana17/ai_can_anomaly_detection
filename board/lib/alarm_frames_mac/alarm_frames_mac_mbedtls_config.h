#ifndef ALARM_FRAMES_MAC_MBEDTLS_CONFIG_H
#define ALARM_FRAMES_MAC_MBEDTLS_CONFIG_H

/* mbed-crypto as the MAC on the alarm frames uses it, HMAC-SHA256 and nothing else */
#define MBEDTLS_MD_C
#define MBEDTLS_SHA256_C
/* calloc and free come from a kernel memory pool, set at start */
#define MBEDTLS_PLATFORM_C
#define MBEDTLS_PLATFORM_MEMORY

#endif
