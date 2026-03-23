import os
import urllib.request
import json

if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

url = f"https://api.notion.com/v1/databases/{DATABASE_ID}"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28"
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as res:
        data = json.load(res)
        props = data["properties"]
        for name in ["Estado", "Sprint", "Fase", "Fases"]:
            if name in props:
                details = props[name]
                prop_type = details["type"]
                if prop_type in ["select", "multi_select"]:
                    opts = [o["name"] for o in details[prop_type]["options"]]
                    print(f"{name}: {opts}")
                else:
                    print(f"{name}: type {prop_type}")
            else:
                print(f"{name}: NOT FOUND")
except Exception as e:
    print(f"Error: {e}")
