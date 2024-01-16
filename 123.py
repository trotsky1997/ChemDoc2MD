import json
import os

with open('./123.json','r') as f:
    data = json.load(f)
    # print(data)
    print([data['input']])
    print('1111')
    print(data['input'])