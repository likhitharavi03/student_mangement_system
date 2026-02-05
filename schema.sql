-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fname TEXT NOT NULL,
    lname TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'student'
);

-- Student table
CREATE TABLE IF NOT EXISTS student (
    sid INTEGER PRIMARY KEY AUTOINCREMENT,
    sname TEXT NOT NULL,
    sbranch TEXT NOT NULL,
    smarks INTEGER NOT NULL,
    phno TEXT
);
