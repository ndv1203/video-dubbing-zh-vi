export type JobStatus = 'queued' | 'processing' | 'completed' | 'failed';

export type JobStage = 'asr' | 'translation' | 'tts' | 'render' | null;

export interface JobSummary {
  id: string;
  status: JobStatus;
  stage: JobStage;
  progress: number;
  original_filename: string;
  created_at: string;
}

export interface JobDetail extends JobSummary {
  file_size_bytes: number;
  duration_seconds: number | null;
  input_path: string;
  output_path: string | null;
  subtitle_path: string | null;
  error_code: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  updated_at: string;
}

export interface PipelineStageInfo {
  key: NonNullable<JobStage>;
  label: string;
  description: string;
  percentage: number;
}

export const PIPELINE_STAGES: PipelineStageInfo[] = [
  {
    key: 'asr',
    label: 'Nhận diện tiếng Trung',
    description: 'Trích xuất âm thanh và chuyển đổi giọng nói tiếng Trung thành phụ đề kèm timestamp.',
    percentage: 25,
  },
  {
    key: 'translation',
    label: 'Dịch thuật Trung ➔ Việt',
    description: 'Mô hình Transformer dịch văn bản tiếng Trung sang tiếng Việt tự nhiên và chuẩn văn phong.',
    percentage: 50,
  },
  {
    key: 'tts',
    label: 'Lồng tiếng giọng Việt',
    description: 'Tạo giọng đọc thuyết minh tiếng Việt chuẩn, đồng bộ nhịp điệu với video gốc.',
    percentage: 75,
  },
  {
    key: 'render',
    label: 'Ghép video & Xuất phụ đề',
    description: 'Dùng FFmpeg hoà trộn âm thanh thuyết minh, burn phụ đề tiếng Việt và xuất file video.',
    percentage: 100,
  },
];

