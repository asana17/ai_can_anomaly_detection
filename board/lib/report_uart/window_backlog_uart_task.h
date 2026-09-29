#ifndef WINDOW_BACKLOG_UART_TASK_H
#define WINDOW_BACKLOG_UART_TASK_H

#include <tk/tkernel.h>
#include "window_backlog_input.h"

/* Where the window backlog report over UART gets backlogs. */
typedef struct {
	WindowBacklogInput *window_backlog_input; /* where the backlogs come from */
	UW id;                                    /* the ID each line names the backlog by */
	ID task_id;
} WindowBacklogUartTask;

/*
 * Create the window backlog report over UART at priority, taking backlogs from
 * window_backlog_input and printing them with id.
 */
IMPORT ER window_backlog_uart_task_create(WindowBacklogUartTask *task, PRI priority,
	WindowBacklogInput *window_backlog_input, UW id);

/* Start the window backlog report over UART. */
IMPORT ER window_backlog_uart_task_start(WindowBacklogUartTask *task);

#endif
