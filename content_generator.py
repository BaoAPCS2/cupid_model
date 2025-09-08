import json
import random

class ContentGenerator:
    def __init__(self, templates_path="templates.json"):
        """Khởi tạo và tải thư viện mẫu câu."""
        with open(templates_path, "r", encoding="utf-8") as f:
            self.templates = json.load(f)

    def _get_activity_category(self, quest, all_pois):
        """Lấy danh mục của hoạt động từ POI."""
        poi = next((p for p in all_pois if p["poi_id"] == quest["poi_id"]), None)
        return poi["category"] if poi else "default"
        
    def _generate_title(self, quest, all_pois, is_update=False):
        """Tạo tiêu đề dựa trên trạng thái và loại hoạt động."""
        if is_update:
            return random.choice(self.templates["titles"]["updated"]["default"])
        
        quest_type = quest.get("type", "main_activity")
        if quest_type == "buffer_activity":
            category = "buffer"
        else:
            category = self._get_activity_category(quest, all_pois)
            
        title_options = self.templates["titles"]["initial"].get(category, self.templates["titles"]["initial"]["default"])
        return random.choice(title_options)

    def _generate_description(self, quest, all_pois, is_update=False):
        """Tạo mô tả."""
        poi_name = next((p["name"] for p in all_pois if p["poi_id"] == quest["poi_id"]), "một địa điểm thú vị")
        
        if is_update:
            template = random.choice(self.templates["descriptions"]["updated"]["default"])
        else:
            quest_type = quest.get("type", "main_activity")
            template = random.choice(self.templates["descriptions"]["initial"][quest_type])
            
        return template.format(location_name=poi_name)

    def _generate_hint(self, quest, all_schedules, all_users):
        """Tạo gợi ý (hint) một cách thông minh."""
        # Ưu tiên 1: Dựa trên lịch trình của cặp đôi được nhắm đến
        if quest.get("associatedMatch"):
            match_id = quest["associatedMatch"]["match_id"]
            match_schedule = next((s for s in all_schedules if s["user_id"] == match_id), None)
            if match_schedule:
                activity_desc = match_schedule["description"]
                # Tìm hint khớp với mô tả hoạt động
                for key, hint in self.templates["hints"]["by_schedule_activity"].items():
                    if key.lower() in activity_desc.lower():
                        return hint
        
        # (Chưa có dữ liệu sở thích, sẽ dùng generic hint)
        # Ưu tiên 2: Dựa trên sở thích của cặp đôi (sẽ thêm ở tương lai)

        # Ưu tiên 3: Dùng một gợi ý chung chung
        return random.choice(self.templates["hints"]["generic"])

    def generate_quest_content(self, quest, all_pois, all_schedules, all_users, is_update=False):
        """
        Hàm chính, nhận vào một Quest struct và trả về một bộ nội dung.
        """
        # Để tạo hint tốt nhất, chúng ta cần biết cặp đôi được nhắm đến là ai.
        # Ta có thể tìm lại cặp đôi này bằng cách phân tích điểm bias_match, 
        # nhưng để đơn giản, ta sẽ giả định quest struct đã có thông tin này.
        # Trong lần chạy thử, ta sẽ tạo hint dựa trên lịch trình.

        title = self._generate_title(quest, all_pois, is_update)
        description = self._generate_description(quest, all_pois, is_update)
        hint = self._generate_hint(quest, all_schedules, all_users) # Cần cải thiện để biết match nào là mục tiêu

        return {
            "title": title,
            "description": description,
            "hint": hint
        }

# --- CÁCH SỬ DỤNG ---
if __name__ == "__main__":
    # Đây là một ví dụ sử dụng độc lập
    # 1. Giả lập dữ liệu đầu vào
    from activity_model_engine import load_data
    all_pois, all_users, all_schedules = load_data()
    
    # Giả sử đây là quest tốt nhất được thuật toán chọn
    sample_quest = {
        "candidate_id": "CANDIDATE_ALT_some_poi_id",
        "type": "main_activity",
        "poi_id": all_pois[0]["poi_id"], # Lấy POI đầu tiên làm ví dụ
        "associatedMatch": {"match_id": "USER_192"} # Giả định ta biết mục tiêu là USER_192
    }

    # 2. Khởi tạo và gọi generator
    generator = ContentGenerator()
    content = generator.generate_quest_content(sample_quest, all_pois, all_schedules, all_users)

    # 3. In kết quả
    print("--- VÍ DỤ TẠO NỘI DUNG ---")
    print(f"Tiêu đề: {content['title']}")
    print(f"Mô tả: {content['description']}")
    print(f"Gợi ý: {content['hint']}")