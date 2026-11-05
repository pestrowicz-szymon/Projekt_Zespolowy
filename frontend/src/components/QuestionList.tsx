import type { Question } from '../api/types'

interface Props {
  questions: Question[]
  onDelete: (questionId: string) => void
  onRegenerate: (questionId: string) => void
}

export function QuestionList({ questions, onDelete, onRegenerate }: Props) {
  if (questions.length === 0) {
    return <p>Brak pytań.</p>
  }

  return (
    <ol className="questions">
      {questions.map((question) => (
        <li key={question.id} className="card">
          <p className="question-text">
            {question.text}
            {question.multiple_choice && <span className="badge">wielokrotny wybór</span>}
          </p>
          <ul>
            {question.answers.map((answer, index) => (
              <li key={index} className={answer.correct ? 'correct' : undefined}>
                {answer.text}
              </li>
            ))}
          </ul>
          <div className="row">
            <button type="button" onClick={() => onRegenerate(question.id)}>
              Wygeneruj ponownie
            </button>
            <button type="button" className="secondary" onClick={() => onDelete(question.id)}>
              Usuń
            </button>
          </div>
        </li>
      ))}
    </ol>
  )
}
