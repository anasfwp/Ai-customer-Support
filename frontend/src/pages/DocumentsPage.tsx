import { useState } from 'react';
import { RefreshCw } from 'lucide-react';
import Layout from '../components/layout/Layout';
import DocumentUpload from '../components/documents/DocumentUpload';
import DocumentList from '../components/documents/DocumentList';
import { useDocuments } from '../hooks/useDocuments';

export default function DocumentsPage() {
  const {
    documents,
    isLoading,
    refetch,
    upload,
    isUploading,
    deleteDocument,
  } = useDocuments();

  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (documentId: string) => {
    if (!confirm('Delete this document and all its indexed chunks?')) return;
    setDeletingId(documentId);
    try {
      await deleteDocument(documentId);
    } finally {
      setDeletingId(null);
    }
  };

  const handleUpload = async (file: File, onProgress: (p: number) => void) => {
    await upload({ file, onProgress });
  };

  return (
    <Layout title="Documents">
      <div className="mx-auto max-w-4xl space-y-8 px-4 py-6 sm:px-6 sm:py-8">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              Documents
            </h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Upload and manage the knowledge base for your workspace.
            </p>
          </div>
          <button
            type="button"
            onClick={() => refetch()}
            aria-label="Refresh list"
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>

        {/* Upload zone */}
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Upload
          </h2>
          <DocumentUpload onUpload={handleUpload} isUploading={isUploading} />
        </section>

        {/* Document list */}
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Uploaded documents
            </h2>
            {documents.length > 0 && (
              <span className="text-xs text-slate-400 dark:text-slate-500">
                {documents.length}{' '}
                {documents.length === 1 ? 'document' : 'documents'}
              </span>
            )}
          </div>
          <DocumentList
            documents={documents}
            isLoading={isLoading}
            deletingId={deletingId}
            onDelete={handleDelete}
          />
        </section>
      </div>
    </Layout>
  );
}