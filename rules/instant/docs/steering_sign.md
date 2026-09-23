# steering_sign

Flags the steering angle and the yaw rate turning opposite ways.

```python
hits(raw, min_speed, min_yaw=0.05)   # -> True per row the rule fires on
```

Steering left turns the truck left. How much yaw a given angle produces changes with
speed and body roll, so only the direction is checked. That is what makes this
usable where a size check is not, and it is the only rule watching VDC2.

Below 0.05 rad/s the truck is going straight and either sign is noise. Over the
2,757,787 moving grid rows of every log the rule fires on 191 at 0.05, against 2,545
at 0.02, measured in [measurements](../../measurements.md).
