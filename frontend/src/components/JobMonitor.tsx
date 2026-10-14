import React from 'react';
import { AlertTriangle, Sparkles } from 'lucide-react';
import { JobDetail } from '../types/job';
import { StepTimeline } from './StepTimeline';
import { VideoPlayer } from './VideoPlayer';

interface JobMonitorProps {
  job: JobDetail | null;
  isLoading?: boolean;
}

export const JobMonitor: React.FC<JobMonitorProps> = ({ job }) => {
  if (!job) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center h-[720px] flex flex-col items-center justify-center text-slate-400 shadow-xs">
        <div className="w-16 h-16 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mb-4">
          <Sparkles className="w-8 h-8" />
        </div>
        <h3 className="text-base font-semibold text-slate-800">Chưa chọn tác vụ nào</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">
          Tải lên video tiếng Trung mới ở cột bên trái hoặc nhấp chọn một tác vụ trong lịch sử để xem tiến trình và kết quả.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Failure alert banner */}
      {job.status === 'failed' && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-start space-x-3 text-rose-800 text-xs">
          <AlertTriangle className="w-5 h-5 shrink-0 text-rose-600 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-rose-900">Quá trình lồng tiếng bị gián đoạn</p>
            <p className="text-rose-700 leading-relaxed font-mono">
              {job.error_message || 'Lỗi không xác định trong quá trình xử lý.'}
            </p>
          </div>
        </div>
      )}

      {/* 4 Steps Timeline Tracker */}
      <StepTimeline job={job} />

      {/* Video Player & Actions */}
      <VideoPlayer job={job} />
    </div>
  );
};
