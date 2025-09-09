import json
import os
from flask import Flask, request, jsonify
import traceback

# Import các thành phần cốt lõi từ các file của chúng ta
from activity_model_engine import (
    load_data,
    generate_quest_candidates,
    score_quest
)
from content_generator import ContentGenerator
from run_scenarios import find_optimal_scenario

# --- 1. KHỞI TẠO ỨNG DỤNG VÀ TẢI DỮ LIỆU ---

print("Khởi động API Server cho Kế hoạch Gió Lốc...")

app = Flask(__name__)

# Tải toàn bộ dữ liệu mô phỏng MỘT LẦN DUY NHẤT khi server khởi động
# Điều này giúp API phản hồi nhanh hơn vì không phải đọc file mỗi lần có yêu cầu
all_pois, all_users, all_schedules = load_data()
content_gen = ContentGenerator()

print("-> Dữ liệu và Content Generator đã được tải và sẵn sàng!")


# --- 2. ĐỊNH NGHĨA API ENDPOINT ---

@app.route('/suggest', methods=['POST'])
def suggest_activity():
    """
    Đây là endpoint chính để nhận yêu cầu và trả về gợi ý.
    """
    print("\nNhận được yêu cầu mới tại /suggest...")

    # --- 2a. Nhận và kiểm tra dữ liệu đầu vào ---
    try:
        input_data = request.get_json()
        user_id = input_data['user_id']
        original_todo = input_data['todo'] # Mong muốn có cấu trúc giống như trong daily_schedules.json
        print(f"Yêu cầu cho người dùng: {user_id}")
        print(f"Với to-do: {original_todo['description']}")
    except (TypeError, KeyError) as e:
        print(f"Lỗi: Dữ liệu đầu vào không hợp lệ - {e}")
        # Trả về lỗi 400 Bad Request
        return jsonify({"error": "Dữ liệu đầu vào không hợp lệ. Cần có 'user_id' và 'todo'."}), 400

    # --- 2b. Tìm hồ sơ người dùng ---
    user_profile = next((u for u in all_users if u["user_id"] == user_id), None)
    if not user_profile:
        print(f"Lỗi: Không tìm thấy người dùng với ID: {user_id}")
        return jsonify({"error": f"Không tìm thấy người dùng với ID: {user_id}"}), 404

    # --- 2c. Chạy lõi mô hình ---
    try:
        # Tạo ứng viên
        candidates = generate_quest_candidates(original_todo, all_pois, user_profile, all_schedules, all_users)
        
        # Chấm điểm
        scored_candidates = []
        for cand in candidates:
            final_score, breakdown = score_quest(cand, original_todo, user_profile, all_schedules, all_users)
            cand['final_score'] = final_score
            cand['scores_breakdown'] = breakdown
            scored_candidates.append(cand)
            
        # Sắp xếp
        sorted_candidates = sorted(scored_candidates, key=lambda x: x['final_score'], reverse=True)
        
        # Lấy top 3 gợi ý
        top_3_suggestions = sorted_candidates[:3]

    except Exception as e:
        print(f"Lỗi trong quá trình xử lý của mô hình: {e}")
        traceback.print_exc() 
        return jsonify({"error": str(e)}), 500

    # --- 2d. Tạo nội dung và định dạng output ---
    response_data = []
    for quest_struct in top_3_suggestions:
        # Tìm lại cặp đôi mục tiêu cho mỗi gợi ý để tạo hint tốt nhất
        # (Logic này có thể được tối ưu hóa trong tương lai)
        from run_scenarios import find_target_match_for_quest # Tạm thời import từ đây
        target_match = find_target_match_for_quest(quest_struct, user_profile, all_schedules, all_users)
        quest_struct['associatedMatch'] = target_match
        
        # Tạo nội dung
        content = content_gen.generate_quest_content(quest_struct, all_pois, all_schedules, all_users)
        
        # Đóng gói kết quả
        response_data.append({
            "quest_details": quest_struct, # Giữ lại dữ liệu gốc để debug hoặc dùng ở client
            "display_content": content     # Dữ liệu sạch để hiển thị
        })

    print(f"-> Đã xử lý xong. Trả về {len(response_data)} gợi ý.")
    return jsonify(response_data)


@app.route('/match', methods=['GET'])
def find_match():
    """Trả về một cặp đôi phù hợp nhất (nếu có)."""
    try:
        user_A, todo_A, match_B, schedule_B = find_optimal_scenario(all_users, all_schedules, all_pois)

        if not user_A:
            return jsonify({"message": "Không tìm thấy cặp đôi phù hợp"}), 200

        return jsonify({
            "user_A": user_A,
            "todo_A": todo_A,
            "match_B": match_B,
            "schedule_B": schedule_B
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# --- 3. CHẠY SERVER ---

if __name__ == '__main__':
    # Chạy server ở chế độ debug để dễ dàng theo dõi lỗi
    # Host '0.0.0.0' cho phép truy cập từ các thiết bị khác trong cùng mạng
    port = int(os.getenv("PORT", "5000"))
    app.run(host='0.0.0.0', port=port, debug=True)