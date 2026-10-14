import React, { useRef, useState } from 'react';
import { UploadCloud, FileVideo, AlertCircle, CheckCircle2, Mic2, Sparkles } from 'lucide-react';
import { uploadVideo } from '../api/client';
import { JobDetail } from '../types/job';

interface UploadCardProps {
  onUploadSuccess: (job: JobDetail) => void;
}

const MAX_SIZE_MB = 500;
const ACCEPTED_FORMATS = ['.mp4', '.mov', '.mkv', '.avi', '.webm'];

export const UploadCard: React.FC<UploadCardProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [voicePreset, setVoicePreset] = useState('female_gentle');
  const [uploading, setUploading] = useState(false);
  const [uploadPercent, setUploadPercent] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): boolean => {
    setErrorMessage(null);
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_FORMATS.includes(ext)) {
      setErrorMessage(`Định dạng ${ext} không hỗ trợ. Vui lòng chọn tệp: ${ACCEPTED_FORMATS.join(', ')}`);
      return false;
    }
    const sizeMb = file.size / (1024 * 1024);
    if (sizeMb > MAX_SIZE_MB) {
      setErrorMessage(`Dung lượng video (${sizeMb.toFixed(1)}MB) vượt quá giới hạn ${MAX_SIZE_MB}MB.`);
      return false;
    }
    return true;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadPercent(0);
    setErrorMessage(null);

    try {
      const job = await uploadVideo(selectedFile, (percent) => {
        setUploadPercent(percent);
      });
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      onUploadSuccess(job);
    } catch (err: any) {
      setErrorMessage(err.message || 'Lỗi không xác định khi tải video lên');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-slate-900 flex items-center space-x-2 text-base">
          <FileVideo className="w-5 h-5 text-indigo-600" />
          <span>Tải lên video tiếng Trung</span>
        </h2>
        <span className="text-xs text-slate-500 font-medium">Tối đa 500MB</span>
      </div>

      {/* Drag & Drop Area */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-150 ${
          isDragging
            ? 'border-indigo-500 bg-indigo-50/60'
            : selectedFile
            ? 'border-indigo-400 bg-indigo-50/20'
            : 'border-slate-300 hover:border-slate-400 bg-slate-50/50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_FORMATS.join(',')}
          onChange={handleFileChange}
          disabled={uploading}
          className="hidden"
        />

        {selectedFile ? (
          <div className="space-y-2">
            <div className="w-12 h-12 mx-auto rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <p className="font-medium text-slate-900 text-sm truncate max-w-xs mx-auto">
                {selectedFile.name}
              </p>
              <p className="text-xs text-slate-500">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
            <p className="text-xs text-indigo-600 font-medium hover:underline pt-1">
              Nhấp để chọn file khác
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="w-12 h-12 mx-auto rounded-full bg-slate-100 flex items-center justify-center text-slate-500">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-800">
                Kéo thả file video vào đây hoặc <span className="text-indigo-600">Duyệt file</span>
              </p>
              <p className="text-xs text-slate-400 mt-1">
                Hỗ trợ định dạng: MP4, MOV, MKV, WebM
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Voice Preset Selection */}
      <div className="mt-4 pt-4 border-t border-slate-100 space-y-2">
        <label className="block text-xs font-semibold text-slate-700 flex items-center justify-between">
          <span className="flex items-center space-x-1.5">
            <Mic2 className="w-3.5 h-3.5 text-indigo-600" />
            <span>Giọng đọc thuyết minh</span>
          </span>
          <span className="text-[10px] text-slate-400 font-normal">Tiếng Việt tự nhiên</span>
        </label>
        <select
          value={voicePreset}
          onChange={(e) => setVoicePreset(e.target.value)}
          disabled={uploading}
          className="w-full text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-800 font-medium focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
        >
          <option value="female_gentle">Nữ miền Bắc - Dịu dàng, tự nhiên (Mặc định)</option>
          <option value="male_narrator">Nam miền Bắc - Truyền cảm, phóng sự</option>
          <option value="female_south">Nữ miền Nam - Trẻ trung, năng động</option>
          <option value="male_south">Nam miền Nam - Trầm ấm, rõ chữ</option>
        </select>
      </div>

      {/* Error alert */}
      {errorMessage && (
        <div className="mt-3 p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start space-x-2 text-xs text-rose-700">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Uploading progress */}
      {uploading && (
        <div className="mt-4 space-y-1.5">
          <div className="flex justify-between text-xs font-medium text-slate-600">
            <span>Đang tải tệp lên máy chủ...</span>
            <span>{uploadPercent}%</span>
          </div>
          <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-indigo-600 rounded-full transition-all duration-150"
              style={{ width: `${uploadPercent}%` }}
            />
          </div>
        </div>
      )}

      {/* Submit Button */}
      <button
        onClick={handleUpload}
        disabled={!selectedFile || uploading}
        className={`mt-4 w-full py-2.5 px-4 rounded-xl font-medium text-sm flex items-center justify-center space-x-2 transition-all shadow-xs ${
          !selectedFile || uploading
            ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
            : 'bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white cursor-pointer shadow-indigo-100'
        }`}
      >
        <Sparkles className="w-4 h-4" />
        <span>{uploading ? 'Đang tải lên...' : 'Bắt đầu lồng tiếng tự động'}</span>
      </button>
    </div>
  );
};

