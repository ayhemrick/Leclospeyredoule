/** Shapes returned by the API, mirroring the Pydantic schemas. */

export type Locale = 'fr' | 'en';

/** A string the API sends in both site languages. */
export interface LocalizedString {
  fr: string;
  en: string;
}

export type GuideCategory = 'arrival' | 'house' | 'practical' | 'rules' | 'local_tips';
export type Visibility = 'public' | 'guest';
export type AttractionCategory = 'heritage' | 'wine' | 'nature' | 'gastronomy' | 'family';
export type AdminRole = 'owner' | 'editor';
export type RotationReason = 'initial' | 'scheduled' | 'manual';

export interface GuideSection {
  id: string;
  slug: string;
  category: GuideCategory;
  visibility: Visibility;
  position: number;
  icon: string | null;
  title: LocalizedString;
  body: LocalizedString;
  updated_at: string;
}

export interface AdminGuideSection extends GuideSection {
  is_published: boolean;
  title_fr: string;
  title_en: string;
  body_fr: string;
  body_en: string;
}

export interface Attraction {
  id: string;
  slug: string;
  category: AttractionCategory;
  position: number;
  name: LocalizedString;
  summary: LocalizedString;
  description: LocalizedString;
  distance_km: string | null;
  travel_time_min: number | null;
  website_url: string | null;
  image_path: string | null;
  image_credit: string | null;
}

export interface AdminAttraction extends Attraction {
  is_published: boolean;
  name_fr: string;
  name_en: string;
  summary_fr: string;
  summary_en: string;
  description_fr: string;
  description_en: string;
}

export interface AccessStatus {
  granted: boolean;
  expires_at: string | null;
  seconds_remaining: number | null;
}

export interface AccessPolicy {
  auto_rotate: boolean;
  rotation_interval_minutes: number;
  guest_session_minutes: number;
  revoke_sessions_on_rotation: boolean;
  max_active_sessions: number;
  updated_at: string;
}

export interface AccessCode {
  id: string;
  code: string;
  is_active: boolean;
  reason: RotationReason;
  scan_count: number;
  created_at: string;
  expires_at: string | null;
  retired_at: string | null;
  poster_url: string;
  qr_svg: string;
}

export interface AccessStats {
  active_sessions: number;
  sessions_last_24h: number;
  scans_current_code: number;
  total_scans: number;
  code_expires_at: string | null;
  auto_rotate: boolean;
}

export interface GuestSessionRow {
  id: string;
  created_at: string;
  expires_at: string;
  last_seen_at: string | null;
  revoked_at: string | null;
  user_agent: string | null;
  access_code_id: string;
}

export interface Admin {
  id: string;
  email: string;
  full_name: string;
  role: AdminRole;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface LoginResponse {
  admin: Admin;
  csrf_token: string;
  access_token_expires_at: string;
}

export interface AuditEntry {
  id: string;
  action: string;
  actor_admin_id: string | null;
  actor_label: string;
  entity_type: string | null;
  entity_id: string | null;
  context: Record<string, unknown>;
  created_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}
