import { useEffect, useState } from 'react'
import { api } from './api/client'
import type { AppConfig, CreateJobInput, Job } from './api/types'
import { QuestionList } from './components/QuestionList'
import { UploadForm } from './components/UploadForm'

const POLL_INTERVAL_MS = 1000

function App() {
  const [config, setConfig] = useState<AppConfig | null>(null)
  const [job, setJob] = useState<Job | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .getConfig()
      .then(setConfig)
      .catch(() => setError('Nie można połączyć się z serwerem. Czy backend jest uruchomiony?'))
  }, [])

  // Poll the job until it finishes (WF-06).
  useEffect(() => {
    if (job?.status !== 'processing') return
    const timer = setTimeout(() => {
      api.getJob(job.id).then(setJob, (err: Error) => setError(err.message))
    }, POLL_INTERVAL_MS)
    return () => clearTimeout(timer)
  }, [job])

  const run = async (action: () => Promise<void>) => {
    setError(null)
    try {
      await action()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  const handleSubmit = (input: CreateJobInput) =>
    run(async () => {
      setSubmitting(true)
      try {
        setJob(await api.createJob(input))
      } finally {
        setSubmitting(false)
      }
    })

  const handleDelete = (questionId: string) =>
    run(async () => {
      if (!job) return
      await api.deleteQuestion(job.id, questionId)
      setJob({ ...job, questions: job.questions.filter((q) => q.id !== questionId) })
    })

  const handleRegenerate = (questionId: string) =>
    run(async () => {
      if (!job) return
      const updated = await api.regenerateQuestion(job.id, questionId)
      setJob({ ...job, questions: job.questions.map((q) => (q.id === questionId ? updated : q)) })
    })

  const handleReset = () =>
    run(async () => {
      if (job) await api.deleteJob(job.id)
      setJob(null)
    })

  return (
    <main>
      <header>
        <h1>Testownik AI</h1>
        <p>Wygeneruj bazę pytań do Testownika z własnych materiałów.</p>
      </header>

      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}

      {!job && <UploadForm config={config} disabled={submitting} onSubmit={handleSubmit} />}

      {job?.status === 'processing' && (
        <section className="card">
          <p>Generowanie pytań… {job.progress}%</p>
          <progress value={job.progress} max={100} />
        </section>
      )}

      {job?.status === 'failed' && (
        <section className="card">
          <p className="error">Generowanie nie powiodło się: {job.error}</p>
          <button type="button" onClick={handleReset}>
            Spróbuj ponownie
          </button>
        </section>
      )}

      {job?.status === 'completed' && (
        <section>
          <div className="row toolbar">
            <a className="button" href={api.exportUrl(job.id)} download>
              Pobierz ZIP ({job.questions.length} pytań)
            </a>
            <button type="button" className="secondary" onClick={handleReset}>
              Nowy quiz
            </button>
          </div>
          <QuestionList
            questions={job.questions}
            onDelete={handleDelete}
            onRegenerate={handleRegenerate}
          />
        </section>
      )}
    </main>
  )
}

export default App
