# assemble

Builds the train, validation, and test sets from the preprocess pipeline, split by
time.

Documented under [docs/](docs).

- [split](docs/split.md) splits the log files into train, validation, and test by
  time.
- [datasets](docs/datasets.md) turns the split file lists into normalized model
  arrays, with the time and segment id of every row.

## Tests

Run from the repository root.

```
python3 -m pytest
```
