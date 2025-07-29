import requests
import json

class RestClient:
    domain = "https://api.dataforseo.com/"

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def request(self, path, method, data=None):
        databyte = None
        if data is not None:
            databyte = bytes(json.dumps(data), "utf-8")
        return requests.request(method, self.domain + path, data=databyte, 
                              auth=(self.username, self.password), 
                              headers={"content-type": "application/json"})

    def get(self, path):
        return self.request(path, 'GET')

    def post(self, path, data):
        return self.request(path, 'POST', data)

    def put(self, path, data):
        return self.request(path, 'PUT', data)

    def delete(self, path):
        return self.request(path, 'DELETE')