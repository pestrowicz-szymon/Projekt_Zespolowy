import { useState, type FormEvent } from 'react'
import type { AppConfig, CreateJobInput, Language } from '../api/types'

const LANGUAGE_LABELS: Record<Language, string> = {
  auto: 'Język materiału',
  pl: 'Polski',
  en: 'Angielski',
}

interface Props {
  config: AppConfig | null
  disabled: boolean
  onSubmit: (input: CreateJobInput) => void
}

export function UploadForm({ config, disabled, onSubmit }: Props) {
  const [files, setFiles] = useState<File[]>([])
  const [text, setText] = useState('')
  const [language, setLanguage] = useState<Language>('auto')
  const [questionCount, setQuestionCount] = useState(config?.default_questions ?? 20)

  const canSubmit = !disabled && (files.length > 0 || text.trim().length > 0)

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (canSubmit) onSubmit({ files, text, language, questionCount })
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <label>
        Pliki ({config?.supported_extensions.join(', ') ?? 'PDF, DOCX, PPTX, TXT, MD, obrazy'})
        <input
          type="file"
          multiple
          accept={config?.supported_extensions.join(',')}
          onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
        />
      </label>

      <label>
        lub wklej tekst
        <textarea rows={6} value={text} onChange={(event) => setText(event.target.value)} />
      </label>

      <div className="row">
        <label>
          Język pytań
          <select
            value={language}
            onChange={(event) => setLanguage(event.target.value as Language)}
          >
            {(config?.languages ?? (['auto', 'pl', 'en'] as Language[])).map((code) => (
              <option key={code} value={code}>
                {LANGUAGE_LABELS[code]}
              </option>
            ))}
          </select>
        </label>

        <label>
          Liczba pytań
          <input
            type="number"
            min={config?.min_questions ?? 1}
            max={config?.max_questions ?? 100}
            value={questionCount}
            onChange={(event) => setQuestionCount(Number(event.target.value))}
          />
        </label>
      </div>

      <button type="submit" disabled={!canSubmit}>
        Generuj pytania
      </button>
    </form>
  )
}
