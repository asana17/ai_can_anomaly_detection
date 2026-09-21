# scale

`scale_for(rows)` takes the mean and std of a [Scale](../../preprocess/docs/scale.md)
from the rows given. A signal that never changes keeps a std of 1, so it stays at 0
instead of dividing by zero.
