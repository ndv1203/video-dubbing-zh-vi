import { JobDetail, JobSummary } from '../types/job';

const API_BASE = '/api/v1';

export async function fetchHealth(): Promise<{ status: string; database: string; redis: string }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error('Hệ thống máy chủ chưa phản hồi');
  }
  return res.json();
}

export async function fetchJobs(limit = 30): Promise<JobSummary[]> {
  const res = await fetch(`${API_BASE}/jobs?limit=${limit}`);
  if (!res.ok) {
    throw new Error('Không thể lấy danh sách tác vụ');
  }
  return res.json();
}

export async function fetchJobDetail(jobId: string): Promise<JobDetail> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) {
    throw new Error('Không thể tải thông tin tác vụ');
  }
  return res.json();
}

export async function uploadVideo(
  file: File,
  onProgress?: (progressPercent: number) => void
): Promise<JobDetail> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);

    xhr.open('POST', `${API_BASE}/jobs`);

    if (xhr.upload && onProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100);
          onProgress(percent);
        }
      };
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch (e) {
          reject(new Error('Phản hồi từ máy chủ không hợp lệ'));
        }
      } else {
        try {
          const errData = JSON.parse(xhr.responseText);
          reject(new Error(errData.detail || 'Lỗi khi tải video lên'));
        } catch {
          reject(new Error(`Tải lên thất bại với mã lỗi ${xhr.status}`));
        }
      }
    };

    xhr.onerror = () => {
      reject(new Error('Lỗi kết nối mạng khi tải video lên'));
    };

    xhr.send(formData);
  });
}

export function getVideoStreamUrl(jobId: string, kind: 'output' | 'input' = 'output'): string {
  return `${API_BASE}/jobs/${jobId}/stream?kind=${kind}`;
}

export function getSubtitlesUrl(jobId: string): string {
  return `${API_BASE}/jobs/${jobId}/subtitles`;
}

