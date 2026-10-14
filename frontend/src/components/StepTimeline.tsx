import React from 'react';
import { Check, Loader2, AlertCircle, Circle, Mic, Globe2, Volume2, Film } from 'lucide-react';
import { JobDetail, PIPELINE_STAGES, PipelineStageInfo } from '../types/job';

interface StepTimelineProps {
  job: JobDetail;
}

export const StepTimeline: React.FC<StepTimelineProps> = ({ job }) => {
  const getStageIcon = (key: string) => {
    switch (key) {
      case 'asr':
        return <Mic className="w-4 h-4" />;
      case 'translation':
        return <Globe2 className="w-4 h-4" />;
      case 'tts':
        return <Volume2 className="w-4 h-4" />;
      case 'render':
        return <Film className="w-4 h-4" />;
      default:
        return <Circle className="w-4 h-4" />;
    }
  };

  const getStageStatus = (stage: PipelineStageInfo, index: number) => {
    if (job.status === 'completed') {
      return 'completed';
    }

    if (job.status === 'failed') {
      if (job.stage === stage.key) return 'failed';
      const failedIndex = PIPELINE_STAGES.findIndex((s) => s.key === job.stage);
      if (failedIndex !== -1 && index < failedIndex) return 'completed';
      return 'pending';
    }

    if (job.status === 'processing') {
      const currentIndex = PIPELINE_STAGES.findIndex((s) => s.key === job.stage);
      if (currentIndex === -1) {
        return index === 0 ? 'active' : 'pending';
      }
      if (index < currentIndex) return 'completed';
      if (index === currentIndex) return 'active';
      return 'pending';
    }

    return 'pending';
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs">
      {/* Header and overall progress */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-semibold text-slate-900 text-sm">Tiến trình xử lý AI</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            {job.status === 'completed'
              ? 'Tất cả các bước đã hoàn tất thành công'
              : job.status === 'processing'
              ? `Đang chạy giai đoạn: ${job.stage ? job.stage.toUpperCase() : 'Khởi động'}`
              : job.status === 'failed'
              ? 'Quy trình xử lý gặp sự cố'
              : 'Đang xếp hàng chờ xử lý'}
          </p>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold tracking-tight text-slate-900">{job.progress}%</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden mb-6">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            job.status === 'failed'
              ? 'bg-rose-500'
              : job.status === 'completed'
              ? 'bg-emerald-500'
              : 'bg-indigo-600'
          }`}
          style={{ width: `${Math.max(job.progress, 5)}%` }}
        />
      </div>

      {/* 4 Pipeline Steps */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {PIPELINE_STAGES.map((stage, idx) => {
          const status = getStageStatus(stage, idx);

          return (
            <div
              key={stage.key}
              className={`p-3.5 rounded-xl border transition-all duration-200 relative ${
                status === 'completed'
                  ? 'border-emerald-200 bg-emerald-50/40 text-emerald-950'
                  : status === 'active'
                  ? 'border-indigo-400 bg-indigo-50/50 text-indigo-950 ring-2 ring-indigo-500/10 shadow-xs'
                  : status === 'failed'
                  ? 'border-rose-200 bg-rose-50/50 text-rose-950'
                  : 'border-slate-200/70 bg-slate-50/50 text-slate-500 opacity-70'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                    status === 'completed'
                      ? 'bg-emerald-500 text-white'
                      : status === 'active'
                      ? 'bg-indigo-600 text-white'
                      : status === 'failed'
                      ? 'bg-rose-500 text-white'
                      : 'bg-slate-200 text-slate-600'
                  }`}
                >
                  {getStageIcon(stage.key)}
                </div>

                {status === 'completed' && (
                  <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center">
                    <Check className="w-3 h-3 stroke-[3]" />
                  </span>
                )}
                {status === 'active' && (
                  <span className="w-5 h-5 flex items-center justify-center text-indigo-600">
                    <Loader2 className="w-4 h-4 animate-spin" />
                  </span>
                )}
                {status === 'failed' && (
                  <span className="w-5 h-5 rounded-full bg-rose-100 text-rose-700 flex items-center justify-center">
                    <AlertCircle className="w-3.5 h-3.5" />
                  </span>
                )}
              </div>

              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold">{stage.label}</span>
                </div>
                <p className="text-[11px] leading-relaxed text-slate-600 line-clamp-2">
                  {stage.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

