#ifndef WINDOW_BACKLOG_CAN_TASK_H
#define WINDOW_BACKLOG_CAN_TASK_H

#include <tk/tkernel.h>
#include "stm32h5xx_hal.h"
#include "can_sender.h"
#include "window_backlog_input.h"

/* Where the window backlog report over CAN gets backlogs and sends them. */
typedef struct {
	WindowBacklogInput *window_backlog_input; /* where the backlogs come from */
	CanSender *sender;                        /* what sends the backlog frames */
	UW id;                                    /* the ID the backlog frames go out with */
	ID task_id;
} WindowBacklogCanTask;

/*
 * Create the window backlog report over CAN at priority, taking backlogs from
 * window_backlog_input and sending them on sender with id.
 */
IMPORT ER window_backlog_can_task_create(WindowBacklogCanTask *task, PRI priority,
	WindowBacklogInput *window_backlog_input, CanSender *sender, UW id);

/* Start the window backlog report over CAN. */
IMPORT ER window_backlog_can_task_start(WindowBacklogCanTask *task);

#endif
