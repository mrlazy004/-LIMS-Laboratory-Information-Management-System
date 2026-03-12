import type {
  ApiResponse, AuthTokens, Sample, TestResult,
  DashboardStats, PaginatedResponse
} from "../types/index.js";

const BASE_URL = "http://localhost:5000/api";

// ─── HTTP Client ───────────────────────────────────────────────────────────────
async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = localStorage.getItem("lims_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  const json = await res.json();
  if (!res.ok && res.status === 401) {
    localStorage.removeItem("lims_token");
    localStorage.removeItem("lims_user");
    window.location.hash = "#/login";
  }
  return json;
}

const get = <T>(path: string) => request<T>(path, { method: "GET" });
const post = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });
const put = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "PUT", body: JSON.stringify(body) });
const del = <T>(path: string) => request<T>(path, { method: "DELETE" });

// ─── Auth API ──────────────────────────────────────────────────────────────────
export const authApi = {
  login: (username: string, password: string) =>
    post<AuthTokens>("/auth/login", { username, password }),
  register: (username: string, email: string, password: string, role = "technician") =>
    post<AuthTokens>("/auth/register", { username, email, password, role }),
  me: () => get("/auth/me"),
};

// ─── Samples API ───────────────────────────────────────────────────────────────
export const samplesApi = {
  list: (params?: Record<string, string | number>) => {
    const qs = params ? "?" + new URLSearchParams(params as Record<string, string>).toString() : "";
    return get<PaginatedResponse<Sample>>(`/samples${qs}`);
  },
  get: (sampleId: string) => get<Sample>(`/samples/${sampleId}`),
  create: (data: Partial<Sample>) => post<Sample>("/samples", data),
  update: (sampleId: string, data: Partial<Sample>) => put<Sample>(`/samples/${sampleId}`, data),
  delete: (sampleId: string) => del(`/samples/${sampleId}`),
  stats: () => get<DashboardStats>("/samples/stats/summary"),
};

// ─── Tests API ─────────────────────────────────────────────────────────────────
export const testsApi = {
  list: (params?: Record<string, string | number>) => {
    const qs = params ? "?" + new URLSearchParams(params as Record<string, string>).toString() : "";
    return get<PaginatedResponse<TestResult>>(`/tests${qs}`);
  },
  get: (testId: string) => get<TestResult>(`/tests/${testId}`),
  create: (data: Partial<TestResult>) => post<TestResult>("/tests", data),
  update: (testId: string, data: Partial<TestResult>) => put<TestResult>(`/tests/${testId}`, data),
  delete: (testId: string) => del(`/tests/${testId}`),
  predict: (sampleId: string, testCode: string) =>
    post("/tests/predict", { sample_id: sampleId, test_code: testCode }),
};
