import React, { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { UploadCard } from './components/UploadCard';
import { HistoryList } from './components/HistoryList';
import { JobMonitor } from './components/JobMonitor';
import { fetchHealth, fetchJobDetail, fetchJobs } from './api/client';
import { JobDetail, JobSummary } from './types/job';

export const App: React.FC = () => {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [activeJobDetail, setActiveJobDetail] = useState<JobDetail | null>(null);
  const [isLoadingJobs, setIsLoadingJobs] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  // Check backend server health
  useEffect(() => {
    fetchHealth()
      .then(() => setIsHealthy(true))
      .catch(() => setIsHealthy(false));
  }, []);

  // Fetch job list
  const loadJobs = async (autoSelectLatest = false) => {
    setIsLoadingJobs(true);
    try {
      const data = await fetchJobs(50);
      setJobs(data);
      if (autoSelectLatest && data.length > 0 && !selectedJobId) {
        setSelectedJobId(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load jobs list:', err);
    } finally {
      setIsLoadingJobs(false);
    }
  };

  useEffect(() => {
    loadJobs(true);
  }, []);

  // Fetch selected job details
  useEffect(() => {
    if (!selectedJobId) {
      setActiveJobDetail(null);
      return;
    }

    let isSubscribed = true;
    setIsLoadingDetail(true);

    fetchJobDetail(selectedJobId)
      .then((detail) => {
        if (isSubscribed) {
          setActiveJobDetail(detail);
        }
      })
      .catch((err) => {
        console.error('Failed to load job detail:', err);
      })
      .finally(() => {
        if (isSubscribed) {
          setIsLoadingDetail(false);
        }
      });

    return () => {
      isSubscribed = false;
    };
  }, [selectedJobId]);

  // Real-time polling when active job is processing or queued
  useEffect(() => {
    if (!selectedJobId || !activeJobDetail) return;
    if (activeJobDetail.status !== 'processing' && activeJobDetail.status !== 'queued') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const updated = await fetchJobDetail(selectedJobId);
        setActiveJobDetail(updated);

        // Also update the job in the history list
        setJobs((prev) =>
          prev.map((j) =>
            j.id === updated.id
              ? {
                  ...j,
                  status: updated.status,
                  stage: updated.stage,
                  progress: updated.progress,
                }
              : j
          )
        );

        if (updated.status === 'completed' || updated.status === 'failed') {
          clearInterval(interval);
          loadJobs();
        }
      } catch (err) {
        console.error('Error polling job update:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [selectedJobId, activeJobDetail?.status]);

  const handleUploadSuccess = (newJob: JobDetail) => {
    // Add to top of list
    setJobs((prev) => [newJob, ...prev]);
    // Select it as active
    setSelectedJobId(newJob.id);
    setActiveJobDetail(newJob);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900">
      <Header isHealthy={isHealthy} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Option B: 2-Column Dashboard Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column (5 cols / ~40%): Upload Card + Recent History */}
          <div className="lg:col-span-5 space-y-6">
            <UploadCard onUploadSuccess={handleUploadSuccess} />
            <HistoryList
              jobs={jobs}
              selectedJobId={selectedJobId}
              onSelectJob={(id) => setSelectedJobId(id)}
              onRefresh={() => loadJobs(false)}
              isLoading={isLoadingJobs}
            />
          </div>

          {/* Right Column (7 cols / ~60%): Active Job Monitor + Steps Timeline + Video Player */}
          <div className="lg:col-span-7">
            <JobMonitor job={activeJobDetail} isLoading={isLoadingDetail} />
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-400">
        <p>DubFlow Studio • Hệ thống lồng tiếng video tự động Trung ➔ Việt với PyTorch, Celery & FFmpeg</p>
      </footer>
    </div>
  );
};

export default App;
