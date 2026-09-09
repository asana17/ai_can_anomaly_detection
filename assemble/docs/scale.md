# scale

The 17 signals are in different units, rpm and km/h and radians per second.

A residual is one distance over all of them, so without scaling the signals with the
largest numbers would decide it alone.

Each signal therefore has its mean subtracted and is divided by its std.
[train_set](train_set.md) computes both from the rows it builds out of the training
logs.

[attack_set](attack_set.md) uses them for two things. It z-scores its own rows, so a
model reads the test rows in the units it was fitted in. It also divides by the std to
report `moved`, how far an attack pushed a row.

They are saved as `mean.npy` and `std.npy`, which is how [evaluate](../../evaluate)
reads them back on a later run.
