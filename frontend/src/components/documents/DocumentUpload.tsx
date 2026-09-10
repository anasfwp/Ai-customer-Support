import { useCallback, useRef, useState, type DragEvent } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileText, X, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { cn } from '../../utils/cn';

interface DocumentUploadProps {
  onUpload: (file: File, onProgress: (p: number) => void) => Promise<void>;
  isUploading: boolean;
}

const ACCEPTED_EXT = ['.pdf', '.docx', '.txt'];
const MAX_SIZE_MB = 25;

export default function DocumentUpload({ onUpload, isUploading }: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);

  const validateFile = (file: File): string | null => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_EXT.includes(ext)) {
      return `Unsupported file type. Use: ${ACCEPTED_EXT.join(', ')}`;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File is too large. Max size: ${MAX_SIZE_MB}MB`;
    }
    return null;
  };

  const handleFile = useCallback((file: File) => {
    const error = validateFile(file);
    if (error) {
      toast.error(error);
      return;
    }
    setSelectedFile(file);
    setProgress(0);
  }, []);

  const handleDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setIsDragging(false);
      const file = event.dataTransfer.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleDragOver = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
  }, []);

  const handleBrowseClick = () => inputRef.current?.click();

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) handleFile(file);
    event.target.value = '';
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    try {
      await onUpload(selectedFile, setProgress);
      setSelectedFile(null);
      setProgress(0);
    } catch {
      // Error already handled by toast in useDocuments hook
    }
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setProgress(0);
  };

  return (
    <div className="space-y-3">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleBrowseClick}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') handleBrowseClick();
        }}
        className={cn(
          'relative flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-10 text-center transition',
          isDragging
            ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30'
            : 'border-slate-300 bg-slate-50 hover:border-indigo-400 hover:bg-indigo-50/50 dark:border-slate-700 dark:bg-slate-900 dark:hover:border-indigo-600 dark:hover:bg-indigo-950/20',
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXT.join(',')}
          onChange={handleInputChange}
          className="hidden"
        />

        <motion.div
          animate={{ scale: isDragging ? 1.08 : 1 }}
          transition={{ duration: 0.15 }}
          className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/20"
        >
          <Upload className="h-5 w-5 text-white" />
        </motion.div>

        <p className="mt-4 text-sm font-medium text-slate-900 dark:text-slate-100">
          {isDragging ? 'Drop to upload' : 'Drag & drop a file, or click to browse'}
        </p>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Supports PDF, DOCX, TXT · up to {MAX_SIZE_MB}MB
        </p>
      </div>

      {/* Selected file preview */}
      {selectedFile && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-50 dark:bg-indigo-950/40">
              <FileText className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">
                {selectedFile.name}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </p>
            </div>

            {!isUploading && (
              <button
                type="button"
                onClick={clearSelection}
                aria-label="Remove file"
                className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
              >
                <X className="h-4 w-4" />
              </button>
            )}

            {isUploading && (
              <div className="flex items-center gap-2 text-xs font-medium text-indigo-600 dark:text-indigo-400">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                {progress}%
              </div>
            )}
          </div>

          {/* Progress bar */}
          {isUploading && (
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.2 }}
                className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500"
              />
            </div>
          )}

          {/* Upload button */}
          {!isUploading && (
            <button
              type="button"
              onClick={handleUpload}
              className="mt-3 w-full rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-indigo-700"
            >
              Upload & process
            </button>
          )}
        </motion.div>
      )}
    </div>
  );
}