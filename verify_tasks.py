import os
import urllib.request
import urllib.error
import json

# Simple .env loader
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def verify_tasks():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    data = {
        "filter": {
            "property": "Sprint",
            "select": {
                "equals": "Sprint 12"
            }
        }
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as res:
            results = json.loads(res.read().decode())["results"]
            print(f"Total tasks found in Sprint 12: {len(results)}")
            for r in results:
                item = r["properties"]["Item"]["rich_text"][0]["plain_text"]
                name = r["properties"]["Tarea"]["title"][0]["plain_text"]
                status = r["properties"]["Estado"]["select"]["name"]
                print(f"- {item}: {name} [{status}]")
    except Exception as e:
        print(f"Error verifying: {e}")
        if isinstance(e, urllib.error.HTTPError):
            print(e.read().decode())

verify_tasks()
