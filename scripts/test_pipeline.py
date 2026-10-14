import sys
from pathlib import Path

# Thêm thư mục backend vào sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.pipeline.audio_extractor import extract_audio_for_asr, get_media_info
from app.pipeline.asr_runner import run_chinese_asr
from app.pipeline.translator_step import translate_segments
from app.pipeline.tts_synthesizer import synthesize_and_align_dubbing
from app.pipeline.media_composer import compose_dubbed_video, generate_srt_subtitles


def main():
    repo_root = Path(__file__).resolve().parent.parent
    work_dir = repo_root / "storage" / "work" / "test_full_pipeline"
    out_dir = repo_root / "storage" / "outputs" / "test_full_pipeline"
    work_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("====================================================")
    print("   KIỂM TRA TOÀN DIỆN VIDEO DUBBING PIPELINE (ZH ➔ VI)")
    print("====================================================")

    # 1. Tìm hoặc tạo video đầu vào
    uploads_dir = repo_root / "storage" / "uploads"
    valid_videos = [f for f in uploads_dir.glob("*.mp4") if f.stat().st_size > 1024]
    if not valid_videos:
        print("Chưa có video thực tế trong uploads. Tạo video mẫu 5 giây...")
        import subprocess

        sample_video = work_dir / "sample_input.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=5:size=640x360:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=5",
            "-c:v", "libx264", "-c:a", "aac",
            str(sample_video),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        video_input = sample_video
    else:
        video_input = valid_videos[0]

    print(f"\n[Bước 1/4] Đọc thông tin video đầu vào: {video_input.name}")
    info = get_media_info(video_input)
    print(f"   ➔ Thời lượng: {info['duration']:.2f}s, Dung lượng: {info['size_bytes'] / 1024:.1f} KB")

    # Tách audio 16kHz
    audio_wav = work_dir / "audio_16k.wav"
    extract_audio_for_asr(video_input, audio_wav)
    print(f"   ➔ Bóc tách audio chuẩn 16kHz WAV thành công: {audio_wav.name}")

    # Chạy ASR
    print(f"\n[Bước 2/4] Nhận diện giọng nói tiếng Trung (ASR)...")
    zh_segments = run_chinese_asr(audio_wav)
    for seg in zh_segments:
        print(f"   • [{seg['start']}s - {seg['end']}s]: {seg['text']}")

    # Dịch sang tiếng Việt
    print(f"\n[Bước 3/4] Dịch thuật sang tiếng Việt (Translation)...")
    vi_segments = translate_segments(zh_segments)
    for seg in vi_segments:
        print(f"   • [{seg['start']}s - {seg['end']}s]: {seg['text_zh']} ➔ {seg['text_vi']}")

    # Sinh giọng đọc tiếng Việt (TTS)
    print(f"\n[Bước 4/4] Lồng tiếng (TTS) và Xuất video thành phẩm (Render)...")
    master_dub = synthesize_and_align_dubbing(
        segments=vi_segments,
        work_dir=work_dir,
        total_video_duration=info["duration"],
        voice_preset="female_gentle",
    )
    print(f"   ➔ Tạo Master Dub Track thành công: {master_dub.name}")

    # Tạo phụ đề SRT
    srt_out = out_dir / "subtitles.srt"
    generate_srt_subtitles(vi_segments, srt_out)
    print(f"   ➔ Xuất file phụ đề: {srt_out.name}")

    # Ghép video thành phẩm
    video_out = out_dir / "final_dubbed_video.mp4"
    compose_dubbed_video(
        video_input_path=video_input,
        dub_audio_path=master_dub,
        srt_path=srt_out,
        output_video_path=video_out,
        bgm_volume=0.18,
        dub_volume=1.0,
    )
    print(f"   ➔ Xuất video thành phẩm: {video_out.name} ({video_out.stat().st_size / 1024:.1f} KB)")

    print("\n====================================================")
    print("🎉 TOÀN BỘ PIPELINE ĐÃ CHẠY HOÀN TẤT THÀNH CÔNG!")
    print(f"Video thành phẩm tại: {video_out}")
    print(f"Phụ đề tiếng Việt tại: {srt_out}")
    print("====================================================")


if __name__ == "__main__":
    main()

