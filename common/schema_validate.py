"""Check a JSON file a stage writes against its JSON Schema in `schemas/`.

The tests run it on every directory a stage uploads, so a schema and the code that
writes its file cannot drift apart.
"""

from __future__ import annotations

import json
import os

import jsonschema
from referencing import Registry, Resource

SCHEMAS = os.path.join(os.path.dirname(__file__), "schemas")
REGISTRY = Registry().with_resources(
    (name, Resource.from_contents(json.load(open(os.path.join(SCHEMAS, name)))))
    for name in os.listdir(SCHEMAS) if name.endswith(".schema.json"))


def check(data, schema):
    """Raise unless `data`, read from a JSON file, fits `schema`.

    `schema` is a file name in `schemas/`, with a `#/...` part for a piece of it. A NaN
    or an infinity raises too, since no schema can refuse one.
    """
    json.dumps(data, allow_nan=False)
    jsonschema.validate(data, {"$ref": schema}, registry=REGISTRY)

