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

export interface TeamMember {
  id: string;
  email: string;
  is_admin: boolean;
  created_at: string;
}

export interface AddMemberRequest {
  email: string;
  password: string;
  is_admin: boolean;
}

// ============================================================
// DOCUMENTS
// ============================================================

export type DocumentStatus = 'processing' | 'ready' | 'failed';

/** everyone: the whole company; restricted: only the owner, admins and `shared_with` users */
export type DocumentVisibility = 'everyone' | 'restricted';

export interface Document {
  id: string;
  filename: string;
  status: DocumentStatus;
  chunk_count: number;
  created_at: string;
  visibility: DocumentVisibility;
  owner_email: string | null;
  /** whether the current user may change sharing or delete it */
  can_manage: boolean;
  /** user ids; only filled in when can_manage */
  shared_with: string[];
}

export interface DocumentAccessUpdate {
  visibility: DocumentVisibility;
  user_ids: string[];
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
  /** the standalone query a follow-up was rewritten to; null when searched as asked */
  search_query?: string | null;
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
  searchQuery?: string | null;
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