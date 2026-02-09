# test_requests.py
# POST request with JSON using the requests library

import requests

# Make a POST request with JSON data
# The json= parameter encodes the dict and sets Content-Type: application/json
url = "https://httpbin.org/post"
data = {"name": "test"}
response = requests.post(url, json=data)

# Get the response
print(response.status_code)
print(response.json())
