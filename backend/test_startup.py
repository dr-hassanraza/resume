#!/usr/bin/env python3
"""
Simple test to check if all imports work correctly
"""

try:
    print("Testing imports...")
    
    # Test basic imports
    from fastapi import FastAPI
    print("✅ FastAPI import OK")
    
    from app.core.config import settings
    print("✅ Settings import OK")
    
    from app.core.database import engine, SessionLocal
    print("✅ Database import OK")
    
    # Test if we can create the FastAPI app
    app = FastAPI(title="Test App")
    print("✅ FastAPI app creation OK")
    
    print("🎉 All imports successful! Railway should be able to start the app.")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()