#ifndef STORED_RECORD_INPUT_H
#define STORED_RECORD_INPUT_H

#include <tk/tkernel.h>

/* The alarm frames record the store has written to Flash. */
typedef struct {
	UW no;          /* the row alarm A started on */
	UW frame_count; /* the frames in it */
} StoredRecord;

/*
 * The latest record the store passes to the task that reports it, under a lock. A new
 * record goes over the one before, so writing never waits for report.
 */
typedef struct {
	ID mutex;                   /* locks stored_record */
	ID wake_reader_flag;        /* event flag that wakes the reader */
	StoredRecord stored_record; /* the latest record */
} StoredRecordInput;

/**
 * @brief Make the input, with no record in it.
 *
 * @param[out] stored_record_input The input.
 * @return E_OK, or the error T-Kernel gave while making its mutex or event flag.
 */
IMPORT ER stored_record_input_create(StoredRecordInput *stored_record_input);

/**
 * @brief Put a record over the one before, and wake the reader.
 *
 * @param[in,out] stored_record_input The input.
 * @param[in] stored_record The record.
 */
IMPORT void stored_record_input_write(StoredRecordInput *stored_record_input,
	CONST StoredRecord *stored_record);

/**
 * @brief Wait for a write, then copy the latest record.
 *
 * @param[in,out] stored_record_input The input.
 * @param[out] stored_record The latest record.
 */
IMPORT void stored_record_input_read(StoredRecordInput *stored_record_input,
	StoredRecord *stored_record);

#endif
