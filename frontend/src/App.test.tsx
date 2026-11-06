import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import type { AppConfig, Job } from './api/types'

const config: AppConfig = {
  max_upload_size_mb: 100,
  supported_extensions: ['.pdf', '.docx', '.pptx', '.txt', '.md'],
  languages: ['auto', 'pl', 'en'],
  min_questions: 1,
  max_questions: 100,
  default_questions: 20,
  ai_provider: 'mock',
}

const completedJob: Job = {
  id: 'job1',
  status: 'completed',
  stage: 'generating',
  progress: 100,
  language: 'auto',
  question_count: 1,
  source_files: [],
  error: null,
  questions: [
    {
      id: 'q1',
      text: 'Ile to 2 + 2?',
      answers: [
        { text: '4', correct: true },
        { text: '5', correct: false },
      ],
      multiple_choice: false,
    },
  ],
}

function mockFetch(responses: Record<string, unknown>) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      const body = responses[url]
      return new Response(JSON.stringify(body), { status: body ? 200 : 404 })
    }),
  )
}

afterEach(() => vi.unstubAllGlobals())

describe('App', () => {
  it('generates questions from pasted text and shows them', async () => {
    mockFetch({ '/api/v1/config/': config, '/api/v1/jobs/': completedJob })
    render(<App />)

    await userEvent.type(screen.getByLabelText(/wklej tekst/i), 'Materiał')
    await userEvent.click(screen.getByRole('button', { name: /generuj pytania/i }))

    expect(await screen.findByText('Ile to 2 + 2?')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /pobierz zip/i })).toHaveAttribute(
      'href',
      '/api/v1/jobs/job1/export/',
    )
  })

  it('shows an error when the backend is unreachable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('fetch failed')))
    render(<App />)

    expect(await screen.findByRole('alert')).toHaveTextContent(/backend/i)
  })
})
