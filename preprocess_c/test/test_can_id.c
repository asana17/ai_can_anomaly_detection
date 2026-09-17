/**
 * test_can_id.c — Unit tests for can_id_decompose().
 *
 * Golden values come directly from the Python docs and the worked example in
 * preprocess/docs/can_id_decompose.md.
 *
 * Compile & run:
 *   make test_can_id && ./test_can_id
 */
#include "../can_id.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>

static void check(uint32_t arb_id,
                  uint8_t  exp_priority,
                  uint32_t exp_pgn,
                  uint8_t  exp_sa,
                  const char *label)
{
    CanId got = can_id_decompose(arb_id);
    assert(got.priority       == exp_priority);
    assert(got.pgn            == exp_pgn);
    assert(got.source_address == exp_sa);
    printf("PASS  %s\n", label);
}

int main(void)
{
    /*
     * Worked example from can_id_decompose.md:
     *   0x18F004E6  PF=0xF0 (240) ≥ 240 → PDU2
     *   pgn = (0xF0 << 8) | 0x04 = 61444 (EEC1)
     *   priority = (0x18F004E6 >> 26) & 7 = 6
     *   SA = 0xE6 = 230
     */
    check(0x18F004E6u, 6, 61444u, 0xE6u, "EEC1 0x18F004E6 → pgn=61444 pri=6 sa=0xE6");

    /*
     * PDU1 example: PF < 240, PS is a destination address and is excluded.
     *   0x0C000003  PF=0x00, DP=0, SA=0x03
     *   pgn = (0 << 16) | (0x00 << 8) = 0
     *   priority = (0x0C000003 >> 26) & 7 = 3
     */
    check(0x0C000003u, 3, 0u, 0x03u, "PDU1 0x0C000003 → pgn=0 pri=3 sa=3");

    /*
     * CCVS1: PGN 65265 = 0xFF11
     *   A typical arbitration ID: 0x18FEF121
     *   PF=0xFE=254 ≥ 240 → PDU2
     *   PS=0xF1, DP=0 → pgn = (0xFE<<8)|0xF1 = 0xFEF1 = 65265
     *   priority=6, SA=0x21
     */
    check(0x18FEF121u, 6, 65265u, 0x21u, "CCVS1 0x18FEF121 → pgn=65265");

    /*
     * High bits beyond bit 28 must be masked off (capture-format flags).
     *   Same as EEC1 example but with bit 31 set.
     */
    check(0x98F004E6u, 6, 61444u, 0xE6u, "EEC1 with bit-31 flag masked out");

    printf("\nAll CAN ID tests passed.\n");
    return 0;
}
