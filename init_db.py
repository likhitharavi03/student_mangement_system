import sqlite3

# Connect to SQLite database (creates if doesn't exist)
conn = sqlite3.connect("colleges.db")
cursor = conn.cursor()

# Read schema from schema.sql
with open("schema.sql", "r") as f:
    schema = f.read()

# Execute the schema
cursor.executescript(schema)
conn.commit()
conn.close()

print("Database 'colleges.db' initialized successfully!")
