#include <tk/tkernel.h>
#include "unity.h"
#include "mbf.h"

#define DEPTH	4
#define SENT	10

LOCAL T_CMBF cmbf = {
	.mbfatr		= TA_TFIFO,
	.bufsz		= DEPTH * MBF_SPACE(sizeof(UW)),
	.maxmsz		= sizeof(UW),
};
LOCAL ID	mbfid;

EXPORT void setUp(void)
{
	mbfid = tk_cre_mbf(&cmbf);
}

EXPORT void tearDown(void)
{
	tk_del_mbf(mbfid);
}

/* Sends 0 to count - 1 */
LOCAL void send_rows(UW count)
{
	UW	no, old;
	INT	dropped;

	for(no = 0; no < count; no++) {
		mbf_send_drop_oldest(mbfid, &no, sizeof(no), &old, &dropped);
	}
}

/*
 * Sends DEPTH rows into an empty queue.
 * Expected: each send returns E_OK with 0 dropped.
 */
LOCAL void test_room_left(void)
{
	UW	no, old;
	INT	dropped;

	for(no = 0; no < DEPTH; no++) {
		TEST_ASSERT_EQUAL_INT(E_OK, mbf_send_drop_oldest(mbfid, &no, sizeof(no), &old, &dropped));
		TEST_ASSERT_EQUAL_INT(0, dropped);
	}
}

/*
 * Fills the queue, then sends DEPTH to SENT - 1.
 * Expected: each send returns E_OK with 1 dropped, and the dropped row is the oldest, no - DEPTH.
 */
LOCAL void test_full_drops_oldest(void)
{
	UW	no, old;
	INT	dropped;

	send_rows(DEPTH);
	for(no = DEPTH; no < SENT; no++) {
		TEST_ASSERT_EQUAL_INT(E_OK, mbf_send_drop_oldest(mbfid, &no, sizeof(no), &old, &dropped));
		TEST_ASSERT_EQUAL_INT(1, dropped);
		TEST_ASSERT_EQUAL_UINT32(no - DEPTH, old);
	}
}

/*
 * Sends 0 to SENT - 1, then receives everything.
 * Expected: SENT - DEPTH to SENT - 1 in order, then the queue is empty (E_TMOUT).
 */
LOCAL void test_newest_left_in_order(void)
{
	UW	no, want;

	send_rows(SENT);
	for(want = SENT - DEPTH; want < SENT; want++) {
		TEST_ASSERT_EQUAL_INT(sizeof(no), tk_rcv_mbf(mbfid, &no, TMO_POL));
		TEST_ASSERT_EQUAL_UINT32(want, no);
	}
	TEST_ASSERT_EQUAL_INT(E_TMOUT, tk_rcv_mbf(mbfid, &no, TMO_POL));
}

EXPORT INT usermain(void)
{
	UNITY_BEGIN();
	RUN_TEST(test_room_left);
	RUN_TEST(test_full_drops_oldest);
	RUN_TEST(test_newest_left_in_order);
	UNITY_END();

	tk_slp_tsk(TMO_FEVR);

	return 0;
}
