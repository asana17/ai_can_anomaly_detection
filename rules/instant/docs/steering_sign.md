# steering_sign

Flags the steering angle and the yaw rate turning opposite ways.

```python
hits(raw, min_speed, min_yaw=0.02)   # -> True per row the rule fires on
```

Steering left turns the truck left. How much yaw a given angle produces changes with
speed and body roll, so only the direction is checked. That is what makes this
usable where a size check is not, and it is the only rule watching VDC2.

Below 0.02 rad/s the truck is going straight and either sign is noise. Above it the
two disagree on 0.0168% of evaluations, measured in
[measurements](../../measurements.md).
