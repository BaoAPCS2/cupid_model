import os, json
import firebase_admin
from firebase_admin import credentials, firestore

def init_firebase():
    if not firebase_admin._apps:  # tránh init nhiều lần
        if os.environ.get("FIREBASE_SERVICE_ACCOUNT"):
            # Deploy trên Render → đọc từ ENV
            key_data = json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])
            cred = credentials.Certificate(key_data)
        else:
            # Local dev → đọc file serviceAccountKey.json
            cred = credentials.Certificate("serviceAccountKey.json")

        firebase_admin.initialize_app(cred)
    return firestore.client()
