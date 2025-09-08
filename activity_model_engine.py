import json
import os
from datetime import datetime
from geopy.distance import geodesic
import numpy as np
import random

# --- 0. HÀM HỖ TRỢ ĐỂ TẢI DỮ LIỆU ---
def load_data():
    """
    Nếu USE_FIREBASE=1 -> đọc Firestore.
    Ngược lại -> fallback đọc từ JSON local.
    """
    if os.getenv("USE_FIREBASE", "0") == "1":
        print("🔗 Loading data from Firestore...")
        from firebase_client import init_firebase
        db = init_firebase()

        # POIs
        pois = []
        for doc in db.collection("pois").stream():
            d = doc.to_dict()
            d.setdefault("poi_id", doc.id)
            pois.append(d)

        # Users
        users = []
        for doc in db.collection("users").stream():
            d = doc.to_dict()
            d.setdefault("user_id", doc.id)
            users.append(d)

        # Schedules
        schedules = []
        for doc in db.collection("daily_schedules").stream():
            d = doc.to_dict()
            d.setdefault("schedule_id", doc.id)
            # Chuẩn hoá timestamp Firestore
            for k in ("start_time", "end_time"):
                v = d.get(k)
                if hasattr(v, "isoformat"):  # Firestore Timestamp
                    d[k] = v.isoformat()
            schedules.append(d)

        return pois, users, schedules

    else:
        print("📂 Loading data from local JSON...")
        with open("pois.json", "r", encoding="utf-8") as f:
            pois = json.load(f)
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
        with open("daily_schedules.json", "r", encoding="utf-8") as f:
            schedules = json.load(f)
        return pois, users, schedules

# --- 1. CÁC HÀM TÍNH TOÁN THÀNH PHẦN ---

def calculate_time_overlap(start_time1, end_time1, start_time2, end_time2):
    """
    Tính điểm chồng chéo thời gian (sim_time) giữa hai khoảng thời gian.
    Trả về điểm từ 0 đến 1.
    """
    st1, et1 = datetime.fromisoformat(start_time1), datetime.fromisoformat(end_time1)
    st2, et2 = datetime.fromisoformat(start_time2), datetime.fromisoformat(end_time2)
    overlap_start = max(st1, st2)
    overlap_end = min(et1, et2)
    if overlap_start >= overlap_end:
        return 0.0
    overlap_duration = (overlap_end - overlap_start).total_seconds()
    duration1 = (et1 - st1).total_seconds()
    duration2 = (et2 - st2).total_seconds()
    score = overlap_duration / max(duration1, duration2) if max(duration1, duration2) > 0 else 0
    return score

def calculate_location_score(loc1, loc2, radius_km=5):
    """
    Tính điểm địa điểm (sim_loc) dựa trên khoảng cách.
    Trả về điểm từ 0 đến 1.
    """
    coords1 = (loc1['latitude'], loc1['longitude'])
    coords2 = (loc2['latitude'], loc2['longitude'])
    distance_km = geodesic(coords1, coords2).kilometers
    score = np.exp(-distance_km / radius_km)
    return score

# --- 2. HÀM TẠO ỨNG VIÊN NHIỆM VỤ (PHIÊN BẢN NÂNG CẤP) ---

def find_best_potential_match(original_todo, user_profile, all_schedules, all_users):
    """
    Tìm ra cặp đôi có tiềm năng gặp gỡ cao nhất cho một to-do cụ thể.
    Trả về (match_info, target_schedule) hoặc (None, None).
    """
    user = next((u for u in all_users if u["user_id"] == user_profile["user_id"]), None)
    if not user:
        return None, None
    best_match_info = None
    best_target_schedule = None
    max_potential_score = 0.0
    for match in user["match_list"]:
        match_id = match["match_id"]
        match_score = match["score"]
        match_schedules_today = [s for s in all_schedules if s["user_id"] == match_id]
        for match_schedule in match_schedules_today:
            location_overlap = calculate_location_score(original_todo["location"], match_schedule["location"])
            potential_score = match_score * location_overlap
            if potential_score > max_potential_score:
                max_potential_score = potential_score
                best_match_info = match
                best_target_schedule = match_schedule
    if max_potential_score > 0.5:
        return best_match_info, best_target_schedule
    return None, None

def generate_quest_candidates(original_todo, all_pois, user_profile, all_schedules, all_users, radius_km=5):
    """
    Tạo danh sách các nhiệm vụ ứng viên từ một to-do gốc,
    bao gồm cả các hoạt động đệm giao thoa.
    """
    candidates = []
    poi_goc = next((p for p in all_pois if p["poi_id"] == original_todo["poi_id"]), None)
    if not poi_goc:
        return []

    # CHIẾN LƯỢC 1: GIỮ NGUYÊN TRẠNG
    candidates.append({
        "candidate_id": "CANDIDATE_BASE", "type": "main_activity",
        "origin_todo_id": original_todo["schedule_id"], "start_time": original_todo["start_time"],
        "end_time": original_todo["end_time"], "poi_id": original_todo["poi_id"], "location": original_todo["location"]
    })

    # CHIẾN LƯỢC 2: THAY THẾ ĐỊA ĐIỂM CÙNG LOẠI
    category_goc = poi_goc["category"]
    user_location = user_profile["home_location"]
    for poi in all_pois:
        if poi["category"] == category_goc and poi["poi_id"] != poi_goc["poi_id"]:
            coords_user = (user_location['latitude'], user_location['longitude'])
            coords_poi = (poi['latitude'], poi['longitude'])
            if geodesic(coords_user, coords_poi).kilometers <= radius_km:
                candidates.append({
                    "candidate_id": f"CANDIDATE_ALT_{poi['poi_id']}", "type": "main_activity",
                    "origin_todo_id": original_todo["schedule_id"], "start_time": original_todo["start_time"],
                    "end_time": original_todo["end_time"], "poi_id": poi["poi_id"],
                    "location": {"latitude": poi["latitude"], "longitude": poi["longitude"]}
                })

    # CHIẾN LƯỢC 4: GỢI Ý HOẠT ĐỘNG ĐỆM GIAO THOA
    target_match, target_schedule = find_best_potential_match(original_todo, user_profile, all_schedules, all_users)
    if target_match:
        target_poi = next((p for p in all_pois if p["poi_id"] == target_schedule["poi_id"]), None)
        if target_poi and target_poi["category"] != category_goc:
            LIGHTWEIGHT_CATEGORIES = ['cafe', 'convenience_store', 'tea_house', 'bookstore']
            target_coords = (target_poi['latitude'], target_poi['longitude'])
            for poi in all_pois:
                if poi["category"] in LIGHTWEIGHT_CATEGORIES:
                    poi_coords = (poi['latitude'], poi['longitude'])
                    if geodesic(target_coords, poi_coords).kilometers <= 0.2:
                        original_start_time = datetime.fromisoformat(original_todo["start_time"])
                        buffer_start_time = original_start_time - timedelta(minutes=30)
                        buffer_end_time = original_start_time - timedelta(minutes=5)
                        candidates.append({
                            "candidate_id": f"CANDIDATE_BUFFER_{poi['poi_id']}", "type": "buffer_activity",
                            "origin_todo_id": original_todo["schedule_id"], "start_time": buffer_start_time.isoformat(),
                            "end_time": buffer_end_time.isoformat(), "poi_id": poi["poi_id"],
                            "location": {"latitude": poi["latitude"], "longitude": poi["longitude"]}
                        })
    return candidates

# --- 3. CÁC HÀM CHẤM ĐIỂM ---

def calculate_match_bias(quest_candidate, user_profile, all_schedules, all_users):
    """
    Tính điểm thiên vị hẹn hò (bias_match) cho một nhiệm vụ.
    """
    total_bias_score = 0.0
    user = next((u for u in all_users if u["user_id"] == user_profile["user_id"]), None)
    if not user:
        return 0.0
    for match in user["match_list"]:
        match_id = match["match_id"]
        match_score = match["score"]
        match_schedules_today = [s for s in all_schedules if s["user_id"] == match_id]
        if match_schedules_today:
            best_overlap_for_this_match = 0
            for match_schedule in match_schedules_today:
                time_overlap = calculate_time_overlap(
                    quest_candidate["start_time"], quest_candidate["end_time"],
                    match_schedule["start_time"], match_schedule["end_time"]
                )
                location_overlap = calculate_location_score(quest_candidate["location"], match_schedule["location"])
                overlap_score = 0.5 * time_overlap + 0.5 * location_overlap
                if overlap_score > best_overlap_for_this_match:
                    best_overlap_for_this_match = overlap_score
            potential_score = match_score * best_overlap_for_this_match
            total_bias_score += potential_score
    return total_bias_score

def score_quest(quest_candidate, original_todo, user_profile, all_schedules, all_users):
    """
    Tính điểm tổng hợp cuối cùng cho một ứng viên nhiệm vụ.
    """
    W_TIME = 0.25
    W_LOC = 0.2
    W_BIAS = 0.55

    # Điều chỉnh `sim_time` và `sim_loc` cho hoạt động đệm
    if quest_candidate.get("type") == "buffer_activity":
        # Hoạt động đệm không nên bị phạt vì thời gian khác.
        # Ta có thể coi sim_time là 1 nếu nó nằm ngay trước hoạt động chính.
        sim_time = 0.9 # Điểm cố định, hơi thấp hơn 1 để ưu tiên hoạt động chính
        # sim_loc so sánh sự thuận tiện của tuyến đường: vị trí đệm so với vị trí gốc
        sim_loc = calculate_location_score(quest_candidate["location"], original_todo["location"], radius_km=2) # Bán kính nhỏ hơn
    else: # Hoạt động chính
        sim_time = calculate_time_overlap(
            quest_candidate["start_time"], quest_candidate["end_time"],
            original_todo["start_time"], original_todo["end_time"]
        )
        sim_loc = calculate_location_score(quest_candidate["location"], original_todo["location"])

    bias_match = calculate_match_bias(quest_candidate, user_profile, all_schedules, all_users)
    final_score = (W_TIME * sim_time) + (W_LOC * sim_loc) + (W_BIAS * bias_match)
    
    scores_breakdown = {"sim_time": sim_time, "sim_loc": sim_loc, "bias_match": bias_match}
    return final_score, scores_breakdown

# --- HÀM CHÍNH ĐỂ CHẠY THỬ NGHIỆM ---
if __name__ == "__main__":
    print("Bắt đầu Giai đoạn 1 (Nâng cấp) của Kế hoạch Gió Lốc: Xây Dựng Lõi Mô Hình...")
    all_pois, all_users, all_schedules = load_data()
    print("-> Đã tải thành công dữ liệu từ các file JSON.")

    test_user_profile = random.choice(all_users)
    user_schedule = [s for s in all_schedules if s["user_id"] == test_user_profile["user_id"]]
    
    if not user_schedule:
        print(f"Người dùng {test_user_profile['user_id']} được chọn không có lịch trình. Vui lòng chạy lại.")
    else:
        test_todo = random.choice(user_schedule)
        print(f"\n--- Thử nghiệm với người dùng: {test_user_profile['user_id']} ---")
        print(f"To-Do Gốc: '{test_todo['description']}' lúc {datetime.fromisoformat(test_todo['start_time']).strftime('%H:%M')}")
        poi_goc_name = next((p["name"] for p in all_pois if p["poi_id"] == test_todo["poi_id"]), "Không rõ")
        print(f"Tại: {poi_goc_name}")

        # CẬP NHẬT LỜI GỌI HÀM
        candidates = generate_quest_candidates(test_todo, all_pois, test_user_profile, all_schedules, all_users)
        print(f"\n-> Đã tạo ra {len(candidates)} ứng viên nhiệm vụ (bao gồm cả hoạt động đệm nếu có).")

        scored_candidates = []
        for cand in candidates:
            final_score, breakdown = score_quest(cand, test_todo, test_user_profile, all_schedules, all_users)
            cand['final_score'] = final_score
            cand['scores_breakdown'] = breakdown
            scored_candidates.append(cand)
            
        sorted_candidates = sorted(scored_candidates, key=lambda x: x['final_score'], reverse=True)

        print("\n--- KẾT QUẢ GỢI Ý (TOP 5) ---")
        for i, quest in enumerate(sorted_candidates[:5]):
            poi_name = next((p["name"] for p in all_pois if p["poi_id"] == quest["poi_id"]), "Không rõ")
            quest_type = f"({quest.get('type', 'main_activity')})"
            print(f"\n{i+1}. Gợi ý đến: {poi_name} {quest_type}")
            print(f"   - Thời gian: {datetime.fromisoformat(quest['start_time']).strftime('%H:%M')}")
            print(f"   - Điểm tổng hợp: {quest['final_score']:.4f}")
            print(f"   - Chi tiết điểm: time={quest['scores_breakdown']['sim_time']:.2f}, loc={quest['scores_breakdown']['sim_loc']:.2f}, bias={quest['scores_breakdown']['bias_match']:.2f}")

    print("\nHoàn thành Giai đoạn 1 (Nâng cấp)!")