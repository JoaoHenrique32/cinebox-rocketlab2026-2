import { useState, type FormEvent } from 'react'
import { getErrorMessage } from '../api/client'
import { createReview } from '../api/movies'
import { RatingInput } from './RatingInput'

interface ReviewFormProps {
  movieId: string
  onCreated: () => void
}

export function ReviewForm({ movieId, onCreated }: ReviewFormProps) {
  const [nome, setNome] = useState('')
  const [nota, setNota] = useState<number | null>(null)
  const [comentario, setComentario] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')

  const canSubmit = nome.trim() !== '' && comentario.trim() !== '' && nota !== null

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (nota === null) return

    setSending(true)
    setError('')
    try {
      await createReview(movieId, { nome: nome.trim(), nota, comentario: comentario.trim() })
      // Limpa o formulário, mas mantém o nome para facilitar outra avaliação
      setNota(null)
      setComentario('')
      onCreated()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSending(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-card space-y-3 rounded p-4">
      <h3 className="font-semibold text-white">Deixe sua avaliação</h3>

      <div>
        <p className="mb-1 text-sm">Nota (0 a 10)</p>
        <RatingInput value={nota} onChange={setNota} />
      </div>

      <input
        value={nome}
        onChange={(e) => setNome(e.target.value)}
        placeholder="Seu nome"
        maxLength={120}
        className="bg-fundo border-borda w-full rounded border px-3 py-2 text-white"
      />

      <textarea
        value={comentario}
        onChange={(e) => setComentario(e.target.value)}
        placeholder="O que você achou do filme?"
        maxLength={4000}
        rows={4}
        className="bg-fundo border-borda w-full rounded border px-3 py-2 text-white"
      />

      {error && <p className="text-sm text-red-400">{error}</p>}

      <button
        type="submit"
        disabled={!canSubmit || sending}
        className="bg-verde rounded px-4 py-2 text-sm font-semibold text-black disabled:opacity-50"
      >
        {sending ? 'Enviando...' : 'Publicar'}
      </button>
    </form>
  )
}
