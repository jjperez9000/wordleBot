import json

data = None
with open('secrets/scores.json', 'r') as f:
    data = json.load(f)

# print(data)
for thing in data:
    data[thing]['weekly_score'] = 0
    data[thing]['recent_scores'] = [0, 0, 0, 0, 0, 0, 0]
print(data)

with open('secrets/scores.json', 'w') as f:
    f.write(json.dumps(data, indent=4))
