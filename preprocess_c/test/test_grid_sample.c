/**
 * test_grid_sample.c — Unit tests for GridSampler / grid_feed().
 *
 * All tests use the EEC1 PGN (61444) with a synthetic payload that encodes
 * a known engine_speed value, plus the other 8 PGNs with trivially-zero
 * payloads to fill every signal slot.
 *
 * The test simulates feeding frames at controlled timestamps and verifies
 * that on_row is called the right number of times and at the right ticks.
 *
 * Compile & run:
 *   make test_grid_sample && ./test_grid_sample
 */
#include "../grid_sample.h"
#include "../spn_spec.h"
#include "../can_id.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

/* ---------------------------------------------------------------------------
 * Helpers
 * --------------------------------------------------------------------------- */

/* Build a 29-bit J1939 arbitration ID for a given PGN with SA=0xE6, pri=6. */
static uint32_t make_arb_id(uint32_t pgn)
{
    /* pgn already has DP+PF+PS packed; SA=0xE6; priority=6 */
    return (6u << 26) | (pgn << 8) | 0xE6u;
}

/* Callback bookkeeping. */
#define MAX_ROWS 64
static float    captured_rows[MAX_ROWS][NUM_SIGNALS];
static uint32_t captured_ticks[MAX_ROWS];
static int      row_count = 0;

static void reset_capture(void) { row_count = 0; }

static void on_row(const float row[NUM_SIGNALS], uint32_t tick_ms)
{
    assert(row_count < MAX_ROWS);
    memcpy(captured_rows[row_count], row, NUM_SIGNALS * sizeof(float));
    captured_ticks[row_count] = tick_ms;
    row_count++;
}

/* Feed one frame with an 8-byte zero payload for the given PGN. */
static void feed_zero(GridSampler *g, uint32_t pgn, uint32_t now_ms)
{
    static const uint8_t zeros[8] = {0};
    grid_feed(g, make_arb_id(pgn), zeros, 8, now_ms);
}

/*
 * Build an EEC1 payload with engine_speed = rpm.
 * SPN 190: start_bit=24, length=16, scale=0.125
 * raw = rpm / 0.125 = rpm * 8
 */
static void feed_eec1_rpm(GridSampler *g, float rpm, uint32_t now_ms)
{
    uint8_t payload[8] = {0};
    uint16_t raw = (uint16_t)(rpm * 8.0f);
    payload[3] = (uint8_t)(raw & 0xFF);
    payload[4] = (uint8_t)(raw >> 8);
    grid_feed(g, make_arb_id(61444u), payload, 8, now_ms);
}

/*
 * Feed a minimal burst that fills all 17 signals once.
 * The PGNs are fed with zero payloads (most signals will be 0 or negative
 * after offset, but that is fine for the ready() check).
 * EEC1 is fed with a known RPM.
 */
static void seed_all_signals(GridSampler *g, float rpm, uint32_t t)
{
    feed_eec1_rpm(g, rpm, t);          /* EEC1: engine_speed, demand, actual torque */
    feed_zero(g, 61443u, t);           /* EEC2 */
    feed_zero(g, 65265u, t);           /* CCVS1 */
    feed_zero(g, 65266u, t);           /* LFE1 */
    feed_zero(g, 61442u, t);           /* ETC1 */
    feed_zero(g, 61445u, t);           /* ETC2 */
    feed_zero(g, 65132u, t);           /* TCO1 */
    feed_zero(g, 61441u, t);           /* EBC1 */
    feed_zero(g, 61449u, t);           /* VDC2 */
}

/* ---------------------------------------------------------------------------
 * Tests
 * --------------------------------------------------------------------------- */

/*
 * T1: No rows before all signals have been seen.
 *
 * Feed only EEC1 frames.  The grid should not emit any rows even when ticks
 * elapse, because signal_state_ready() is false.
 */
static void test_not_ready_no_rows(void)
{
    GridSampler g;
    grid_sampler_init(&g, 100, 1000, on_row);
    reset_capture();

    /* t=0ms: EEC1 only → state not ready */
    feed_eec1_rpm(&g, 800.0f, 0);
    /* t=200ms: another EEC1, two ticks should have elapsed but not emitted */
    feed_eec1_rpm(&g, 810.0f, 200);

    assert(row_count == 0);
    printf("PASS  T1: no rows before all signals seen\n");
}

/*
 * T2: Rows emitted once all signals arrive.
 *
 * Seed all signals at t=0.  At t=200ms another frame arrives; the two
 * grid ticks at t=100 and t=200 should both fire.
 */
static void test_rows_after_ready(void)
{
    GridSampler g;
    grid_sampler_init(&g, 100, 1000, on_row);
    reset_capture();

    /* Seed all signals at t=0; grid armed → next_tick = 100 */
    seed_all_signals(&g, 1000.0f, 0);
    assert(row_count == 0);   /* tick not reached yet */

    /* At t=200: ticks 100 and 200 both fire */
    feed_eec1_rpm(&g, 1000.0f, 200);
    assert(row_count == 2);
    assert(captured_ticks[0] == 100);
    assert(captured_ticks[1] == 200);
    printf("PASS  T2: two rows emitted for t=100 and t=200\n");
}

/*
 * T3: Gap > max_hold resets the state.
 *
 * Seed all signals, let some ticks fire, then simulate a 1500 ms gap.
 * The row count should not increase across the gap, and after re-seeding
 * it should resume.
 */
static void test_gap_resets(void)
{
    GridSampler g;
    grid_sampler_init(&g, 100, 1000, on_row);
    reset_capture();

    /* Seed at t=0, tick fires at t=100 */
    seed_all_signals(&g, 500.0f, 0);
    feed_eec1_rpm(&g, 500.0f, 100);   /* emits row at t=100 */
    int before_gap = row_count;
    assert(before_gap == 1);

    /* Gap of 1500 ms → exceeds max_hold=1000 → state resets */
    /* t=1600: the gap check fires, state is reset, nothing emitted */
    feed_eec1_rpm(&g, 500.0f, 1600);
    assert(row_count == before_gap);   /* no additional rows */

    /* Re-seed all signals; grid re-armed → next_tick = 1700 */
    seed_all_signals(&g, 500.0f, 1600);

    /*
     * t=1800: ticks 1700 and 1800 both fire (1800 >= 1800).
     * Two rows are emitted, not one — this is correct grid behaviour.
     */
    feed_eec1_rpm(&g, 500.0f, 1800);
    assert(row_count == before_gap + 2);
    assert(captured_ticks[before_gap]     == 1700u);
    assert(captured_ticks[before_gap + 1] == 1800u);
    printf("PASS  T3: gap > max_hold resets state and resumes\n");
}

/*
 * T4: Hold-last: engine_speed from EEC1 persists across non-EEC1 frames.
 *
 * Seed all signals with engine_speed=1000 rpm, then advance time with
 * non-EEC1 frames.  The emitted rows should still carry 1000 rpm.
 */
static void test_hold_last(void)
{
    GridSampler g;
    grid_sampler_init(&g, 100, 1000, on_row);
    reset_capture();

    seed_all_signals(&g, 1000.0f, 0);   /* engine_speed = 1000 rpm */

    /* Advance with CCVS1 only (no EEC1 update) */
    feed_zero(&g, 65265u, 100);   /* tick 100 fires */
    feed_zero(&g, 65265u, 200);   /* tick 200 fires */

    assert(row_count == 2);
    /* signal index 0 = engine_speed */
    assert(fabsf(captured_rows[0][0] - 1000.0f) < 0.5f);
    assert(fabsf(captured_rows[1][0] - 1000.0f) < 0.5f);
    printf("PASS  T4: engine_speed held across non-EEC1 frames (%.1f rpm)\n",
           (double)captured_rows[0][0]);
}

/*
 * T5: Period boundary — exactly on-period frame triggers exactly one row.
 */
static void test_period_boundary(void)
{
    GridSampler g;
    grid_sampler_init(&g, 100, 1000, on_row);
    reset_capture();

    seed_all_signals(&g, 200.0f, 0);
    feed_zero(&g, 65265u, 100);   /* exactly at first tick */
    assert(row_count == 1);
    assert(captured_ticks[0] == 100u);
    printf("PASS  T5: frame exactly at tick emits one row\n");
}

/* ---------------------------------------------------------------------------
 * Main
 * --------------------------------------------------------------------------- */
int main(void)
{
    test_not_ready_no_rows();
    test_rows_after_ready();
    test_gap_resets();
    test_hold_last();
    test_period_boundary();

    printf("\nAll grid_sample tests passed.\n");
    return 0;
}
