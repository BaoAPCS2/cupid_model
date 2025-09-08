import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. Kết nối Firebase ---
cred = credentials.Certificate("serviceAccountKey.json")  # 🔑 file key tải về
firebase_admin.initialize_app(cred)
db = firestore.client()

def upsert(col, id_field, items):
    batch = db.batch()
    for it in items:
        doc_id = it.get(id_field) or it.get("id")
        if not doc_id:
            raise ValueError(f"Missing {id_field} in item: {it}")
        ref = db.collection(col).document(doc_id)
        batch.set(ref, it, merge=True)  # merge=True để update nếu có sẵn
    batch.commit()
    print(f"✅ Imported {len(items)} docs into '{col}'")

# --- 2. Đọc dữ liệu từ file JSON ---
with open("pois.json","r",encoding="utf-8") as f:
    pois = json.load(f)

with open("users.json","r",encoding="utf-8") as f:
    users = json.load(f)

with open("daily_schedules.json","r",encoding="utf-8") as f:
    schedules = json.load(f)

# --- 3. Upload lên Firestore ---
upsert("pois", "poi_id", pois)
upsert("users", "user_id", users)
upsert("daily_schedules", "schedule_id", schedules)

print("🎉 Done! All data migrated to Firestore.")
