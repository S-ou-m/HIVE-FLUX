import urllib.request
import json

def fetch(url):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            print(f"{url}: {response.status}")
            data = json.loads(response.read().decode())
            print(f"Data: {str(data)[:100]}...")
    except Exception as e:
        print(f"{url} ERROR: {e}")

fetch("http://127.0.0.1:8000/dashboard/admin/partial/finance/chart/revenue/")
fetch("http://127.0.0.1:8000/dashboard/admin/partial/finance/chart/payment-modes/")
fetch("http://127.0.0.1:8000/dashboard/admin/partial/finance/chart/departments/")
