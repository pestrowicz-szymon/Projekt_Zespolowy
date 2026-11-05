// Mirrors the backend serializers (backend/apps/generation/serializers.py).
// Full contract: http://127.0.0.1:8000/api/docs/

export type Language = 'auto' | 'pl' | 'en'

export interface Answer {
  text: string
  correct: boolean
}

export interface Question {
  id: string
  text: string
  answers: Answer[]
  multiple_choice: boolean
}

export type JobStatus = 'processing' | 'completed' | 'failed'

export interface Job {
  id: string
  status: JobStatus
  progress: number
  language: string
  question_count: number
  source_files: string[]
  error: string | null
  questions: Question[]
}

export interface AppConfig {
  max_upload_size_mb: number
  supported_extensions: string[]
  languages: Language[]
  min_questions: number
  max_questions: number
  default_questions: number
  ai_provider: string
}

export interface CreateJobInput {
  files: File[]
  text: string
  language: Language
  questionCount: number
}
