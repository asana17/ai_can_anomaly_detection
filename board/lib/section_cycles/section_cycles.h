#ifndef BOARD_SECTION_CYCLES_H
#define BOARD_SECTION_CYCLES_H

#include <tk/tkernel.h>

/*
 * The sections whose fewest and most DWT cycles are kept. Each is written from one
 * interrupt or task, or under one mutex, so no write cuts into another.
 */
typedef enum {
	SECTION_RECEIVE,                    /* one FDCAN receive callback */
	SECTION_TICK,                       /* the cyclic handler that wakes preprocess */
	SECTION_PREPROCESS,                 /* preprocess on one tick */
	SECTION_SCORE_AND_DETECT_BY_ROW,    /* score and detect by row on one row */
	SECTION_ROW_MODEL,                  /* the row model's inference in it */
	SECTION_SCORE_AND_DETECT_BY_WINDOW, /* score and detect by window on one row */
	SECTION_WINDOW_MODEL,               /* the window model's inference in it */
	SECTION_COPY_ALARM_FRAMES,          /* copying the frames of one alarm start */
	SECTION_STORE_ALARM_FRAMES,         /* the MAC and Flash write of one record */
	SECTION_CAN_SEND,                   /* one can_sender_send with its mutex held */
	SECTION_ALARM_LED,                  /* one step of the alarm LED */
	SECTION_COUNT
} Section;

typedef struct {
	UW fewest;
	UW most;
} SectionCycles;

/* Read with the programmer while the board runs. */
IMPORT SectionCycles section_cycles[SECTION_COUNT];

/**
 * @brief Set every section to no cycles seen.
 * @pre No section is written yet.
 */
IMPORT void section_cycles_clear(void);

/**
 * @brief The DWT cycle count to pass to section_cycles_end().
 * @pre model_init() has turned the DWT cycle counter on.
 */
IMPORT UW section_cycles_start(void);

/**
 * @brief Keep the cycles since @p started if they are the fewest or most of @p section.
 * @param[in] section The section that ends.
 * @param[in] started What section_cycles_start() returned when it began.
 */
IMPORT void section_cycles_end(Section section, UW started);

/**
 * @brief Keep @p cycles if they are the fewest or most of @p section.
 * @param[in] section The section measured.
 * @param[in] cycles The DWT cycles it took.
 */
IMPORT void section_cycles_add(Section section, UW cycles);

#endif
