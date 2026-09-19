#include "mbf.h"

/*
 * Sends msg without waiting, removing the oldest message while the buffer is full.
 * old holds one removed message. Each calling task passes its own.
 * dropped gets how many were removed. Returns E_OK or an error.
 */
EXPORT ER mbf_send_drop_oldest(ID mbfid, CONST void *msg, INT msgsize, void *old, INT *dropped)
{
	ER	er;
	INT	size;

	*dropped = 0;

	for(;;) {			/* another sender can take the freed room */
		er = tk_snd_mbf(mbfid, msg, msgsize, TMO_POL);
		if(er != E_TMOUT) {	/* sent, or an error other than full */
			return er;
		}
		size = tk_rcv_mbf(mbfid, old, TMO_POL);	/* full: receive the oldest and discard it to make room */
		if(size > 0) {
			(*dropped)++;
		} else if(size != E_TMOUT) {	/* E_TMOUT: a receiver emptied it, send again */
			return size;
		}
	}
}
