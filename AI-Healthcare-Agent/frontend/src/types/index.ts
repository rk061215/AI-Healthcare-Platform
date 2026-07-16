// ──────────────────────────────────────────────
// Auth
// ──────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "patient" | "doctor";
  phone: string | null;
}

export interface PatientUser extends User {
  role: "patient";
  date_of_birth: string | null;
  gender: string | null;
  is_active: boolean;
}

export interface DoctorUser extends User {
  role: "doctor";
  specialization: string | null;
  license_number: string | null;
  hospital_name: string | null;
  years_of_experience: number | null;
  is_active: boolean;
}

export type UserProfile = PatientUser | DoctorUser;

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
  role: "patient" | "doctor";
  remember_me?: boolean;
}

export interface PatientRegisterRequest {
  email: string;
  password: string;
  confirm_password: string;
  full_name: string;
  phone?: string;
  date_of_birth?: string;
  gender?: string;
  terms_accepted: boolean;
}

export interface DoctorRegisterRequest {
  email: string;
  password: string;
  confirm_password: string;
  full_name: string;
  phone?: string;
  license_number?: string;
  hospital_name?: string;
  specialization?: string;
  years_of_experience?: number;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface LogoutRequest {
  refresh_token: string;
}

// ──────────────────────────────────────────────
// Patient
// ──────────────────────────────────────────────
export interface PatientProfile {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  date_of_birth: string | null;
  gender: string | null;
  blood_group: string | null;
  address: string | null;
  emergency_contact: string | null;
  emergency_phone: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Doctor {
  id: string;
  full_name: string;
  specialization: string | null;
}

// ──────────────────────────────────────────────
// Medicine
// ──────────────────────────────────────────────
export interface Medicine {
  id: string;
  report_id: string;
  patient_id: string;
  name: string;
  dosage: string | null;
  frequency: string | null;
  duration: string | null;
  route: string | null;
  instructions: string | null;
  start_date: string | null;
  end_date: string | null;
  is_active: boolean;
  created_at: string;
  adherence_rate?: number;
  total_doses?: number;
  taken_doses?: number;
  missed_doses?: number;
}

// ──────────────────────────────────────────────
// Report
// ──────────────────────────────────────────────
export interface Report {
  id: string;
  title: string | null;
  file_type: string | null;
  status: string;
  ocr_text: string | null;
  extracted_data: Record<string, unknown> | null;
  uploaded_at: string;
  processed_at: string | null;
}

// ──────────────────────────────────────────────
// Chat
// ──────────────────────────────────────────────
export interface ChatSource {
  id: number;
  document_id: string;
  section: string;
  source: string;
  text_snippet: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  message: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface ChatResponse {
  reply: string;
  sources: ChatSource[] | null;
  suggested_questions?: string[];
  metadata: Record<string, unknown> | null;
}

// ──────────────────────────────────────────────
// Adherence
// ──────────────────────────────────────────────
export interface AdherenceStats {
  total_doses: number;
  taken_doses: number;
  missed_doses: number;
  skipped_doses: number;
  pending_doses: number;
  adherence_rate: number;
}

export interface TodaySchedule {
  medicine_id: string;
  medicine_name: string;
  dosage: string | null;
  frequency: string | null;
  scheduled_time: string;
  status: string;
  is_taken: boolean;
}

// ──────────────────────────────────────────────
// Emergency
// ──────────────────────────────────────────────
export interface EmergencyAlert {
  id: string;
  patient_id: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  symptoms: string;
  analysis: string | null;
  is_acknowledged: boolean;
  acknowledged_by: string | null;
  created_at: string;
}

export interface SymptomCheckResponse {
  risk_level: string;
  analysis: string;
  recommendations: string[];
  disclaimer: string;
}

// ──────────────────────────────────────────────
// Appointment
// ──────────────────────────────────────────────
export interface Appointment {
  id: string;
  patient_id: string;
  doctor_id: string;
  title: string | null;
  description: string | null;
  scheduled_at: string;
  status: string;
  follow_up_notes: string | null;
  created_at: string;
}

// ──────────────────────────────────────────────
// API Response
// ──────────────────────────────────────────────
export interface ApiError {
  error: string;
  detail: string | null;
}
