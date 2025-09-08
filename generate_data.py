import json
import random
import uuid
from datetime import datetime, timedelta

# --- 1. ĐỊNH NGHĨA KHÔNG GIAN ĐỊA LÝ (Giữ nguyên) ---
DISTRICT_BOUNDS = {
    "quan_1": {"lat_min": 10.76, "lat_max": 10.78, "lon_min": 106.69, "lon_max": 106.71},
    "quan_5": {"lat_min": 10.74, "lat_max": 10.76, "lon_min": 106.64, "lon_max": 106.67},
    "quan_10": {"lat_min": 10.76, "lat_max": 10.78, "lon_min": 106.66, "lon_max": 106.68}
}

def get_random_coords(district_name):
    bounds = DISTRICT_BOUNDS[district_name]
    lat = random.uniform(bounds["lat_min"], bounds["lat_max"])
    lon = random.uniform(bounds["lon_min"], bounds["lon_max"])
    return {"latitude": lat, "longitude": lon}

# --- 2. TẠO DỮ LIỆU ĐỊA ĐIỂM (POIs) - PHIÊN BẢN NÂNG CẤP VỚI DỮ LIỆU THẬT ---
def create_pois_real_data():
    """
    Tạo danh sách các địa điểm ưa thích (POIs) với tên và tọa độ thật (gần đúng).
    """
    pois = [
        # === QUẬN 1 ===
        # Cafes
        {"name": "The Coffee House - Nguyễn Huệ", "category": "cafe", "type": "indoor", "district": "quan_1", "latitude": 10.7719, "longitude": 106.7037},
        {"name": "Starbucks Reserve - Hàn Thuyên", "category": "cafe", "type": "indoor", "district": "quan_1", "latitude": 10.7794, "longitude": 106.6994},
        {"name": "Cộng Cà Phê - Lý Tự Trọng", "category": "cafe", "type": "indoor", "district": "quan_1", "latitude": 10.7766, "longitude": 106.7001},
        {"name": "Phúc Long - Mạc Thị Bưởi", "category": "cafe", "type": "indoor", "district": "quan_1", "latitude": 10.7735, "longitude": 106.7042},
        {"name": "L'Usine - Lê Thánh Tôn", "category": "cafe", "type": "indoor", "district": "quan_1", "latitude": 10.7769, "longitude": 106.7018},

        # Gyms
        {"name": "California Fitness & Yoga - Lim Tower", "category": "gym", "type": "indoor", "district": "quan_1", "latitude": 10.7801, "longitude": 106.7029},
        {"name": "Elite Fitness - Vincom Center", "category": "gym", "type": "indoor", "district": "quan_1", "latitude": 10.7781, "longitude": 106.7032},
        
        # Parks
        {"name": "Công viên 23/9", "category": "park", "type": "outdoor", "district": "quan_1", "latitude": 10.7699, "longitude": 106.6954},
        {"name": "Công viên Tao Đàn", "category": "park", "type": "outdoor", "district": "quan_1", "latitude": 10.7738, "longitude": 106.6936},
        
        # Cinemas
        {"name": "CGV Vincom Center Đồng Khởi", "category": "cinema", "type": "indoor", "district": "quan_1", "latitude": 10.7780, "longitude": 106.7033},
        {"name": "BHD Star Bitexco", "category": "cinema", "type": "indoor", "district": "quan_1", "latitude": 10.7716, "longitude": 106.7044},

        # === QUẬN 5 ===
        # Cafes
        {"name": "The Coffee House - An Dương Vương", "category": "cafe", "type": "indoor", "district": "quan_5", "latitude": 10.7588, "longitude": 106.6669},
        {"name": "Phin & Bean Roastery", "category": "cafe", "type": "indoor", "district": "quan_5", "latitude": 10.7554, "longitude": 106.6631},

        # Gyms
        {"name": "CitiGym - Hùng Vương Plaza", "category": "gym", "type": "indoor", "district": "quan_5", "latitude": 10.7599, "longitude": 106.6617},
        {"name": "Jetts 24h Fitness An Dương Vương", "category": "gym", "type": "indoor", "district": "quan_5", "latitude": 10.7585, "longitude": 106.6672},
        
        # Parks
        {"name": "Công viên Văn Lang", "category": "park", "type": "outdoor", "district": "quan_5", "latitude": 10.7562, "longitude": 106.6644},

        # Cinemas
        {"name": "CGV Hùng Vương Plaza", "category": "cinema", "type": "indoor", "district": "quan_5", "latitude": 10.7600, "longitude": 106.6618},
        
        # === QUẬN 10 ===
        # Cafes
        {"name": "Highlands Coffee - Vạn Hạnh Mall", "category": "cafe", "type": "indoor", "district": "quan_10", "latitude": 10.7744, "longitude": 106.6687},
        {"name": "The Coffee House - Sư Vạn Hạnh", "category": "cafe", "type": "indoor", "district": "quan_10", "latitude": 10.7730, "longitude": 106.6689},
        {"name": "Cheese Coffee - Sư Vạn Hạnh", "category": "cafe", "type": "indoor", "district": "quan_10", "latitude": 10.7712, "longitude": 106.6680},

        # Gyms
        {"name": "California Fitness & Yoga - Vạn Hạnh Mall", "category": "gym", "type": "indoor", "district": "quan_10", "latitude": 10.7745, "longitude": 106.6688},
        {"name": "Getfit Gym & Yoga", "category": "gym", "type": "indoor", "district": "quan_10", "latitude": 10.7780, "longitude": 106.6698},
        
        # Parks
        {"name": "Công viên Lê Thị Riêng", "category": "park", "type": "outdoor", "district": "quan_10", "latitude": 10.7836, "longitude": 106.6626}, # Gần Q10

        # Cinemas
        {"name": "CGV Sư Vạn Hạnh", "category": "cinema", "type": "indoor", "district": "quan_10", "latitude": 10.7746, "longitude": 106.6689},
    ]
    
    # Gán poi_id duy nhất cho mỗi địa điểm
    for poi in pois:
        poi["poi_id"] = str(uuid.uuid4())
        
    return pois


# --- CÁC HÀM create_users và create_schedules (Giữ nguyên như cũ) ---
def create_users(num_users=300):
    users = []
    for i in range(num_users):
        user_id = f"USER_{i:03d}"
        gender = "male" if i < num_users // 2 else "female"
        district = random.choice(list(DISTRICT_BOUNDS.keys()))
        
        users.append({
            "user_id": user_id,
            "gender": gender,
            "home_location": get_random_coords(district),
            "match_list": [] 
        })

    male_ids = [u["user_id"] for u in users if u["gender"] == "male"]
    female_ids = [u["user_id"] for u in users if u["gender"] == "female"]

    for user in users:
        num_matches = random.randint(3, 7)
        if user["gender"] == "male":
            potential_partners = random.sample(female_ids, min(len(female_ids), num_matches))
        else:
            potential_partners = random.sample(male_ids, min(len(male_ids), num_matches))
        
        for partner_id in potential_partners:
            user["match_list"].append({
                "match_id": partner_id,
                "score": round(random.uniform(0.3, 1.0), 2)
            })
    return users

def create_schedules(users, pois):
    schedules = []
    activities_by_category = {
        "gym": ["Tập gym", "Tập yoga", "Cardio"],
        "cafe": ["Uống cà phê", "Gặp gỡ bạn bè", "Làm việc tại quán cafe"],
        "park": ["Chạy bộ", "Đi dạo", "Ngồi thư giãn"],
        "cinema": ["Xem phim"]
    }
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    for user in users:
        num_todos = random.randint(1, 3)
        for _ in range(num_todos):
            category = random.choice(list(activities_by_category.keys()))
            possible_pois = [p for p in pois if p["category"] == category]
            if not possible_pois:
                continue

            chosen_poi = random.choice(possible_pois)
            description = random.choice(activities_by_category[category])
            
            start_hour = random.choice([8, 9, 10, 14, 15, 18, 19, 20])
            start_time = today + timedelta(hours=start_hour, minutes=random.choice([0, 30]))
            end_time = start_time + timedelta(hours=random.choice([1, 1.5, 2]))

            schedules.append({
                "schedule_id": str(uuid.uuid4()),
                "user_id": user["user_id"],
                "description": description,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "poi_id": chosen_poi["poi_id"],
                "location": {
                    "latitude": chosen_poi["latitude"],
                    "longitude": chosen_poi["longitude"]
                }
            })
    return schedules

# --- HÀM CHÍNH ĐỂ THỰC THI (Cập nhật để gọi hàm mới) ---
if __name__ == "__main__":
    print("Bắt đầu Giai đoạn 0 của Kế hoạch Gió Lốc (Phiên bản Dữ liệu Thật)...")

    # Bước 1: Tạo POIs với dữ liệu thật
    pois_data = create_pois_real_data() # <--- THAY ĐỔI Ở ĐÂY
    with open("pois.json", "w", encoding="utf-8") as f:
        json.dump(pois_data, f, indent=4, ensure_ascii=False)
    print(f"-> Đã tạo thành công file 'pois.json' với {len(pois_data)} địa điểm THẬT.")

    # Bước 2: Tạo Users (giữ nguyên)
    users_data = create_users()
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users_data, f, indent=4, ensure_ascii=False)
    print(f"-> Đã tạo thành công file 'users.json' với {len(users_data)} người dùng.")

    # Bước 3: Tạo Schedules (giữ nguyên, nhưng sẽ sử dụng POIs thật)
    schedules_data = create_schedules(users_data, pois_data)
    with open("daily_schedules.json", "w", encoding="utf-8") as f:
        json.dump(schedules_data, f, indent=4, ensure_ascii=False)
    print(f"-> Đã tạo thành công file 'daily_schedules.json' với {len(schedules_data)} lịch trình.")

    print("\nHoàn thành xuất sắc Giai đoạn 0!")