import json, os

# Open and read the JSON file
with open('output.json', 'r') as file:
    data = json.load(file)

# Access the crop analysis text
crop_analysis_text = data['response']

print(crop_analysis_text)

os.remove('output.json')