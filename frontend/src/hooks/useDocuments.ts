import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { documentsApi } from '../api/documents';
import { errorMessage } from '../api/client';
import type { DocumentAccessUpdate } from '../types';

const DOCUMENTS_KEY = ['documents'] as const;

export function useDocuments() {
  const queryClient = useQueryClient();

  const listQuery = useQuery({
    queryKey: [...DOCUMENTS_KEY],
    queryFn: () => documentsApi.list(),
    // Poll while any document is still processing.
    refetchInterval: (query) => {
      const docs = query.state.data ?? [];
      return docs.some((d) => d.status === 'processing') ? 5000 : false;
    },
  });

  const uploadMutation = useMutation({
    mutationFn: ({ file, onProgress }: { file: File; onProgress?: (p: number) => void }) =>
      documentsApi.upload(file, onProgress),
    onSuccess: (data) => {
      toast.success(
        data.chunk_count > 0
          ? `Document uploaded — ${data.chunk_count} chunks indexed`
          : 'Document uploaded and processing',
      );
      queryClient.invalidateQueries({ queryKey: [...DOCUMENTS_KEY] });
    },
    onError: (error) => {
      toast.error(errorMessage(error, 'Failed to upload document'));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (documentId: string) => documentsApi.delete(documentId),
    onSuccess: () => {
      toast.success('Document deleted');
      queryClient.invalidateQueries({ queryKey: [...DOCUMENTS_KEY] });
    },
    onError: (error) => {
      toast.error(errorMessage(error, 'Failed to delete document'));
    },
  });

  const accessMutation = useMutation({
    mutationFn: ({ documentId, access }: { documentId: string; access: DocumentAccessUpdate }) =>
      documentsApi.setAccess(documentId, access),
    onSuccess: () => {
      toast.success('Sharing updated');
      queryClient.invalidateQueries({ queryKey: [...DOCUMENTS_KEY] });
    },
    onError: (error) => {
      toast.error(errorMessage(error, 'Failed to update sharing'));
    },
  });

  return {
    documents: listQuery.data ?? [],
    isLoading: listQuery.isLoading,
    isError: listQuery.isError,
    refetch: listQuery.refetch,
    upload: uploadMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
    deleteDocument: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
    setAccess: accessMutation.mutateAsync,
    isSavingAccess: accessMutation.isPending,
  };
}