import os
import sqlite3
import datetime

DB_PATH = "state.db"
WORKSPACE_DIR = "workspace"

def recover_sessions():
    if not os.path.exists(WORKSPACE_DIR):
        print("No workspace directory found.")
        return

    # Connect to DB (creates it if missing)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ensure Table Exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_metadata (
            session_id TEXT PRIMARY KEY,
            model_name TEXT,
            created_at TIMESTAMP,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            cached_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            total_cost REAL DEFAULT 0.0
        )
    """)
    
    # Scan Directories
    restored_count = 0
    for item in os.listdir(WORKSPACE_DIR):
        item_path = os.path.join(WORKSPACE_DIR, item)
        if os.path.isdir(item_path):
            session_id = item
            
            # Check if exists
            cursor.execute("SELECT 1 FROM session_metadata WHERE session_id = ?", (session_id,))
            if cursor.fetchone():
                print(f"Skipping {session_id} (already exists)")
                continue
                
            # Insert
            print(f"Restoring {session_id}...")
            # Use directory modification time or now
            timestamp = datetime.datetime.fromtimestamp(os.path.getctime(item_path))
            
            cursor.execute("""
                INSERT INTO session_metadata (session_id, model_name, created_at)
                VALUES (?, ?, ?)
            """, (session_id, "gemini-2.5-flash", timestamp))
            restored_count += 1
            
    conn.commit()
    conn.close()
    print(f"Recovery Complete. Restored {restored_count} sessions.")

if __name__ == "__main__":
    recover_sessions()
