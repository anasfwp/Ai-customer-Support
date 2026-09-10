// ============================================================
// AUTH
// ============================================================

export interface RegisterRequest {
  email: string;
  password: string;
  company_name: string;
}

export interface RegisterResponse {
  user_id: string;
  tenant_id: string;
  access_token: string;
  token_type: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  email: string;
  tenant_id: string;
  is_admin: boolean;
}

// ============================================================
// DOCUMENTS
// ============================================================

export type DocumentStatus = 'processing' | 'ready' | 'failed';

export interface Document {
  id: string;
  filename: string;
  status: DocumentStatus;
  chunk_count: number;
  created_at: string;
}

export interface DocumentUploadResponse {
  document_id: string;
  status: string;
  chunk_count: number;
}

// ============================================================
// CHAT
// ============================================================

export interface Citation {
  document_id: string;
  document_name: string;
  section: string;
  page: number;
  similarity?: number;
}

export interface ChatQueryRequest {
  question: string;
  session_id?: string | null;
}

export interface ChatQueryResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
  fallback: boolean;
  session_id: string;
  chat_log_id?: string;
  id?: string;
}

export interface ChatHistoryItem {
  id: string;
  question: string;
  answer: string;
  citations: Citation[];
  confidence: string;
  fallback: boolean;
  session_id: string;
  created_at: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations: Citation[];
  confidence?: number;
  fallback?: boolean;
  sessionId?: string;
  chatLogId?: string;
  createdAt: string;
  pending?: boolean;
  feedback?: 'helpful' | 'unhelpful' | null;
}

// ============================================================
// FEEDBACK
// ============================================================

export interface FeedbackRequest {
  chat_log_id: string;
  helpful: boolean;
  comment?: string;
}

export interface FeedbackStats {
  total_feedback: number;
  helpful: number;
  unhelpful: number;
  satisfaction_rate: number;
}

// ============================================================
// ANALYTICS
// ============================================================

export interface UsageStats {
  total_queries: number;
  fallback_rate: number;
  total_documents: number;
  top_questions: Array<{ question: string; count: number }>;
}

export interface UnansweredQuestion {
  question: string;
  created_at: string;
}

// ============================================================
// API ERRORS
// ============================================================

export interface ApiError {
  detail: string | Array<{ msg: string; loc: string[] }>;
}