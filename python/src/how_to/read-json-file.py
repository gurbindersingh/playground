import json

with open("configs/reminder-webhook.json") as f:
    myJson = json.loads(f.read())

print(myJson)
