import React from 'react';
import { Languages, Server } from 'lucide-react';

interface HeaderProps {
  isHealthy: boolean | null;
}

export const Header: React.FC<HeaderProps> = ({ isHealthy }) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-700 flex items-center justify-center text-white shadow-sm">
            <Languages className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-slate-900 text-lg tracking-tight">DubFlow Studio</span>
              <span className="text-[11px] font-semibold uppercase tracking-wider bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full border border-indigo-200/60">
                ZH ➔ VI
              </span>
            </div>
            <p className="text-xs text-slate-500">Hệ thống lồng tiếng video tiếng Trung sang tiếng Việt</p>
          </div>
        </div>

        {/* Status Indicators */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
            <span className="relative flex h-2 w-2">
              {isHealthy === true && (
                <>
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </>
              )}
              {isHealthy === false && (
                <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
              )}
              {isHealthy === null && (
                <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-400 animate-pulse"></span>
              )}
            </span>
            <span className="font-medium text-slate-700">
              {isHealthy === true ? 'Hệ thống sẵn sàng' : isHealthy === false ? 'Mất kết nối máy chủ' : 'Đang kiểm tra...'}
            </span>
          </div>

          <div className="hidden sm:flex items-center space-x-1 text-slate-400 text-xs">
            <Server className="w-3.5 h-3.5" />
            <span>FastAPI + Celery + PyTorch</span>
          </div>
        </div>
      </div>
    </header>
  );
};
