import React from 'react';
import { Clock, CheckCircle2, AlertCircle, Loader2, RotateCcw, Video } from 'lucide-react';
import { JobStatus, JobSummary } from '../types/job';

interface HistoryListProps {
  jobs: JobSummary[];
  selectedJobId: string | null;
  onSelectJob: (jobId: string) => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const HistoryList: React.FC<HistoryListProps> = ({
  jobs,
  selectedJobId,
  onSelectJob,
  onRefresh,
  isLoading,
}) => {
  const getStatusBadge = (status: JobStatus, progress: number) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center space-x-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            <span>Hoàn thành</span>
          </span>
        );
      case 'processing':
        return (
          <span className="inline-flex items-center space-x-1 text-[11px] font-medium text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-200 animate-pulse">
            <Loader2 className="w-3 h-3 animate-spin text-indigo-600" />
            <span>Đang xử lý {progress}%</span>
          </span>
        );
      case 'queued':
        return (
          <span className="inline-flex items-center space-x-1 text-[11px] font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
            <Clock className="w-3 h-3 text-amber-600" />
            <span>Đang chờ</span>
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center space-x-1 text-[11px] font-medium text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
            <AlertCircle className="w-3 h-3 text-rose-600" />
            <span>Thất bại</span>
          </span>
        );
      default:
        return null;
    }
  };

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
        day: '2-digit',
        month: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-col h-[480px]">
      <div className="flex items-center justify-between mb-3 shrink-0">
        <div className="flex items-center space-x-2">
          <h2 className="font-semibold text-slate-900 text-base">Lịch sử tác vụ</h2>
          <span className="text-xs bg-slate-100 text-slate-600 font-semibold px-2 py-0.5 rounded-full">
            {jobs.length}
          </span>
        </div>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          title="Làm mới danh sách"
          className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
        >
          <RotateCcw className={`w-4 h-4 ${isLoading ? 'animate-spin text-indigo-600' : ''}`} />
        </button>
      </div>

      {/* List content */}
      <div className="overflow-y-auto flex-1 space-y-2 pr-1 custom-scrollbar">
        {jobs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400">
            <Video className="w-10 h-10 mb-2 stroke-1" />
            <p className="text-sm font-medium text-slate-600">Chưa có tác vụ nào</p>
            <p className="text-xs text-slate-400 mt-1 max-w-[200px]">
              Tải lên một video tiếng Trung ở trên để bắt đầu chuyển đổi
            </p>
          </div>
        ) : (
          jobs.map((job) => {
            const isSelected = job.id === selectedJobId;
            return (
              <div
                key={job.id}
                onClick={() => onSelectJob(job.id)}
                className={`p-3 rounded-xl border text-left cursor-pointer transition-all duration-150 ${
                  isSelected
                    ? 'border-indigo-500 bg-indigo-50/50 shadow-xs'
                    : 'border-slate-200/80 hover:border-slate-300 hover:bg-slate-50/70 bg-white'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <p
                    className={`text-xs font-semibold truncate ${
                      isSelected ? 'text-indigo-950' : 'text-slate-800'
                    }`}
                    title={job.original_filename}
                  >
                    {job.original_filename}
                  </p>
                  <span className="text-[10px] text-slate-400 shrink-0">
                    {formatDate(job.created_at)}
                  </span>
                </div>

                <div className="flex items-center justify-between mt-2 pt-1 border-t border-slate-100/80">
                  <div>{getStatusBadge(job.status, job.progress)}</div>
                  {job.status === 'processing' && (
                    <div className="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-indigo-600 rounded-full transition-all duration-300"
                        style={{ width: `${job.progress}%` }}
                      />
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

