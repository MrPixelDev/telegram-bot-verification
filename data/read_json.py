import json


def read_json(name):
    with open(f"./data/{name}.json") as file:
        data = json.load(file)
        return data
