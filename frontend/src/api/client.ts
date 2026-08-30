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
}

export interface Ticket {
  id: string;
  submitted_by: string;
  department_id: string | null;
  subject: string;
  description: string;
  attachment_path: string | null;
  attachment_type: string | null;
  priority: string | null;
  sentiment: string | null;
  status: string;
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

export async function getTicketEvidence(token: string, id: string): Promise<Evidence[]> {
  const res = await fetch(`${API_URL}/tickets/${id}/evidence`, { headers: authHeaders(token) });
  if (!res.ok) throw new ApiError(res.status, await parseErrorDetail(res));
  return res.json();
}
