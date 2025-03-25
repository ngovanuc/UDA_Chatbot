SUMMARIZER_SYSTEM = """Nhiệm vụ của bạn là tóm tắt lịch sử  đoạn tin nhắn trước đây trong cuộc trò chuyện giữa AI và người dùng.
Bạn sẽ nhận đoạn tin nhắn trong hai dấu ```
Cuộc trò chuyện được cung cấp từ ngữ cảnh và có thể không hoàn chỉnh.
Các tin nhắn do AI gửi được đánh dấu với vai trò 'assistant'.
Tin nhắn người dùng gửi ở trong vai trò 'user'.
Hãy tóm tắt những gì đã xảy ra trong cuộc trò chuyện từ quan điểm của AI (sử dụng ngôi thứ nhất) bằng Tiếng Việt.
Đầu ra chỉ gồm bản tóm tắt cuộc đối thoại,không giải thích không bao gồm bất cứ chuỗi nào khác ngoài bản tóm tắt cuộc đối thoại."""

SUMMARIZER_HUMAN_TEMPLATE = """```{input}```
Tóm tắt đoạn hội thoại trên. LUÔN phản hồi bằng Tiếng Việt."""
