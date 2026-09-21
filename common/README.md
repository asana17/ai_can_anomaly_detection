# common

What every stage needs, the parameters of a run and the repository directories the
stages hand to each other.

- `settings.py` holds every value a run is made with, and
  [docs/settings.md](docs/settings.md) says how each was set.
- `hub_dirs.py` reads and writes one directory of a Hugging Face repository.
- `schemas/` describes every JSON file a stage uploads, one schema per file, and
  `schema_validate.py` checks a file against its schema. The tests run it on every
  directory a stage uploads.
- `cli.py` reads a stage's arguments, and `git.py` records the commit a run was made
  from.
