export type Frequency = "immediate" | "daily" | "weekly";
export type ConfigStatus = "active" | "paused";

export interface User {
  id: string;
  email: string;
}

export interface MonitorConfig {
  id: string;
  email_to_monitor: string;
  imap_server: string;
  imap_port: number;
  report_destination_email: string;
  frequency: Frequency;
  status: ConfigStatus;
  last_checked_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConfigInput {
  email_to_monitor: string;
  imap_server: string;
  imap_port: number;
  imap_password: string;
  report_destination_email: string;
  frequency: Frequency;
}

export interface Analysis {
  id: string;
  sender: string;
  subject: string;
  received_at: string | null;
  mood_label: string;
  mood_score: number;
  mood_summary: string;
  requires_attention: boolean;
  analysis_failed: boolean;
  analyzed_at: string;
  report_sent: boolean;
}
