import requests
import json
import base64
import re
from io import BytesIO
from PIL import Image

API_URL = "http://localhost:8000/api/"

def validate_image(base64_str):
    """Check if base64 PNG is valid and <100KB"""
    try:
        if not base64_str.startswith("data:image/png;base64,"):
            return False, "Invalid header"
        data = base64.b64decode(base64_str.split(",")[1])
        if len(data) > 100_000:
            return False, "Image too large"
        Image.open(BytesIO(data))
        return True, "OK"
    except Exception as e:
        return False, str(e)

def run_highest_grossing_test():
    print("\n🎬 Highest Grossing Films Test")
    with open("questions.txt", "rb") as f:
        files = {"file": ("questions.txt", f)}
        r = requests.post(API_URL, files=files)
    print("Status Code:", r.status_code)
    try:
        arr = r.json()
    except:
        print("❌ Response not JSON")
        return
    if not isinstance(arr, list) or len(arr) != 4:
        print("❌ Incorrect structure")
        return
    print("✅ Structure OK")

    img_ok, msg = validate_image(arr[3])
    print("Image validation:", msg)

def run_sales_dataset_test():
    print("\n📊 Sales Dataset Test")
    with open("questions_sales.txt", "rb") as f1, open("sample-sales.csv", "rb") as f2:
        files = {
            "file": ("questions_sales.txt", f1),
            "other_files": ("sample-sales.csv", f2)
        }
        r = requests.post(API_URL, files=files)
    print("Status Code:", r.status_code)
    try:
        obj = r.json()
    except:
        print("❌ Response not JSON")
        return
    if not isinstance(obj, dict):
        print("❌ Incorrect format")
        return
    print("✅ Structure OK")
    if "bar_chart" in obj:
        img_ok, msg = validate_image(obj["bar_chart"])
        print("Bar chart validation:", msg)
    if "cumulative_sales_chart" in obj:
        img_ok, msg = validate_image(obj["cumulative_sales_chart"])
        print("Cumulative chart validation:", msg)

if __name__ == "__main__":
    run_highest_grossing_test()
    run_sales_dataset_test()
