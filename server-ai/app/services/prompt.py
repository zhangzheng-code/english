from app.schemas import success

CHAT_MODES = [
    {"role": "normal", "label": "\U0001f4ac \u667a\u80fd\u52a9\u624b", "id": "1"},
    {"role": "master", "label": "\U0001f393 \u82f1\u8bed\u5927\u5e08", "id": "2"},
    {"role": "business", "label": "\U0001f4bc \u5546\u52a1\u82f1\u8bed", "id": "3"},
    {"role": "qilinge", "label": "\U0001f409 \u9e92\u9e9f\u54e5", "id": "4"},
    {"role": "xiaoman", "label": "\U0001f4bb \u5c0f\u6ee1\u6a21\u5f0f", "id": "5"},
]


def get_prompt_list() -> dict:
    return success(CHAT_MODES)
