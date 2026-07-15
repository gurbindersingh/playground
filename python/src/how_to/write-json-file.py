import json

from utils.path_utils import path_from_project_root

data = {
    "foo": "bar",
    "bar": "baz",
}

output_file_path = path_from_project_root("data", "example.json")
# output_file_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_file_path, mode="w", encoding="utf-8") as json_file:
    json.dump(data, json_file, indent=2)
