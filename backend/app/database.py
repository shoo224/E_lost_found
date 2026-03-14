# database.py - MongoDB connection and collection helpers
# We connect lazily (on first use) so the app starts even before .env has a real MongoDB URI.

from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from app.config import settings

# Lazy: only connect when first needed (avoids DNS/connection error at import if URI is placeholder)
_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def _get_client() -> MongoClient:
    global _client
    if _client is None:
        uri = settings.MONGODB_URI
        if "xxxxx" in uri or "USER:PASSWORD" in uri:
            # Likely placeholder; avoid DNS lookup and give a clear message
            raise RuntimeError(
                "Set MONGODB_URI in backend/.env to your MongoDB Atlas connection string. "
                "Get it from MongoDB Atlas > Connect > Connect your application. "
                "Replace USER, PASSWORD, and the cluster host (e.g. cluster0.xxxxx.mongodb.net) with your values."
            )
        _client = MongoClient(uri)
    return _client


def _get_db() -> Database:
    global _db
    if _db is None:
        _db = _get_client()[settings.DB_NAME]
    return _db


def get_collection(name: str) -> Collection:
    """Return a MongoDB collection by name. Use for users, lost_items, found_items, claims, otp_store."""
    return _get_db()[name]


def users_collection() -> Collection:
    return _get_db()["users"]


def lost_items_collection() -> Collection:
    return _get_db()["lost_items"]


def found_items_collection() -> Collection:
    return _get_db()["found_items"]


def claims_collection() -> Collection:
    return _get_db()["claims"]


def otp_store_collection() -> Collection:
    return _get_db()["otp_store"]
