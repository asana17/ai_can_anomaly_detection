# models

The learned half of the detector. Rules state what the bus must do; these learn what
it usually does, and report what does not fit.

Documented under [docs/](docs).

- [pca](docs/pca.md) scores a row by how far it sits off the subspace normal traffic
  occupies.

Each is fit on normal rows only, from [assemble](../assemble). Attacks come from
[attack](../attack) and are never seen during fitting.

## Tests

Run from the repository root.

```
python3 -m pytest
```
