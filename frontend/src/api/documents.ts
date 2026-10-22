import { apiClient } from './client';
import type { Document, DocumentAccessUpdate, DocumentUploadResponse } from '../types';

export const documentsApi = {
  /**
   * List all documents for the current tenant.
   */
  list: async (): Promise<Document[]> => {
    const response = await apiClient.get<Document[]>('/api/v1/documents/');
    return response.data;
  },

  /**
   * Upload a document with progress tracking.
   */
  upload: async (
    file: File,
    onProgress?: (percent: number) => void,
  ): Promise<DocumentUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<DocumentUploadResponse>(
      '/api/v1/documents/upload',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (event) => {
          if (onProgress && event.total) {
            const percent = Math.round((event.loaded * 100) / event.total);
            onProgress(percent);
          }
        },
      },
    );
    return response.data;
  },

  /**
   * Delete a document and all its chunks.
   */
  delete: async (documentId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/documents/${documentId}`);
  },

  /**
   * Set who can see a document (owner or admin only).
   */
  setAccess: async (documentId: string, access: DocumentAccessUpdate): Promise<Document> => {
    const response = await apiClient.put<Document>(`/api/v1/documents/${documentId}/access`, access);
    return response.data;
  },
};