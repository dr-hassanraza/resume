#\!/usr/bin/env python3

import sqlite3
from passlib.context import CryptContext
from datetime import datetime
import uuid

# Initialize password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User data
email = "admin@resumes.ai"
username = "admin"
password = "admin123"
first_name = "Admin"
last_name = "User"
subscription_tier = "enterprise"

# Hash the password
hashed_password = pwd_context.hash(password)

# Connect to database
conn = sqlite3.connect('resume_optimizer.db')
cursor = conn.cursor()

# Create users table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    full_name TEXT,
    phone_number TEXT,
    profile_picture_url TEXT,
    bio TEXT,
    location TEXT,
    website TEXT,
    linkedin_url TEXT,
    github_url TEXT,
    subscription_tier TEXT DEFAULT 'free',
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT true,
    last_login DATETIME,
    login_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# Insert or update user
cursor.execute('''
INSERT OR REPLACE INTO users (
    email, username, hashed_password, first_name, last_name, 
    full_name, subscription_tier, is_active, email_verified,
    login_count, created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    email, username, hashed_password, first_name, last_name,
    f"{first_name} {last_name}", subscription_tier, True, True,
    0, datetime.now().isoformat(), datetime.now().isoformat()
))

conn.commit()
conn.close()

print(f"Created user: {email} / {username} with password: {password}")
print(f"Subscription tier: {subscription_tier}")
print("User created successfully\!")
EOF < /dev/null