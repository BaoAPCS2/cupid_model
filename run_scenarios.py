import json
from datetime import datetime
from geopy.distance import geodesic

# Import các hàm từ file engine của chúng ta
from activity_model_engine import (
    load_data,
    generate_quest_candidates,
    score_quest
)
# Import module tạo nội dung mới
from content_generator import ContentGenerator

def find_optimal_scenario(users, schedules, pois, min_match_score=0.85, max_distance_km=1.5):
    """Tự động tìm kiếm trong bộ dữ liệu để tìm một kịch bản tối ưu."""
    for user_A in users:
        schedules_A = [s for s in schedules if s["user_id"] == user_A["user_id"]]
        if not schedules_A: continue
        for todo_A in schedules_A:
            if not user_A["match_list"]: continue
            top_match = max(user_A["match_list"], key=lambda x: x["score"], default=None)
            if top_match and top_match["score"] >= min_match_score:
                match_B_id = top_match["match_id"]
                schedules_B = [s for s in schedules if s["user_id"] == match_B_id]
                if not schedules_B: continue
                for schedule_B in schedules_B:
                    dist = geodesic((todo_A["location"]["latitude"], todo_A["location"]["longitude"]), (schedule_B["location"]["latitude"], schedule_B["location"]["longitude"])).kilometers
                    if dist <= max_distance_km:
                        time_diff = abs(datetime.fromisoformat(todo_A["start_time"]) - datetime.fromisoformat(schedule_B["start_time"]))
                        if time_diff.total_seconds() / 3600 <= 2:
                            return user_A, todo_A, top_match, schedule_B
    return None, None, None, None

def find_target_match_for_quest(quest, user_A, all_schedules, all_users):
    """
    Phân tích một quest để tìm ra cặp đôi mục tiêu chính (người đóng góp nhiều nhất vào điểm bias).
    """
    best_match_id = None
    max_contribution = 0
    
    for match in user_A["match_list"]:
        match_id = match["match_id"]
        match_score = match["score"]
        match_schedules_today = [s for s in all_schedules if s["user_id"] == match_id]
        if match_schedules_today:
            best_overlap = 0
            for schedule in match_schedules_today:
                # Tính lại overlap
                from activity_model_engine import calculate_time_overlap, calculate_location_score
                time_o = calculate_time_overlap(quest["start_time"], quest["end_time"], schedule["start_time"], schedule["end_time"])
                loc_o = calculate_location_score(quest["location"], schedule["location"])
                overlap = 0.5 * time_o + 0.5 * loc_o
                if overlap > best_overlap:
                    best_overlap = overlap
            
            contribution = match_score * best_overlap
            if contribution > max_contribution:
                max_contribution = contribution
                best_match_id = match_id
                
    return {"match_id": best_match_id} if best_match_id else None

if __name__ == "__main__":
    print("Bắt đầu Giai đoạn 2 & 2.5 của Kế hoạch Gió Lốc: Kiểm tra và Tạo Nội dung...")
    
    all_pois, all_users, all_schedules = load_data()
    content_gen = ContentGenerator() # Khởi tạo Content Generator
    print("-> Đã tải thành công dữ liệu và khởi tạo Content Generator.")

    print("\n--- [Kịch bản 1: Tình huống Tối ưu] ---")
    print("Đang tìm kiếm một cặp đôi hoàn hảo trong bộ dữ liệu...")

    user_A, todo_A, match_B, schedule_B = find_optimal_scenario(all_users, all_schedules, all_pois)

    if not user_A:
        print("Không tìm thấy kịch bản tối ưu trong lần chạy này.")
    else:
        # ... (Phần print thông tin kịch bản giữ nguyên) ...
        poi_A_name = next((p["name"] for p in all_pois if p["poi_id"] == todo_A["poi_id"]), "Không rõ")
        poi_B_name = next((p["name"] for p in all_pois if p["poi_id"] == schedule_B["poi_id"]), "Không rõ")
        print("\n*** Đã tìm thấy kịch bản phù hợp! ***")
        print(f"Người dùng A: {user_A['user_id']}")
        print(f"  -> Kế hoạch: '{todo_A['description']}' lúc {datetime.fromisoformat(todo_A['start_time']).strftime('%H:%M')} tại '{poi_A_name}'")
        print(f"Cặp đôi tiềm năng B: {match_B['match_id']} (Điểm hợp gu: {match_B['score']})")
        print(f"  -> Kế hoạch: '{schedule_B['description']}' lúc {datetime.fromisoformat(schedule_B['start_time']).strftime('%H:%M')} tại '{poi_B_name}'")

        print("\n-> Chạy mô hình gợi ý cho Người dùng A...")
        candidates = generate_quest_candidates(todo_A, all_pois, user_A, all_schedules, all_users)
        
        scored_candidates = []
        for cand in candidates:
            final_score, breakdown = score_quest(cand, todo_A, user_A, all_schedules, all_users)
            cand['final_score'] = final_score
            cand['scores_breakdown'] = breakdown
            scored_candidates.append(cand)
            
        sorted_candidates = sorted(scored_candidates, key=lambda x: x['final_score'], reverse=True)

        print("\n--- KẾT QUẢ GỢI Ý (ĐÃ CHUYỂN THÀNH NỘI DUNG) ---")
        top_suggestion = sorted_candidates[0]
        
        # Tìm cặp đôi mục tiêu để tạo hint tốt nhất
        target_match = find_target_match_for_quest(top_suggestion, user_A, all_schedules, all_users)
        top_suggestion['associatedMatch'] = target_match

        # Tạo nội dung
        generated_content = content_gen.generate_quest_content(top_suggestion, all_pois, all_schedules, all_users)

        print("\n=======================================================")
        print(f"  Tiêu đề: {generated_content['title']}")
        print(f"  Mô tả: {generated_content['description']}")
        print(f"  Gợi ý: {generated_content['hint']}")
        print("=======================================================")
        print(f"(Debug Info: Điểm tổng hợp: {top_suggestion['final_score']:.4f}, bias: {top_suggestion['scores_breakdown']['bias_match']:.2f})")

        # ... (Phần Kịch bản 2 sẽ được thêm vào đây) ...
# ... (Phần Kịch bản 1 vẫn giữ nguyên ở trên, kết thúc bằng dòng print Debug Info) ...

        
        # --- KỊCH BẢN 2: KIỂM TRA TÌNH HUỐNG DỰ PHÒNG (FALLBACK) ---
        print("\n\n--- [Kịch bản 2: Tình huống Dự phòng (Fallback)] ---")
        print(f"Giả lập tình huống Cặp đôi tiềm năng ({match_B['match_id']}) không thể tham gia...")

        # 1. Giả lập bằng cách tạm thời loại bỏ lịch trình của match_B
        schedules_without_match_B = [s for s in all_schedules if s["user_id"] != match_B['match_id']]

        # 2. Chạy lại mô hình gợi ý cho An với dữ liệu mới
        print("\n-> Chạy lại mô hình gợi ý cho Người dùng A...")
        
        candidates_fallback = generate_quest_candidates(todo_A, all_pois, user_A, schedules_without_match_B, all_users)
        
        scored_candidates_fallback = []
        for cand in candidates_fallback:
            final_score, breakdown = score_quest(cand, todo_A, user_A, schedules_without_match_B, all_users)
            cand['final_score'] = final_score
            cand['scores_breakdown'] = breakdown
            scored_candidates_fallback.append(cand)

        sorted_candidates_fallback = sorted(scored_candidates_fallback, key=lambda x: x['final_score'], reverse=True)

        print("\n--- KẾT QUẢ GỢI Ý MỚI (SAU KHI FALLBACK, ĐÃ CHUYỂN THÀNH NỘI DUNG) ---")
        if sorted_candidates_fallback:
            top_fallback_suggestion = sorted_candidates_fallback[0]
            
            # Tìm cặp đôi mục tiêu mới (nếu có)
            new_target_match = find_target_match_for_quest(top_fallback_suggestion, user_A, schedules_without_match_B, all_users)
            top_fallback_suggestion['associatedMatch'] = new_target_match

            # Tạo nội dung cập nhật, truyền vào is_update=True
            fallback_content = content_gen.generate_quest_content(
                top_fallback_suggestion, 
                all_pois, 
                schedules_without_match_B, 
                all_users, 
                is_update=True # <-- ĐÂY LÀ THAM SỐ QUAN TRỌNG
            )

            print("\n=======================================================")
            print(f"  Tiêu đề: {fallback_content['title']}")
            print(f"  Mô tả: {fallback_content['description']}")
            print(f"  Gợi ý: {fallback_content['hint']}")
            print("=======================================================")
            print(f"(Debug Info: Điểm tổng hợp: {top_fallback_suggestion['final_score']:.4f}, bias: {top_fallback_suggestion['scores_breakdown']['bias_match']:.2f})")
            
            print("\n--- Phân tích kết quả Fallback ---")
            # Phân tích này vẫn giữ nguyên để kiểm tra logic
            if top_fallback_suggestion['scores_breakdown']['bias_match'] < top_suggestion['scores_breakdown']['bias_match']:
                 print("=> THÀNH CÔNG! Điểm bias_match đã giảm, cho thấy mô hình đã nhận ra cơ hội với cặp đôi B không còn nữa.")
            
            if top_fallback_suggestion['candidate_id'] == "CANDIDATE_BASE":
                print("=> HÀNH VI ĐÚNG! Mô hình đã quaypip install Flask trở về gợi ý kế hoạch gốc vì đó là phương án an toàn nhất.")
            else:
                new_bias = top_fallback_suggestion['scores_breakdown']['bias_match']
                if new_bias > 0.1:
                     print(f"=> HÀNH VI THÔNG MINH! Mô hình đã tìm thấy một cơ hội khác (bias={new_bias:.2f}) và tối ưu lại.")
        else:
            print("Không có gợi ý nào được tạo ra sau khi fallback.")

# ... (Dòng print cuối cùng nằm ở đây) ...

    print("\nHoàn thành Giai đoạn 2.5 (phần 1).")

