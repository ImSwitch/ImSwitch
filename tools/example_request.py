import requests

url = "http://169.254.165.4:8000"
url = "http://localhost:8000"

test = "/start_viewer/"
single_run = "/start_viewer_single_loop/10"
compeleted = "/wait_for_viewer_completion/"

response = requests.get(url+single_run)
complete = requests.get(url+compeleted)
print(complete.json())