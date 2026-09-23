#!/bin/sh
# Send the nine J1939 frames the model reads, with fixed "moving / normal" values,
# so ai_can_anomaly_detection's inference path runs. Extended 29-bit IDs, 250 kbps.
#
# The nine PGNs and their payloads are computed from preprocess/frames/spn_spec.py
# by board/send_test_frames.py; this script is the no-dependency form. wheel_speed
# is 50 km/h so moving() passes; every other signal sits in its normal range.
#
# Usage: ./board/send_test_frames.sh [interface] [period_seconds]
#   interface     SocketCAN interface, default can0
#   period_seconds delay between full rounds, default 1 (0 = send once and exit)
#
# Bring the bus up first (matching the board's 250 kbps):
#   sudo ip link set can0 type can bitrate 250000
#   sudo ip link set can0 up

IFACE="${1:-can0}"
PERIOD="${2:-1}"

# arb_id#payload, one per PGN the model decodes
FRAMES="
18F00400#FFA5AA401FFFFFFF
18F00300#FF6432FFFFFFFFFF
18FEF100#FF0032FFFFFFFFFF
18FEF200#9001FFFFFFFFFFFF
18F00200#FFD41700FFD417FF
18F00500#82FFFF82FFFFFFFF
18FE6C00#FFFFFFFFFFFF0032
18F00100#FF00FFFFFFFFFFFF
18F00900#7F7DFF717D7F7DFF
"

send_round() {
	for f in $FRAMES; do
		cansend "$IFACE" "$f"
	done
}

if [ "$PERIOD" = "0" ]; then
	send_round
	exit 0
fi

while true; do
	send_round
	sleep "$PERIOD"
done
