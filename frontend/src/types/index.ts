// ─── Core Types ────────────────────────────────────────────────────────────────

export interface User {
  _id: string;
  username: string;
  email: string;
  role: "admin" | "technician" | "viewer";
  created_at: string;
  last_login: string | null;
}

export interface SampleMetadata {
  temperature?: number;
  volume_ml?: number;
  container_type?: string;
}

export type SampleType = "blood" | "urine" | "tissue" | "swab" | "serum" | "other";
export type SampleStatus = "received" | "processing" | "completed" | "rejected";
export type Priority = "routine" | "urgent" | "stat";

export interface Sample {
  _id: string;
  sample_id: string;
  name: string;
  type: SampleType;
  patient_id: string;
  patient_name: string;
  collected_by: string;
  collection_date: string;
  status: SampleStatus;
  priority: Priority;
  notes: string;
  metadata: SampleMetadata;
  created_at: string;
  updated_at: string;
  created_by: string;
  test_results?: TestResult[];
}

export type TestStatus = "pending" | "in_progress" | "completed" | "failed";
export type TestCategory = "hematology" | "biochemistry" | "microbiology" | "immunology" | "urinalysis";

export interface AIPrediction {
  predicted_value: number;
  confidence: number;
  risk_level: "low" | "medium" | "high";
  reference_range: { min: number; max: number; unit: string };
  model_version: string;
  predicted_at: string;
}

export interface TestResult {
  _id: string;
  sample_id: string;
  test_name: string;
  test_code: string;
  category: TestCategory;
  status: TestStatus;
  result_value?: number | string;
  result_unit: string;
  reference_range: { min: number; max: number };
  is_abnormal: boolean;
  ai_prediction?: AIPrediction;
  performed_by: string;
  performed_at: string;
  verified_by?: string;
  verified_at?: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface DashboardStats {
  samples: {
    total: number;
    by_status: Record<string, number>;
  };
  tests: {
    total: number;
    completed: number;
    pending: number;
    failed: number;
    by_status: Record<string, number>;
  };
  recent_samples: Partial<Sample>[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
}

export interface AuthTokens {
  token: string;
  username: string;
  role: string;
}
