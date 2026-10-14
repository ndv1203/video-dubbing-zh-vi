import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from app.pipeline.audio_extractor import get_media_info

logger = logging.getLogger(__name__)


def format_timestamp_srt(seconds: float) -> str:
    """
    Chuyển đổi số giây float sang định dạng SRT timestamp: HH:MM:SS,mmm
    Ví dụ: 65.25 -> 00:01:05,250
    """
    total_ms = int(round(seconds * 1000))
    hours = total_ms // 3600000
    minutes = (total_ms % 3600000) // 60000
    secs = (total_ms % 60000) // 1000
    ms = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def generate_srt_subtitles(segments: List[Dict[str, Any]], output_srt_path: str | Path) -> Path:
    """
    Tạo file phụ đề .srt tiếng Việt từ các mốc thời gian đã dịch.
    """
    path = Path(output_srt_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    for idx, seg in enumerate(segments, start=1):
        text = seg.get("text_vi", "").strip()
        if not text:
            continue
        start_str = format_timestamp_srt(seg.get("start", 0.0))
        end_str = format_timestamp_srt(seg.get("end", seg.get("start", 0.0) + 2.0))

        lines.append(str(idx))
        lines.append(f"{start_str} --> {end_str}")
        lines.append(text)
        lines.append("")  # Dòng trống ngăn cách

    content = "\n".join(lines)
    path.write_text(content, encoding="utf-8")
    logger.info(f"Đã tạo file phụ đề SRT thành công: {path} ({len(lines)//4} câu)")
    return path


def compose_dubbed_video(
    video_input_path: str | Path,
    dub_audio_path: str | Path,
    srt_path: str | Path,
    output_video_path: str | Path,
    bgm_volume: float = 0.18,
    dub_volume: float = 1.0,
) -> Path:
    """
    Hoà trộn hoàn chỉnh:
    1. Audio Ducking: Giảm volume video gốc còn ~18% để giữ nhạc nền/hiệu ứng + Phủ giọng đọc lồng tiếng 100%.
    2. Burn phụ đề tiếng Việt (Hardsub) với font chữ rõ nét.
    3. Xuất file MP4 tối ưu hoá cho web player (+faststart).
    """
    video_in = Path(video_input_path)
    audio_in = Path(dub_audio_path)
    srt_in = Path(srt_path)
    out_video = Path(output_video_path)

    out_video.parent.mkdir(parents=True, exist_ok=True)

    info = get_media_info(video_in)
    has_orig_audio = info.get("has_audio", False)

    # Escape ký tự đặc biệt cho filter subtitles của FFmpeg
    escaped_srt = str(srt_in).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")

    # Cấu hình style phụ đề: Chữ trắng, viền đen bóng mờ, cỡ chữ 15
    sub_style = (
        "force_style='FontSize=15,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        "BackColour=&H60000000,BorderStyle=4,MarginV=24'"
    )

    if has_orig_audio:
        filter_complex = (
            f"[0:a]volume={bgm_volume:.2f}[bgm];"
            f"[1:a]volume={dub_volume:.2f}[dub];"
            f"[bgm][dub]amix=inputs=2:duration=first[aout];"
            f"[0:v]subtitles='{escaped_srt}':{sub_style}[vout]"
        )
    else:
        filter_complex = (
            f"[1:a]volume={dub_volume:.2f}[aout];"
            f"[0:v]subtitles='{escaped_srt}':{sub_style}[vout]"
        )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_in),
        "-i", str(audio_in),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",  # Cho phép phát video stream ngay trên trình duyệt
        str(out_video),
    ]

    logger.info(f"Đang render video lồng tiếng sang: {out_video}...")
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        err = exc.stderr.strip()
        logger.warning(f"Lỗi khi burn hardsub ({err}). Thử render dự phòng không burn subtitle...")

        # Fallback nếu hệ thống thiếu thư viện fontconfig/libass
        if has_orig_audio:
            filter_no_sub = (
                f"[0:a]volume={bgm_volume:.2f}[bgm];"
                f"[1:a]volume={dub_volume:.2f}[dub];"
                f"[bgm][dub]amix=inputs=2:duration=first[aout]"
            )
        else:
            filter_no_sub = f"[1:a]volume={dub_volume:.2f}[aout]"

        fallback_cmd = [
            "ffmpeg", "-y",
            "-i", str(video_in),
            "-i", str(audio_in),
            "-filter_complex", filter_no_sub,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(out_video),
        ]
        subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

    if not out_video.is_file() or out_video.stat().st_size == 0:
        raise RuntimeError(f"Xuất video thất bại hoặc file rỗng: {out_video}")

    logger.info(f"Render video thành phẩm thành công: {out_video} ({out_video.stat().st_size} bytes)")
    return out_video

