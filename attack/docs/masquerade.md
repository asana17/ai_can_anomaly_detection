# masquerade

Fakes signal values in a normal trace by overwriting them in place. The frames
keep their original timing and count. Only the values change.

## Example

```python
masquerade(frames, {65265: {"wheel_speed": 5.0}}, start=10.0, stop=20.0)
```

Every CCVS1 (PGN 65265) frame between t=10 and t=20 gets its `wheel_speed`
rewritten to 5.0 km/h. All other frames, and all other signals, are untouched.

`changes` has the form `{pgn: {signal: value}}`, so several signals can be faked
at once.

## Why overwrite instead of inject

Adding fake frames would raise the message rate and trip a timing check.
Overwriting keeps the rate normal, so the attack shows up only in the values.

Faking one signal breaks its link to the others and is easy to spot. Faking
several signals with matching values keeps the links intact and is stealthier.
Those matching values come from the normal correlation, measured separately.
