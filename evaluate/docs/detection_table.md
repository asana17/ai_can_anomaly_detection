# detection table

`detection_table` puts what test runs and window test runs caught side by side, as
Markdown tables. It counts nothing again. It reads the counts
[run_test_set](run_test_set.md) and [run_window_test_set](run_window_test_set.md)
wrote.

## Running it

```
python3 -m evaluate.detection_table runs_repo revision listed.json local_dir runs_dir out.md
```

| argument | |
|---|---|
| `runs_repo` | Hugging Face model repo holding the directories |
| `revision` | commit of `runs_repo` to read them at |
| `listed.json` | `{"test_runs": [...], "window_test_runs": [...]}`, the paths of the directories to put in the tables |
| `local_dir` | local folder the dataset directories are downloaded to |
| `runs_dir` | local folder the runs directories are downloaded to |
| `out.md` | the Markdown file written |

Only what `listed.json` names goes in. A window test run gives the rows of each instant
model with each window model. It does not add the rows of its test run, which are
listed as a test run of their own.

The fold, the attack and the seed of each directory come from the test set and the log
split its test run names, read at the commits it names them at.

## The tables

`out.md` starts with the repo, the revision and `listed.json`, so the tables can be
made again.

The first tables are one per attack, with all its runs together. A row is a detector
and a column a k. A cell holds the attacks worth catching it caught, of how many, and
its false alarms an hour. A window model's cell adds what it catches over the instant
alarm alone at the k with no more false alarms that catches the most. Caught, worth and
that gain are summed over the runs that hold the detector, and the false alarms an hour
averaged, the runs being about as long.

The later tables are the same, one per fold, attack and seed.

A detector counted twice for one fold, attack and seed stops it with the two
directories named. The rules are the one exception. Two test runs of one test set count
them the same, and they are kept once.
