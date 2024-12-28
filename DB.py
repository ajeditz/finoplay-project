import sqlite3

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

if __name__=="__main__":
    conn = sqlite3.connect('recruiting.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * from jobs")
    tables = cursor.fetchall()
    print(tables)  # Output: [('table1',), ('table2',), ...]
