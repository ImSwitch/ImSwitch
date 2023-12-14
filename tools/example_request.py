import requests
import time

url = "http://169.254.165.4:8000"
#url = "http://localhost:8000"

test = "/start_viewer/"
single_run = "/start_viewer_single_loop/2"
compeleted = "/wait_for_viewer_completion/"

for i in range(4):
    response = requests.get(url+single_run)
    print(response.json)
    complete = requests.get(url+compeleted)
    print(complete.json())
    time.sleep(5)