import React, { useState } from 'react';
import { Download, Film, RefreshCw } from 'lucide-react';
import { JobDetail } from '../types/job';
import { getVideoStreamUrl } from '../api/client';

interface VideoPlayerProps {
  job: JobDetail;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({ job }) => {
  const [videoKind, setVideoKind] = useState<'output' | 'input'>(
    job.status === 'completed' ? 'output' : 'input'
  );

  const isCompleted = job.status === 'completed';
  const isProcessing = job.status === 'processing' || job.status === 'queued';
  const videoUrl = getVideoStreamUrl(job.id, videoKind);

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-col">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="font-semibold text-slate-900 text-base flex items-center space-x-2">
            <Film className="w-5 h-5 text-indigo-600" />
            <span className="truncate max-w-sm" title={job.original_filename}>
              {job.original_filename}
            </span>
          </h2>
          <span className="text-xs text-slate-500 font-mono">ID: {job.id.slice(0, 8)}...</span>
        </div>

        {/* Video Mode Switcher (Output vs Input) */}
        <div className="flex items-center bg-slate-100 p-1 rounded-xl text-xs font-medium">
          <button
            onClick={() => setVideoKind('output')}
            disabled={!isCompleted}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              videoKind === 'output' && isCompleted
                ? 'bg-white text-indigo-700 shadow-xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            } ${!isCompleted ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            Video lồng tiếng (VI)
          </button>
          <button
            onClick={() => setVideoKind('input')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              videoKind === 'input'
                ? 'bg-white text-slate-900 shadow-xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Video gốc (ZH)
          </button>
        </div>
      </div>

      {/* Video Screen Area */}
      <div className="relative aspect-video w-full rounded-xl overflow-hidden bg-slate-950 flex items-center justify-center border border-slate-900 shadow-inner">
        {isProcessing && videoKind === 'output' ? (
          <div className="text-center p-6 text-slate-400 space-y-3">
            <div className="w-12 h-12 mx-auto rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center text-indigo-400 animate-pulse">
              <RefreshCw className="w-6 h-6 animate-spin" />
            </div>
            <div>
              <p className="font-medium text-slate-200 text-sm">
                Đang xử lý lồng tiếng ({job.progress}%)
              </p>
              <p className="text-xs text-slate-500 mt-1 max-w-sm">
                Video thành phẩm sẽ tự động hiển thị sau khi hoàn tất giai đoạn render
              </p>
            </div>
            <button
              onClick={() => setVideoKind('input')}
              className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 transition-colors"
            >
              Xem tạm video gốc
            </button>
          </div>
        ) : (
          <video
            key={`${job.id}_${videoKind}`}
            controls
            className="w-full h-full object-contain"
            src={videoUrl}
          >
            Trình duyệt của bạn không hỗ trợ phát thẻ video HTML5.
          </video>
        )}
      </div>

      {/* Action Footer */}
      <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="text-slate-500 space-y-0.5">
          <p>
            Dung lượng: <span className="font-medium text-slate-700">{(job.file_size_bytes / (1024 * 1024)).toFixed(1)} MB</span>
          </p>
          <p>
            Khởi tạo:{' '}
            <span className="font-medium text-slate-700">
              {new Date(job.created_at).toLocaleString('vi-VN')}
            </span>
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {isCompleted && (
            <a
              href={getVideoStreamUrl(job.id, 'output')}
              download={`dubbed_${job.original_filename}`}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-xl flex items-center space-x-1.5 shadow-xs transition-colors"
            >
              <Download className="w-4 h-4" />
              <span>Tải video lồng tiếng (MP4)</span>
            </a>
          )}
          <a
            href={getVideoStreamUrl(job.id, 'input')}
            download={`original_${job.original_filename}`}
            className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-xl flex items-center space-x-1.5 transition-colors"
          >
            <Download className="w-4 h-4 text-slate-500" />
            <span>Tải video gốc</span>
          </a>
        </div>
      </div>
    </div>
  );
};
