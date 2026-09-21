#ifndef MBF_H
#define MBF_H

#include <tk/tkernel.h>

/* Bytes one message uses in a message buffer. The kernel stores its length in an INT before it. */
#define MBF_SPACE(msgsize)	(sizeof(INT) + (msgsize))

IMPORT ER mbf_send_drop_oldest(ID mbfid, CONST void *msg, INT msgsize, void *old, INT *dropped);

#endif
