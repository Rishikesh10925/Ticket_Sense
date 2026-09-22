const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "end_user" | "department_engineer" | "admin";
  department_id: string | null;
}

export interface Department {
  id: string;
  name: string;
  confidence_threshold: number;
}

export interface ConfidenceFeatures {
  retrieval_relevance: number;
  ticket_resolution_similarity: number;
  document_freshness: number;
  ocr_confidence: number;
  category_risk: number;
}

export interface Citation {
  source_type: "knowledge_base" | "resolved_ticket";
  source_id: string;
  title: string;
}

export interface Ticket {
  id: string;
  submitted_by: string;
  department_id: string | null;
  subject: string;
  description: string;
  attachment_path: string | null;
  attachment_type: string | null;
  // Set once the pipeline's extract node has run — null while still processing, and
  // also null if extraction found no readable text. Unlike ai_draft_reply, visible to
  // every role that can see the ticket (see build_ticket_out).
  attachment_text: string | null;
  ocr_confidence: number | null;
  priority: string | null;
  sentiment: string | null;
  status: string;
  // Null for the end_user role even once a draft exists — see
  // app/schemas/tickets.py's build_ticket_out.
  ai_draft_reply: string | null;
  ai_draft_citations: Citation[] | null;
  // Null for the end_user role, same reason as the draft fields above — a confidence
  // judgment about a draft no one shows them is meaningless to expose.
  confidence_score: number | null;
  confidence_features: ConfidenceFeatures | null;
  confidence_threshold: number | null;
  created_at: string;
  updated_at: string;
}

export interface Evidence {
  source_type: "knowledge_base" | "resolved_ticket";
  source_id: string;
  title: string;
  snippet: string;
  distance: number;
}

export interface KnowledgeBaseArticle {
  id: string;
  department_id: string;
  title: string;
  source_url: string | null;
  updated_at: string;
}

export interface Escalation {
  id: string;
  ticket_id: string;
  reason: string;
  confidence_score: number | null;
  escalated_to: string | null;
  resolved_at: string | null;
  created_at: string;
}

export type FeedbackAction = "accept" | "edit" | "reject" | "escalate";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body.detail ?? response.statusText;
  } catch {
    return response.statusText;
  }
}

function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

export async function register(email: string, fullName: string, password: string): Promise<User> {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, full_name: fullName, password }),
  });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res.json();
}

export async function login(email: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  const data = await res.json();
  return data.access_token as string;
}

export async function getMe(token: string): Promise<User> {
  const res = await fetch(`${API_URL}/auth/me`, { headers: authHeaders(token) });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res.json();
}

export async function createTicket(
  token: string,
  subject: string,
  description: string,
  attachment: File | null
): Promise<Ticket> {
  const form = new FormData();
  form.set("subject", subject);
  form.set("description", description);
  if (attachment) form.set("attachment", attachment);

  const res = await fetch(`${API_URL}/tickets`, {
    method: "POST",
    headers: authHeaders(token),
    body: form,
  });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res.json();
}

export async function listTickets(
  token: string,
  filters: { status?: string; priority?: string; departmentId?: string; sort?: string } = {}
): Promise<Ticket[]> {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.priority) params.set("priority", filters.priority);
  if (filters.departmentId) params.set("department_id", filters.departmentId);
  if (filters.sort) params.set("sort", filters.sort);
  const query = params.toString();

  const res = await fetch(`${API_URL}/tickets${query ? `?${query}` : ""}`, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res.json();
}

export async function getTicket(token: string, id: string): Promise<Ticket> {
  const res = await fetch(`${API_URL}/tickets/${id}`, { headers: authHeaders(token) });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res.json();
}

export async function listDepartments(token: string): Promise<Department[]> {
  const res = await fetch(`${API_URL}/departments`, { headers: authHeaders(token) });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res.json();
}

export async function getTicketAttachment(token: string, id: string): Promise<Blob> {
  // The endpoint is auth-gated (same per-ticket access check as the ticket itself),
  // so it can't be used as a plain <img src>/<a href> URL — the caller fetches the
  // blob and builds an object URL from it instead.
  const res = await fetch(`${API_URL}/tickets/${id}/attachment`, { headers: authHeaders(token) });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res.blob();
}

export async function getTicketEvidence(token: string, id: string): Promise<Evidence[]> {
  const res = await fetch(`${API_URL}/tickets/${id}/evidence`, { headers: authHeaders(token) });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res.json();
}

export async function listUsers(token: string): Promise<User[]> {
  const res = await fetch(`${API_URL}/users`, { headers: authHeaders(token) });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res.json();
}

export async function listKnowledgeBase(token: string): Promise<KnowledgeBaseArticle[]> {
  const res = await fetch(`${API_URL}/knowledge-base`, { headers: authHeaders(token) });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res.json();
}

export async function getTicketEscalation(token: string, id: string): Promise<Escalation> {
  const res = await fetch(`${API_URL}/tickets/${id}/escalation`, { headers: authHeaders(token) });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res.json();
}

export async function submitTicketFeedback(
  token: string,
  id: string,
  action: FeedbackAction,
  details: { editedReply?: string; rejectReason?: string } = {}
): Promise<Ticket> {
  const res = await fetch(`${API_URL}/tickets/${id}/feedback`, {
    method: "POST",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify({
      action,
      edited_reply: details.editedReply ?? null,
      reject_reason: details.rejectReason ?? null,
    }),
  });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res.json();
}

export async function updateDepartmentThreshold(
  token: string,
  departmentId: string,
  confidenceThreshold: number
): Promise<Department> {
  const res = await fetch(`${API_URL}/departments/${departmentId}/threshold`, {
    method: "PATCH",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify({ confidence_threshold: confidenceThreshold }),
  });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res.json();
}

export interface ReviewActionCounts {
  accept: number;
  edit: number;
  reject: number;
  escalate: number;
}

export interface ConfidenceBucket {
  label: string;
  count: number;
}

export interface DepartmentBreakdown {
  department_id: string;
  department_name: string;
  total_tickets: number;
  scored_tickets: number;
  escalation_rate: number | null;
  avg_confidence: number | null;
}

export interface FeedbackSourceSummary {
  total: number;
  review_actions: ReviewActionCounts;
  agreement_rate: number | null;
}

// `in_review` is the reviewer's department queue count (drafted tickets awaiting
// anyone's action there), not a per-person figure — a ticket has no assigned
// reviewer until someone acts on it. See backend/app/schemas/analytics.py.
export interface ReviewerBreakdown {
  reviewer_id: string;
  reviewer_name: string;
  reviewer_email: string;
  department_name: string;
  resolved: number;
  rejected: number;
  escalated: number;
  in_review: number;
}

export interface AnalyticsSummary {
  total_tickets: number;
  by_status: Record<string, number>;
  scored_tickets: number;
  escalation_rate: number | null;
  confidence_distribution: ConfidenceBucket[];
  by_department: DepartmentBreakdown[];
  by_reviewer: ReviewerBreakdown[];
  real_feedback: FeedbackSourceSummary;
  synthetic_feedback: FeedbackSourceSummary;
}

export async function getAnalyticsSummary(token: string): Promise<AnalyticsSummary> {
  const res = await fetch(`${API_URL}/analytics/summary`, { headers: authHeaders(token) });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res.json();
}
