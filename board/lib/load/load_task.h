#ifndef LOAD_TASK_H
#define LOAD_TASK_H

#include <tk/tkernel.h>

/* A synthetic load that stands in for the work an ECU has besides detection. */
typedef struct {
	UW units;  /* work units done on each wake */
	ID task_id;
	ID tick_id;
} LoadTask;

/**
 * @brief Do units of work, a CRC-32 over a small buffer each.
 *
 * The work is set by the units, not by time, so a task that is interrupted still does
 * the same work.
 *
 * @param[in] units Work units.
 */
IMPORT void load_work(UW units);

/**
 * @brief Create the load at priority and the tick that wakes it every period ms.
 *
 * On each wake it does units of work. A wake that comes while it works makes it run
 * again at once.
 *
 * @param[out] task The load.
 * @param[in] priority Its priority.
 * @param[in] period ms between wakes.
 * @param[in] units Work units on each wake.
 * @return E_OK, or the error T-Kernel gave while making the task or the tick.
 */
IMPORT ER load_task_create(LoadTask *task, PRI priority, RELTIM period, UW units);

/* Start the load and its tick. */
IMPORT ER load_task_start(LoadTask *task);

#endif
