# Rule check from Flash

Sends the 80 rows of `raw_rows.h` through a queue, one every 100 ms, and runs one rule
on each row. The rule flags a row where the gear is below 0 and the wheel speed is
above 10 km/h. It was made to check that rows pass through the queue and that the rule
gives the same result as on the PC.

The rule is written in `usermain.c` of this application. The rules in
[`board/lib/rules/`](../../lib/rules) run in `can_path_from_flash` and
`ai_can_anomaly_detection`.

## Check on the board

```sh
python3 -m board.prepare CUBEIDE_PROJECT_DIR rule_check_from_flash
python3 board/flash.py CUBEIDE_PROJECT_DIR
```

On the PC the same rule flags rows 1253 to 1312, 60 rows in all. The last UART line
should read:

```
reverse rule: processed 80/80, flagged_rows 60, dropped 0
```
