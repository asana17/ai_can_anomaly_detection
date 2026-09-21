# detect

Turns the model's scores and the rule hits into alarms. [scoring](../scoring) writes
both.

Documented under [docs/](docs).

- [alarm](docs/alarm.md) flags a row a rule hits or whose score is above the
  threshold, and raises an alarm after `HOLD` flagged rows in a row.
