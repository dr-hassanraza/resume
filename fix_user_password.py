#!/usr/bin/env python3
"""
Fix the user password with proper bcrypt hashing
"""

import sqlite3
import os
import sys
from passlib.context import CryptContext

def fix_user_password():
    """Fix the user password with proper bcrypt hashing"""
    
    # Database file path
    db_path = os.path.join('backend', 'resume_optimizer.db')
    
    if not os.path.exists(db_path):
        print("❌ Database doesn't exist yet.")
        return False
    
    # Initialize password context (same as backend)
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test user credentials
        email = "admin@resumeoptimizer.com"
        username = "admin"
        password = "admin123"
        
        # Hash the password properly with bcrypt
        hashed_password = pwd_context.hash(password)
        
        # Update the user with proper hashed password
        cursor.execute('''
        UPDATE users 
        SET hashed_password = ?
        WHERE email = ? OR username = ?
        ''', (hashed_password, email, username))
        
        if cursor.rowcount == 0:
            print("❌ User not found. Creating new user...")
            # Create the user if it doesn't exist
            cursor.execute('''
            INSERT INTO users 
            (email, username, full_name, hashed_password, is_active, email_verified, subscription_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (email, username, "Resume Optimizer Admin", hashed_password, True, True, 'enterprise'))
        
        conn.commit()
        
        print("✅ User password fixed successfully!")
        print("\n🔑 Updated Login Credentials:")
        print(f"   Email: {email}")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   Access Level: Enterprise (Full Access)")
        print("\n🚀 You can now log into the application at:")
        print("   Frontend: http://localhost:3000")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing user password: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔧 Fixing user password with proper bcrypt hashing...")
    success = fix_user_password()
    if success:
        print("\n✅ Password fix complete! You can now log into the application.")
    else:
        print("\n❌ Failed to fix user password.")
        sys.exit(1)