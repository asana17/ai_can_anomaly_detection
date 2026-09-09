# assemble

Builds the train, validation, and test sets from the preprocess pipeline, split by
time.

Documented under [docs/](docs).

- [split](docs/split.md) cuts the logs into train and test by time, sized by the
  driving in them.
- [datasets](docs/datasets.md) turns a list of logs into z-scored model rows, with
  the physical values, time and segment id of each beside them.
- [attack_set](docs/attack_set.md) builds the test arrays with attacks in them, and
  says which rows each one changed.

## Tests

Run from the repository root.

```
python3 -m pytest
```
