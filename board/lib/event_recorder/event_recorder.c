#include "event_recorder.h"
#include "mbf.h"
#include <string.h>

LOCAL ID event_mbf = 0;

/* In-memory storage for event records */
#define MAX_STORED_EVENTS 10
LOCAL EventRecord stored_events[MAX_STORED_EVENTS];
LOCAL uint32_t stored_count = 0;

LOCAL T_CMBF event_cmbf = {
	.mbfatr = TA_TPRI,  /* priority-order queue */
	.bufsz = EVENT_BUF_SIZE + EVENT_BUF_COUNT * sizeof(INT),
	.maxmsz = sizeof(EventRecord),
};

EXPORT ER event_recorder_init(void)
{
	event_mbf = tk_cre_mbf(&event_cmbf);
	if (event_mbf < E_OK) {
		return event_mbf;
	}
	return E_OK;
}

EXPORT ER event_recorder_send(const EventRecord *event)
{
	if (event_mbf <= 0) {
		return E_OBJ;
	}

	/* Non-blocking send. If buffer is full, drop the event. */
	return tk_snd_mbf(event_mbf, event, sizeof(EventRecord), TMO_POL);
}

EXPORT ER event_recorder_receive(EventRecord *event)
{
	if (event_mbf <= 0) {
		return E_OBJ;
	}

	/* Blocking receive. Wait forever for an event. */
	INT received = tk_rcv_mbf(event_mbf, event, TMO_FEVR);
	if (received == sizeof(EventRecord)) {
		return E_OK;
	}
	return (received < 0) ? received : E_SYS;
}

EXPORT void event_recorder_copy_rows(float *dest, const float (*history)[EVENT_SIGNALS],
                                     uint32_t history_size, uint32_t history_head,
                                     uint32_t count)
{
	uint32_t i, idx;

	if (count > history_size) {
		count = history_size;
	}

	/* Copy the last `count` rows from the ring buffer.
	 * If history_head is at position H and we want the last N rows,
	 * we copy from position (H - N) to (H - 1), wrapping around. */
	for (i = 0; i < count; i++) {
		/* Calculate source index: (head - count + i) mod size */
		if (history_head >= count - i) {
			idx = history_head - count + i;
		} else {
			idx = history_size + history_head - count + i;
		}

		memcpy(&dest[i * EVENT_SIGNALS], history[idx], EVENT_SIGNALS * sizeof(float));
	}
}

EXPORT ER event_recorder_store(const EventRecord *event)
{
	if (stored_count >= MAX_STORED_EVENTS) {
		return E_NOMEM;
	}

	memcpy(&stored_events[stored_count], event, sizeof(EventRecord));
	stored_count++;
	return E_OK;
}

EXPORT uint32_t event_recorder_get_count(void)
{
	return stored_count;
}

EXPORT const EventRecord* event_recorder_get_event_ptr(uint32_t index)
{
	if (index >= stored_count) {
		return NULL;
	}

	return &stored_events[index];
}
