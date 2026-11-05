import type { AppConfig, CreateJobInput, Job, Question } from './types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, init)
  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response))
  }
  return (response.status === 204 ? undefined : await response.json()) as T
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') return body.detail
    return Object.values(body).flat().join(' ')
  } catch {
    return `Błąd serwera (${response.status})`
  }
}

export const api = {
  getConfig: () => request<AppConfig>('/config/'),

  createJob: ({ files, text, language, questionCount }: CreateJobInput) => {
    const form = new FormData()
    files.forEach((file) => form.append('files', file))
    form.append('text', text)
    form.append('language', language)
    form.append('question_count', String(questionCount))
    return request<Job>('/jobs/', { method: 'POST', body: form })
  },

  getJob: (jobId: string) => request<Job>(`/jobs/${jobId}/`),

  deleteJob: (jobId: string) => request<void>(`/jobs/${jobId}/`, { method: 'DELETE' }),

  deleteQuestion: (jobId: string, questionId: string) =>
    request<void>(`/jobs/${jobId}/questions/${questionId}/`, { method: 'DELETE' }),

  regenerateQuestion: (jobId: string, questionId: string) =>
    request<Question>(`/jobs/${jobId}/questions/${questionId}/regenerate/`, { method: 'POST' }),

  exportUrl: (jobId: string) => `${BASE_URL}/jobs/${jobId}/export/`,
}
