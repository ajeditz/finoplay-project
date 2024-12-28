import sqlite3
from typing import Dict, List, Tuple, Optional, TypedDict

# Database setup
def setup_database():
    conn = sqlite3.connect('recruiting.db')
    cursor = conn.cursor()
    
    # Create candidates table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        experience_years INTEGER,
        skills TEXT,
        current_role TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create jobs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        requirements TEXT,
        location TEXT,
        salary_range TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    
# Database operations
class DatabaseOperations:
    def __init__(self, db_path='recruiting.db'):
        self.db_path = db_path
    
    def add_candidate(self, candidate_data: Dict) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO candidates (name, email, phone, experience_years, skills, current_role)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                candidate_data['name'],
                candidate_data['email'],
                candidate_data['phone'],
                candidate_data['experience_years'],
                candidate_data['skills'],
                candidate_data['current_role']
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding candidate: {e}")
            return False
        finally:
            conn.close()
    
    def get_active_jobs(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM jobs WHERE is_active = 1')
        jobs = cursor.fetchall()
        conn.close()
        
        return [{
            'id': job[0],
            'title': job[1],
            'description': job[2],
            'requirements': job[3],
            'location': job[4],
            'salary_range': job[5]
        } for job in jobs]

if __name__=="__main__":
    conn = sqlite3.connect('recruiting.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * from jobs")
    tables = cursor.fetchall()
    print(tables)  # Output: [('table1',), ('table2',), ...]
