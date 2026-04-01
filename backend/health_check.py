#!/usr/bin/env python3
"""
Health check script for E Lost & Found backend.
Run this locally to verify all dependencies are installed and MongoDB is reachable.
"""

import sys
import os

def check_imports():
    """Check all required packages are installed."""
    print("✓ Checking imports...")
    required_packages = [
        "fastapi",
        "uvicorn",
        "pymongo",
        "pydantic",
        "jose",
        "passlib",
        "apscheduler",
        "boto3",
    ]
    
    missing = []
    for pkg in required_packages:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} (missing)")
            missing.append(pkg)
    
    if missing:
        print(f"\n✗ Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    return True


def check_env():
    """Check required environment variables."""
    print("\n✓ Checking environment variables...")
    from app.config import settings
    
    critical = {
        "MONGODB_URI": "MongoDB connection string",
        "JWT_SECRET": "JWT secret key",
    }
    
    warnings = {
        "AWS_ACCESS_KEY_ID": "AWS credentials (optional for dev)",
        "ADMIN_EMAILS": "Admin emails (optional)",
        "ADMIN_PANEL_PASSWORD": "Admin password (optional for dev)",
    }
    
    missing_critical = []
    for key, desc in critical.items():
        val = getattr(settings, key, None)
        if not val or val == "change-me-in-production":
            print(f"  ⚠ {key}: {desc}")
            missing_critical.append(key)
        else:
            print(f"  ✓ {key}: Set")
    
    for key, desc in warnings.items():
        val = getattr(settings, key, None)
        if not val:
            print(f"  ℹ {key}: {desc} (not set)")
        else:
            print(f"  ✓ {key}: Set")
    
    if missing_critical:
        print(f"\n✗ Missing critical config: {', '.join(missing_critical)}")
        return False
    return True


def check_mongodb():
    """Check MongoDB connection."""
    print("\n✓ Checking MongoDB connection...")
    try:
        from app.database import _get_client
        client = _get_client()
        client.server_info()
        print("  ✓ MongoDB connected")
        return True
    except Exception as e:
        print(f"  ✗ MongoDB connection failed: {e}")
        return False


def check_app():
    """Check FastAPI app loads."""
    print("\n✓ Checking FastAPI app...")
    try:
        from app.main import app
        print("  ✓ FastAPI app loaded")
        return True
    except Exception as e:
        print(f"  ✗ FastAPI app failed to load: {e}")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("E Lost & Found Backend - Health Check")
    print("=" * 60)
    
    # Change to backend directory
    if os.path.basename(os.getcwd()) != "backend":
        if os.path.exists("backend"):
            os.chdir("backend")
        else:
            print("✗ Must run from project root or backend/ directory")
            sys.exit(1)
    
    checks = [
        check_imports,
        check_env,
        check_mongodb,
        check_app,
    ]
    
    results = []
    for check in checks:
        try:
            results.append(check())
        except Exception as e:
            print(f"✗ Check failed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    if all(results):
        print("✓ All checks passed! Backend is ready.")
        print("\nTo start the server locally:")
        print("  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("\nThen visit: http://localhost:8000/docs")
        sys.exit(0)
    else:
        print("✗ Some checks failed. See above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
