
import json


with open('my_map.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(data)

