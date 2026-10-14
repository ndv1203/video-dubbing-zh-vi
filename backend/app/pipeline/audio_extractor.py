import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def get_media_info(video_path: str | Path) -> Dict[str, Any]:
    """
    Sử dụng ffprobe để trích xuất thông tin kỹ thuật của file video:
    - duration (giây)
    - has_audio (True/False)
    - has_video (True/False)
    - audio_sample_rate
    - audio_channels
    - format_name, size
    """
    path = Path(video_path)
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy file video: {video_path}")

    # Chạy ffprobe lấy thông tin format và streams
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration,size,format_name:stream=index,codec_type,codec_name,channels,sample_rate",
        "-of", "json",
        str(path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
    except subprocess.CalledProcessError as exc:
        logger.error(f"Lỗi khi chạy ffprobe trên {video_path}: {exc.stderr}")
        raise RuntimeError(f"Không thể đọc thông tin video qua ffprobe: {exc.stderr.strip()}")
    except Exception as exc:
        logger.error(f"Lỗi phân tích metadata video: {exc}")
        raise RuntimeError(f"Lỗi phân tích metadata video: {str(exc)}")

    streams = data.get("streams", [])
    format_info = data.get("format", {})

    has_video = any(s.get("codec_type") == "video" for s in streams)
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    has_audio = len(audio_streams) > 0

    duration = 0.0
    if "duration" in format_info and format_info["duration"]:
        try:
            duration = float(format_info["duration"])
        except ValueError:
            pass

    audio_sample_rate = None
    audio_channels = None
    if has_audio:
        first_audio = audio_streams[0]
        try:
            audio_sample_rate = int(first_audio.get("sample_rate", 0)) or None
            audio_channels = int(first_audio.get("channels", 0)) or None
        except (ValueError, TypeError):
            pass

    return {
        "file_path": str(path),
        "duration": duration,
        "has_video": has_video,
        "has_audio": has_audio,
        "audio_channels": audio_channels,
        "audio_sample_rate": audio_sample_rate,
        "format_name": format_info.get("format_name"),
        "size_bytes": int(format_info.get("size", 0)) if format_info.get("size") else path.stat().st_size,
    }


def extract_audio_for_asr(
    video_path: str | Path,
    output_wav_path: str | Path,
    sample_rate: int = 16000,
    channels: int = 1,
) -> Path:
    """
    Tách luồng âm thanh từ video sang file WAV chuẩn 16kHz Mono 16-bit PCM:
    - Định dạng chuẩn bắt buộc cho hầu hết các model ASR (Whisper, FunASR, v.v.).
    - sample_rate: mặc định 16000 Hz.
    - channels: 1 (mono).
    """
    src = Path(video_path)
    dst = Path(output_wav_path)

    if not src.is_file():
        raise FileNotFoundError(f"File video nguồn không tồn tại: {video_path}")

    # Đảm bảo thư mục đích tồn tại
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Kiểm tra xem video có stream audio hay không
    info = get_media_info(src)
    if not info["has_audio"]:
        raise ValueError(f"Video {src.name} không có luồng âm thanh (has_audio=False)")

    logger.info(
        f"Bắt đầu tách audio từ {src.name} sang {dst.name} (sample_rate={sample_rate}, channels={channels})..."
    )

    # Chạy FFmpeg để tách và chuẩn hoá audio
    cmd = [
        "ffmpeg",
        "-y",               # Ghi đè file nếu đã tồn tại
        "-i", str(src),
        "-vn",              # Bỏ luồng video
        "-acodec", "pcm_s16le",  # PCM 16-bit
        "-ar", str(sample_rate), # Tần số lấy mẫu (16000 Hz)
        "-ac", str(channels),    # Số kênh (1 = mono)
        str(dst),
    ]

    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        err_msg = exc.stderr.strip()
        logger.error(f"FFmpeg trích xuất audio thất bại: {err_msg}")
        raise RuntimeError(f"FFmpeg trích xuất audio thất bại: {err_msg}")

    if not dst.is_file() or dst.stat().st_size == 0:
        raise RuntimeError(f"File audio đầu ra không hợp lệ hoặc rỗng: {dst}")

    logger.info(
        f"Tách audio thành công: {dst} ({dst.stat().st_size} bytes, thời lượng ~{info['duration']:.2f}s)"
    )
    return dst
