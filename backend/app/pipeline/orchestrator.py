import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from uuid import UUID

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.job import ProcessingJob
from app.pipeline.audio_extractor import extract_audio_for_asr, get_media_info
from app.pipeline.asr_runner import run_chinese_asr
from app.pipeline.translator_step import translate_segments
from app.pipeline.tts_synthesizer import synthesize_and_align_dubbing
from app.pipeline.media_composer import compose_dubbed_video, generate_srt_subtitles

logger = logging.getLogger(__name__)


def update_job_progress(job_uuid: UUID, stage: str, progress: int):
    with SessionLocal() as db:
        job = db.get(ProcessingJob, job_uuid)
        if job:
            job.stage = stage
            job.progress = progress
            db.commit()


def run_dubbing_pipeline(
    job_id: str,
    voice_preset: str = "female_gentle",
) -> Dict[str, Any]:
    """
    Quy trình lồng tiếng hoàn chỉnh từ Video đầu vào sang Video thành phẩm:
    Giai đoạn 1: ASR (25%) -> Tách audio và nhận diện tiếng Trung.
    Giai đoạn 2: Translation (50%) -> Dịch ngữ cảnh Trung sang Việt.
    Giai đoạn 3: TTS (75%) -> Lồng tiếng Việt & Căn chỉnh thời gian.
    Giai đoạn 4: Render (100%) -> Audio ducking, burn phụ đề & xuất file MP4.
    """
    job_uuid = UUID(job_id)

    with SessionLocal() as db:
        job = db.get(ProcessingJob, job_uuid)
        if not job:
            raise ValueError(f"Không tìm thấy job: {job_id}")
        input_path = Path(job.input_path)

    if not input_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy video đầu vào: {input_path}")

    # Chuẩn bị thư mục làm việc và thư mục xuất
    work_dir = Path(settings.storage_root) / "work" / str(job_uuid)
    output_dir = Path(settings.storage_root) / "outputs"
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Đọc thông số video gốc
    video_info = get_media_info(input_path)
    total_duration = max(video_info.get("duration", 0.0), 1.0)

    with SessionLocal() as db:
        job = db.get(ProcessingJob, job_uuid)
        if job:
            job.duration_seconds = int(total_duration)
            db.commit()

    # --- GIAI ĐOẠN 1: ASR (25%) ---
    update_job_progress(job_uuid, "asr", 10)
    audio_16k_path = work_dir / "audio_16k.wav"
    logger.info(f"[{job_id}] Bắt đầu bóc tách âm thanh sang {audio_16k_path}...")
    extract_audio_for_asr(input_path, audio_16k_path, sample_rate=16000, channels=1)

    update_job_progress(job_uuid, "asr", 25)
    logger.info(f"[{job_id}] Nhận diện giọng nói tiếng Trung...")
    chinese_segments = run_chinese_asr(audio_16k_path)

    # --- GIAI ĐOẠN 2: TRANSLATION (50%) ---
    update_job_progress(job_uuid, "translation", 35)
    logger.info(f"[{job_id}] Dịch {len(chinese_segments)} phân đoạn sang tiếng Việt...")
    translated_segments = translate_segments(chinese_segments)
    update_job_progress(job_uuid, "translation", 50)

    # --- GIAI ĐOẠN 3: TTS (75%) ---
    update_job_progress(job_uuid, "tts", 60)
    logger.info(f"[{job_id}] Sinh giọng đọc tiếng Việt và căn chỉnh mốc thời gian...")
    master_dub_path = synthesize_and_align_dubbing(
        segments=translated_segments,
        work_dir=work_dir,
        total_video_duration=total_duration,
        voice_preset=voice_preset,
    )
    update_job_progress(job_uuid, "tts", 75)

    # --- GIAI ĐOẠN 4: RENDER (95% -> 100%) ---
    update_job_progress(job_uuid, "render", 85)
    srt_path = output_dir / f"{job_uuid}_subs.srt"
    generate_srt_subtitles(translated_segments, srt_path)

    output_video_path = output_dir / f"{job_uuid}_dubbed.mp4"
    logger.info(f"[{job_id}] Hoà âm và xuất video thành phẩm...")
    compose_dubbed_video(
        video_input_path=input_path,
        dub_audio_path=master_dub_path,
        srt_path=srt_path,
        output_video_path=output_video_path,
        bgm_volume=0.18,
        dub_volume=1.0,
    )

    update_job_progress(job_uuid, "render", 100)

    # Cập nhật kết quả cuối cùng vào database
    with SessionLocal() as db:
        job = db.get(ProcessingJob, job_uuid)
        if job:
            job.output_path = str(output_video_path)
            job.subtitle_path = str(srt_path)
            db.commit()

    logger.info(f"[{job_id}] Toàn bộ quy trình lồng tiếng hoàn tất thành công!")
    return {
        "job_id": job_id,
        "output_path": str(output_video_path),
        "subtitle_path": str(srt_path),
        "segments": translated_segments,
    }

