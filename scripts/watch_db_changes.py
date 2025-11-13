import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import subprocess

DB_PATH = Path("db/nika_data.db")

class DBWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("nika_data.db"):
            print("🧠 Database changed — syncing RAG...")
            subprocess.run(["python", "-m", "scripts.sync_rag_from_db"])

if __name__ == "__main__":
    observer = Observer()
    handler = DBWatcher()
    observer.schedule(handler, str(DB_PATH.parent), recursive=False)
    observer.start()
    print("👀 Watching DB for changes...")
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
