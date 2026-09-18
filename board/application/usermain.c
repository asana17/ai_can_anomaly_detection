#include <tk/tkernel.h>
#include <tm/tmonitor.h>
#include "stm32h5xx_nucleo.h"

LOCAL void alive_task(INT stacd, void *exinf);
LOCAL ID	alive_tskid;
LOCAL T_CTSK alive_ctsk = {
	.itskpri	= 10,
	.stksz		= 1024,
	.task		= alive_task,
	.tskatr		= TA_HLNG | TA_RNG3,
};

/* Blinks the green LED and counts on the ST-LINK virtual COM port, every 500 ms */
LOCAL void alive_task(INT stacd, void *exinf)
{
	INT	count = 0;

	while(1) {
		BSP_LED_Toggle(LED_GREEN);
		tm_printf((UB*)"usermain %d\n", ++count);
		tk_dly_tsk(500);
	}
}

EXPORT INT usermain(void)
{
	alive_tskid = tk_cre_tsk(&alive_ctsk);
	tk_sta_tsk(alive_tskid, 0);

	tk_slp_tsk(TMO_FEVR);

	return 0;
}
