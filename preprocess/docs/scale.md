# scale

The 17 signals are in different units, rpm and km/h and radians per second.

A residual is one distance over all of them, so without scaling the signals with the
largest numbers would decide it alone. Each signal therefore has its mean subtracted
and is divided by its std.

`Scale` holds the mean and std. `Scale.apply` puts rows on them, `Scale.undo` takes
them back off.
