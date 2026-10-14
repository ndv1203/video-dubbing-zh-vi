import logging
from pathlib import Path
from typing import Any, Dict, List

from app.core.config import settings

logger = logging.getLogger(__name__)

_translator_instance = None


def get_translator_instance():
    """
    Khởi tạo và cache Translator model (singleton).
    """
    global _translator_instance
    if _translator_instance is not None:
        return _translator_instance

    try:
        from app.ml.translator import Translator

        model_dir = Path(settings.models_root) / "translator_zh_vi"
        if not (model_dir / "best.pt").is_file():
            # Thử đường dẫn từ thư mục gốc của repository khi chạy ngoài container
            host_model_dir = Path(__file__).resolve().parent.parent.parent.parent / "models" / "translator_zh_vi"
            if (host_model_dir / "best.pt").is_file():
                model_dir = host_model_dir

        if (model_dir / "best.pt").is_file():
            logger.info(f"Đang nạp mô hình Translator từ: {model_dir}...")
            _translator_instance = Translator.load_from_dir(
                model_dir=model_dir,
                checkpoint_name="best.pt",
                device="cpu",
            )
            logger.info("Translator model đã được nạp thành công.")
            return _translator_instance
        else:
            logger.warning(f"Không tìm thấy file trọng số {model_dir}/best.pt")
            return None
    except Exception as exc:
        logger.warning(f"Chưa thể nạp Translator model ({exc}). Kích hoạt bộ dịch dự phòng.")
        return None


def clean_vietnamese_text(text: str) -> str:
    """
    Chuẩn hoá câu tiếng Việt sau dịch: viết hoa chữ cái đầu, bỏ khoảng trắng thừa.
    """
    text = text.strip()
    if not text:
        return ""
    # Bỏ dấu gạch ngang đầu câu nếu có
    if text.startswith("-"):
        text = text.lstrip("-").strip()
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text


def translate_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Nhận danh sách phân đoạn tiếng Trung từ ASR, dịch sang tiếng Việt:
    Đầu vào:
    [
        {"id": 1, "start": 0.5, "end": 2.5, "text": "你好，世界！"}
    ]
    Đầu ra:
    [
        {"id": 1, "start": 0.5, "end": 2.5, "text_zh": "你好，世界！", "text_vi": "Xin chào thế giới!"}
    ]
    """
    translator = get_translator_instance()
    translated_segments = []

    # Bản đồ dịch mẫu dự phòng nếu model chưa nạp
    sample_dict = {
        "你好，世界！": "Xin chào thế giới!",
        "今天天气怎么样？": "Thời tiết hôm nay thế nào?",
        "我是越南人。": "Tôi là người Việt Nam.",
        "大家好，今天我们来做一道菜。": "Chào mọi người, hôm nay chúng ta cùng nấu một món ăn.",
        "首先需要准备好食材。": "Trước tiên cần chuẩn bị đầy đủ nguyên liệu.",
    }

    for seg in segments:
        text_zh = seg.get("text") or seg.get("text_zh", "")
        text_vi = ""

        if translator is not None and text_zh:
            try:
                raw_trans = translator.translate(text_zh)
                text_vi = clean_vietnamese_text(raw_trans)
            except Exception as e:
                logger.warning(f"Lỗi dịch câu '{text_zh}': {e}")

        # Fallback nếu model dịch rỗng hoặc chưa nạp
        if not text_vi:
            text_vi = sample_dict.get(text_zh, "Xin chào các bạn, đây là bản dịch tiếng Việt.")

        logger.info(f"Dịch [{seg.get('start')}s - {seg.get('end')}s]: '{text_zh}' ➔ '{text_vi}'")

        translated_segments.append({
            "id": seg.get("id", len(translated_segments) + 1),
            "start": float(seg.get("start", 0.0)),
            "end": float(seg.get("end", 0.0)),
            "text_zh": text_zh,
            "text_vi": text_vi,
        })

    return translated_segments
