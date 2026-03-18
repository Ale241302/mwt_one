from knowledge_service.database import engine, init_db
from knowledge_service.indexer import run_indexer
import traceback

def main():
    try:
        print("Running init_db()...")
        init_db()
        print("init_db() finished.")
        with engine.begin() as conn:
            res = run_indexer(conn)
            print("INDEXER RESULT:", res)
    except Exception as e:
        print("INDEXER FAILED:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
