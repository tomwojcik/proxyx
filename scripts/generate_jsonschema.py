import json

from proxyx.models import Proxyx
from proxyx.settings import ROOT_DIR


def generate_jsonschema():
    with open(ROOT_DIR / "jsonschema.json", "w") as f:
        schema = Proxyx.schema()
        json.dump(schema, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    generate_jsonschema()
