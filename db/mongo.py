from pymongo import MongoClient
from datetime import datetime, timezone
from bson import ObjectId

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "nexus_rag"

_client = None

def get_db():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    return _client[DB_NAME]

def save_message(session_id: str, role: str, content: str):
    db = get_db()
    db.messages.insert_one({
        "session_id": session_id,
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc),
    })
    db.sessions.update_one(
        {"_id": session_id},
        {
            "$set": {"updated_at": datetime.now(timezone.utc)},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc), "title": content[:60]},
        },
        upsert=True,
    )

def get_sessions():
    db = get_db()
    sessions = list(db.sessions.find().sort("updated_at", -1))
    for s in sessions:
        s["id"] = s.pop("_id")
    return sessions

def get_session_messages(session_id: str):
    db = get_db()
    msgs = list(db.messages.find({"session_id": session_id}).sort("timestamp", 1))
    for m in msgs:
        m["id"] = str(m.pop("_id"))
        m["timestamp"] = m["timestamp"].isoformat()
    return msgs

def delete_session(session_id: str):
    db = get_db()
    db.messages.delete_many({"session_id": session_id})
    db.sessions.delete_one({"_id": session_id})

def get_stats():
    db = get_db()
    pipeline = [
        {"$group": {
            "_id": {
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                "role": "$role"
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.date": 1}}
    ]
    raw = list(db.messages.aggregate(pipeline))

    days = {}
    for r in raw:
        d = r["_id"]["date"]
        role = r["_id"]["role"]
        if d not in days:
            days[d] = {"user": 0, "assistant": 0}
        days[d][role] = r["count"]

    total_sessions = db.sessions.count_documents({})
    total_messages = db.messages.count_documents({})

    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "daily": [{"date": d, **v} for d, v in sorted(days.items())],
    }
