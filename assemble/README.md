# assemble

Builds the train, validation, and test sets from the preprocess pipeline, split by
time.

Documented under [docs/](docs).

- [split](docs/split.md) cuts the logs into train and test by time, and holds
  blocks out of the training period to read a threshold off.
- [datasets](docs/datasets.md) turns the split file lists into normalized model
  arrays, with the time and segment id of every row.
- [attack_set](docs/attack_set.md) builds the test arrays with attacks in them, and
  says which rows each one changed.

## Tests

Run from the repository root.

```
python3 -m pytest
```
