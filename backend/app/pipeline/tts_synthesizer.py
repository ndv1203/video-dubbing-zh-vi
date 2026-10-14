import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from app.pipeline.audio_extractor import get_media_info

logger = logging.getLogger(__name__)

VOICE_MAP = {
    "female_gentle": "vi-VN-HoaiMyNeural",
    "female_south": "vi-VN-HoaiMyNeural",
    "male_narrator": "vi-VN-NamMinhNeural",
    "male_south": "vi-VN-NamMinhNeural",
}


async def synthesize_sentence_edge_tts(
    text: str,
    output_path: Path,
    voice_name: str = "vi-VN-HoaiMyNeural",
) -> Path:
    """
    Sinh audio tiếng Việt cho một câu qua Microsoft Edge-TTS.
    """
    import edge_tts

    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(str(output_path))
    return output_path


def synthesize_fallback_beep(duration: float, output_path: Path) -> Path:
    """
    Tạo audio dự phòng nếu không có mạng gọi Edge-TTS (dùng lavfi sine wave ngắn).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dur = max(duration, 1.0)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=frequency=520:duration={dur}",
        "-af", "volume=0.3",
        "-ar", "44100", "-ac", "1",
        str(output_path),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_path


def adjust_audio_speed(input_audio: Path, output_audio: Path, speed_factor: float) -> Path:
    """
    Co giãn thời lượng âm thanh bằng filter atempo của FFmpeg (giữ nguyên cao độ giọng nói).
    - speed_factor > 1.0: phát nhanh hơn để kịp khớp mốc thời gian.
    - speed_factor < 1.0: phát chậm hơn.
    """
    # atempo chỉ nhận giá trị từ 0.5 đến 2.0
    factor = max(0.5, min(speed_factor, 1.5))
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_audio),
        "-filter:a", f"atempo={factor:.2f}",
        "-ar", "44100", "-ac", "1",
        str(output_audio),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_audio


def synthesize_and_align_dubbing(
    segments: List[Dict[str, Any]],
    work_dir: str | Path,
    total_video_duration: float,
    voice_preset: str = "female_gentle",
) -> Path:
    """
    Quy trình sinh lời thoại và căn chỉnh thời gian:
    1. Sinh từng đoạn audio TTS cho text_vi.
    2. So sánh độ dài audio TTS với khoảng thời gian (end - start).
    3. Tăng tốc độ phát (atempo) nếu câu tiếng Việt nói dài hơn thời lượng video cho phép.
    4. Trộn tất cả vào master dub track theo đúng mốc giây start.
    """
    work = Path(work_dir)
    tts_dir = work / "tts_clips"
    tts_dir.mkdir(parents=True, exist_ok=True)

    voice_name = VOICE_MAP.get(voice_preset, "vi-VN-HoaiMyNeural")
    master_dub_path = work / "dub_master.wav"

    processed_clips: List[Dict[str, Any]] = []

    # Duyệt từng phân đoạn để sinh audio
    for seg in segments:
        seg_id = seg["id"]
        text_vi = seg.get("text_vi", "").strip()
        if not text_vi:
            continue

        start_time = float(seg.get("start", 0.0))
        end_time = float(seg.get("end", start_time + 2.0))
        target_duration = max(end_time - start_time, 0.5)

        raw_clip = tts_dir / f"clip_{seg_id}_raw.mp3"
        final_clip = tts_dir / f"clip_{seg_id}.wav"

        # 1. Gọi Edge-TTS
        try:
            asyncio.run(synthesize_sentence_edge_tts(text_vi, raw_clip, voice_name))
            info = get_media_info(raw_clip)
            actual_duration = info["duration"]
        except Exception as e:
            logger.warning(f"Lỗi khi gọi Edge-TTS câu {seg_id} ('{text_vi}'): {e}. Dùng audio dự phòng.")
            synthesize_fallback_beep(target_duration, final_clip)
            actual_duration = target_duration
            raw_clip = final_clip

        # 2. Kiểm tra lệch pha thời gian (Time-Stretching)
        if raw_clip != final_clip:
            if actual_duration > target_duration:
                # Tiếng Việt nói dài hơn mốc thời gian video -> tăng tốc độ
                speed_factor = actual_duration / target_duration
                # Giới hạn tốc độ tối đa 1.35x để người nghe vẫn nghe rõ lời
                speed_factor = min(speed_factor, 1.35)
                logger.info(
                    f"Câu {seg_id} dài hơn mốc cho phép ({actual_duration:.2f}s > {target_duration:.2f}s). "
                    f"Tăng tốc {speed_factor:.2f}x qua FFmpeg atempo..."
                )
                adjust_audio_speed(raw_clip, final_clip, speed_factor)
            else:
                # Không bị tràn thời lượng, chỉ chuyển sang WAV chuẩn 44.1kHz
                cmd = ["ffmpeg", "-y", "-i", str(raw_clip), "-ar", "44100", "-ac", "1", str(final_clip)]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        processed_clips.append({
            "clip_path": final_clip,
            "start_time": start_time,
        })

    # 3. Tạo Master Dub Track bao phủ toàn bộ thời lượng video
    duration = max(total_video_duration, 1.0)
    if not processed_clips:
        # Nếu không có câu nào, tạo một track âm thanh tĩnh
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-t", f"{duration:.2f}", "-i", "anullsrc=r=44100:cl=mono",
            "-c:a", "pcm_s16le", str(master_dub_path),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return master_dub_path

    # Xây dựng FFmpeg filter adelay + amix để đặt từng câu vào đúng giây start
    inputs = ["-f", "lavfi", "-t", f"{duration:.2f}", "-i", "anullsrc=r=44100:cl=mono"]
    filter_parts = []
    amix_inputs = ["[0:a]"]

    for idx, item in enumerate(processed_clips, start=1):
        inputs.extend(["-i", str(item["clip_path"])])
        delay_ms = int(item["start_time"] * 1000)
        filter_parts.append(f"[{idx}:a]adelay=delays={delay_ms}:all=1[d{idx}];")
        amix_inputs.append(f"[d{idx}]")

    amix_filter = f"{' '.join(filter_parts)} {''.join(amix_inputs)}amix=inputs={len(amix_inputs)}:duration=first:normalize=0[out]"

    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", amix_filter, "-map", "[out]", "-c:a", "pcm_s16le", str(master_dub_path)]

    logger.info(f"Đang trộn {len(processed_clips)} phân đoạn audio vào Master Dub Track...")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logger.info(f"Tạo Master Dub Track thành công: {master_dub_path}")

    return master_dub_path
