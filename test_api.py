import os
import sys
import json
import urllib.request
import urllib.error

url = "http://187.77.218.102:8001/api/knowledge/ask/"
req = urllib.request.Request(url, method="POST")
req.add_header("accept", "application/json")
req.add_header("Authorization", "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYWRtaW4iLCJwZXJtaXNzaW9ucyI6WyJBU0tfS05PV0xFREdFX09QUyIsIkFTS19LTk9XTEVER0VfUFJPRFVDVFMiLCJBU0tfS05PV0xFREdFX1BSSUNJTkciLCJJTkRFWF9LTk9XTEVER0UiXX0.H5d54w_U__Hi_UQZimbom_b8Gim8hH-ivEpfUwPUryQ")
req.add_header("Content-Type", "application/json")

data = json.dumps({
    "question": "que prodcutos tiene rana walk",
    "session_id": "string",
    "expediente_ref": 0
}).encode("utf-8")

try:
    with urllib.request.urlopen(req, data=data) as f:
        print("STATUS:", f.status)
        import json
        resp = json.loads(f.read().decode("utf-8"))
        print(json.dumps(resp, indent=2))
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code)
    print(e.read().decode("utf-8"))
except Exception as e:
    print("ERROR:", e)
