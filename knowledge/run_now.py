from database import engine, init_db
from indexer import run_indexer
try:
    init_db()
    with engine.begin() as conn:
        res = run_indexer(conn)
        print("INDEXER RESULT:", res)
except Exception as e:
    print("FAILED:", e)
