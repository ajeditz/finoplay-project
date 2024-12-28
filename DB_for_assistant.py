import sqlite3
from datetime import  datetime
# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('recruitment.db')
cursor = conn.cursor()

# # Create the Candidates table
# cursor.execute('''
# CREATE TABLE IF NOT EXISTS Candidates (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT NOT NULL,
#     email TEXT NOT NULL,
#     phone TEXT NOT NULL,
#     resume_link TEXT NOT NULL
# );
# ''')

# # Create the JobPostings table
# cursor.execute('''
# CREATE TABLE IF NOT EXISTS JobPostings (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     title TEXT NOT NULL,
#     description TEXT NOT NULL,
#     location TEXT NOT NULL,
#     date_posted TEXT NOT NULL
# );
# ''')

# # Sample data for Candidates table
# candidates = [
#     ('Alice Johnson', 'alice.johnson@example.com', '555-1234', 'http://example.com/resume/alice_johnson.pdf'),
#     ('Bob Smith', 'bob.smith@example.com', '555-5678', 'http://example.com/resume/bob_smith.pdf'),
#     ('Carol White', 'carol.white@example.com', '555-8765', 'http://example.com/resume/carol_white.pdf'),
#     ('David Brown', 'david.brown@example.com', '555-4321', 'http://example.com/resume/david_brown.pdf'),
#     ('Eve Black', 'eve.black@example.com', '555-6789', 'http://example.com/resume/eve_black.pdf'),
#     ('Frank Green', 'frank.green@example.com', '555-9876', 'http://example.com/resume/frank_green.pdf')
# ]

# # Insert data into Candidates table
# cursor.executemany('''
# INSERT INTO Candidates (name, email, phone, resume_link)
# VALUES (?, ?, ?, ?)
# ''', candidates)

# job_postings = [
#     ('Software Engineer', 'Develop and maintain software applications.', 'New York, NY', datetime.now().strftime('%Y-%m-%d')),
#     ('Data Analyst', 'Analyze data to support business decisions.', 'San Francisco, CA', datetime.now().strftime('%Y-%m-%d')),
#     ('Project Manager', 'Lead project teams to deliver solutions.', 'Chicago, IL', datetime.now().strftime('%Y-%m-%d')),
#     ('UX Designer', 'Design user interfaces for web applications.', 'Austin, TX', datetime.now().strftime('%Y-%m-%d')),
#     ('Marketing Specialist', 'Develop marketing strategies and campaigns.', 'Seattle, WA', datetime.now().strftime('%Y-%m-%d')),
#     ('Sales Representative', 'Sell products and services to clients.', 'Boston, MA', datetime.now().strftime('%Y-%m-%d'))
# ]

# # Insert data into JobPostings table
# cursor.executemany('''
# INSERT INTO JobPostings (title, description, location, date_posted)
# VALUES (?, ?, ?, ?)
# ''', job_postings)

cursor.execute('''
SELECT * FROM Candidates''')
print(cursor.fetchall())
# Commit the changes and close the connection
conn.commit()
conn.close()
