# windows

A window model reads the last `rows` moving rows together.

## Position

`positions(moving, segment)` gives each row how many rows come before it in its
unbroken run of moving rows. A row not moving gets -1.

A run ends at a row not moving, and where the grid's segment changes. A missing tick
starts a new segment, so it ends the run too. A row a rule hits does not end the run.

## Where a window ends

`window_ends(position, rows, stride)` gives the indices of the rows that end a window.
A row ends one when its position is at least `rows - 1` and `position - (rows - 1)` is
a multiple of `stride`.

The ends at a `stride` above 1 are some of the ends at a `stride` of 1. So a model can
score every window once at a `stride` of 1. The scores at any other `stride` are then
the scores at the ends that `window_ends` gives for it.

## The window

`window_rows(grid_rows, ends, rows)` gives the window each end ends, its `rows` rows of
`grid_rows` oldest first. The caller passes scaled grid rows for a model or raw ones for
a rule. A window is cut as it is, NaN included.
