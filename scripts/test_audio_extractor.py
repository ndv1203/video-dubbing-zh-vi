import sys
from pathlib import Path

# Thêm thư mục backend vào sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.pipeline.audio_extractor import extract_audio_for_asr, get_media_info


def main():
    repo_root = Path(__file__).resolve().parent.parent
    uploads_dir = repo_root / "storage" / "uploads"
    work_dir = repo_root / "storage" / "work" / "test_extract"
    work_dir.mkdir(parents=True, exist_ok=True)

    print("=== KIỂM TRA BÓC TÁCH AUDIO TỪ VIDEO ===")

    # Tìm file video hợp lệ trong uploads (bỏ qua file giả lập/rỗng < 1KB)
    all_files = list(uploads_dir.glob("*.mp4")) + list(uploads_dir.glob("*.mkv"))
    video_files = [f for f in all_files if f.stat().st_size > 1024]

    if not video_files:
        print(f"Chưa có video thực tế trong {uploads_dir}. Đang tạo một video ngắn mẫu bằng FFmpeg để kiểm tra...")
        sample_video = work_dir / "sample_test.mp4"
        import subprocess

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=5:size=640x360:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=1000:duration=5",
            "-c:v", "libx264", "-c:a", "aac",
            str(sample_video),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        target_video = sample_video
    else:
        target_video = video_files[0]

    print(f"\n1. Đọc thông tin video: {target_video.name}")
    info = get_media_info(target_video)
    print(f"   - Thời lượng: {info['duration']:.2f}s")
    print(f"   - Có video: {info['has_video']}")
    print(f"   - Có audio: {info['has_audio']}")
    print(f"   - Sample rate: {info['audio_sample_rate']} Hz")
    print(f"   - Kênh audio: {info['audio_channels']}")
    print(f"   - Dung lượng: {info['size_bytes'] / 1024:.1f} KB")

    out_wav = work_dir / f"{target_video.stem}_16k.wav"
    print(f"\n2. Bóc tách audio chuẩn ASR sang: {out_wav.name}")
    res = extract_audio_for_asr(target_video, out_wav, sample_rate=16000, channels=1)
    print(f"   - File WAV đầu ra: {res}")
    print(f"   - Dung lượng WAV: {res.stat().st_size / 1024:.1f} KB")

    # Kiểm tra lại file WAV qua get_media_info
    wav_info = get_media_info(res)
    print(f"   - Tần số lấy mẫu kiểm tra: {wav_info['audio_sample_rate']} Hz (chuẩn ASR)")
    print(f"   - Số kênh kiểm tra: {wav_info['audio_channels']} (mono)")

    print("\n✅ KIỂM TRA BÓC TÁCH AUDIO THÀNH CÔNG!")


if __name__ == "__main__":
    main()
