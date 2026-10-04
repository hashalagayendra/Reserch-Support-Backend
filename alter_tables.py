import sys
import os

# Add the project root to the sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.session import engine

def alter_tables():
    tables = ['students', 'users', 'projects', 'api_keys', 'ai_tools']
    
    with engine.connect() as conn:
        for table in tables:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"))
                print(f"Added created_at to {table}")
            except Exception as e:
                print(f"Could not add created_at to {table}: {e}")
                
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE"))
                print(f"Added updated_at to {table}")
            except Exception as e:
                print(f"Could not add updated_at to {table}: {e}")
                
        conn.commit()

if __name__ == "__main__":
    alter_tables()
