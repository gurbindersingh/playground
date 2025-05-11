import json


def read_configs(path: str) -> dict:
    with open(path) as json_file:
        configs = json.loads(json_file.read())
    return configs


if __name__ == "__main__":
    print(read_configs("configs/example.json"))
