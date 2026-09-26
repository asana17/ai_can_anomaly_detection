#ifndef EVENT_RECORDER_H
#define EVENT_RECORDER_H

#include <stdint.h>
#include <tk/tkernel.h>

#define EVENT_WINDOW_ROWS  50
#define EVENT_SIGNALS      17  /* MODEL_SIGNALS */
#define EVENT_DATA_SIZE    (EVENT_WINDOW_ROWS * EVENT_SIGNALS * sizeof(float))

/* 2-3 events can be queued */
#define EVENT_BUF_COUNT    3
#define EVENT_BUF_SIZE     (EVENT_DATA_SIZE * EVENT_BUF_COUNT)

typedef struct {
	uint32_t row_number;  /* row number when the alarm was raised */
	float data[EVENT_WINDOW_ROWS * EVENT_SIGNALS];
} EventRecord;

/**
 * @brief Initialize event recorder message buffer.
 *
 * @retval E_OK Success
 * @return T-Kernel error code
 */
IMPORT ER event_recorder_init(void);

/**
 * @brief Send event to flash writer task (non-blocking).
 *
 * Called by alarm detection task when alarm is raised.
 * If the buffer is full, the event is dropped without blocking.
 *
 * @param[in] event Event record to send
 * @retval E_OK Event queued
 * @retval E_TMOUT Buffer full, event dropped
 * @return T-Kernel error code
 */
IMPORT ER event_recorder_send(const EventRecord *event);

/**
 * @brief Receive event from message buffer (blocking).
 *
 * Called by flash writer task. Blocks until an event is available.
 *
 * @param[out] event Received event record
 * @retval E_OK Event received
 * @return T-Kernel error code
 */
IMPORT ER event_recorder_receive(EventRecord *event);

/**
 * @brief Copy the last N rows from the signal history.
 *
 * Called by alarm detection task to prepare the event record.
 * This function copies rows from the ring buffer maintained by
 * the preprocess task.
 *
 * @param[out] dest Destination buffer (EVENT_WINDOW_ROWS * EVENT_SIGNALS floats)
 * @param[in] history Ring buffer of rows
 * @param[in] history_size Number of rows in history ring
 * @param[in] history_head Current head position in ring
 * @param[in] count Number of rows to copy (typically EVENT_WINDOW_ROWS)
 */
IMPORT void event_recorder_copy_rows(float *dest, const float (*history)[EVENT_SIGNALS],
                                     uint32_t history_size, uint32_t history_head,
                                     uint32_t count);

/**
 * @brief Store event record (called by flash writer task).
 *
 * @param[in] event Event record to store
 * @retval E_OK Success
 * @retval E_NOMEM Storage full
 */
IMPORT ER event_recorder_store(const EventRecord *event);

/**
 * @brief Get number of stored events.
 *
 * @return Number of stored events
 */
IMPORT uint32_t event_recorder_get_count(void);

/**
 * @brief Get pointer to stored event (read-only).
 *
 * Returns a direct pointer to the stored event, avoiding stack allocation.
 *
 * @param[in] index Event index (0 to count-1)
 * @return Pointer to event, or NULL if index is invalid
 */
IMPORT const EventRecord* event_recorder_get_event_ptr(uint32_t index);

#endif
