import { useEffect, useState } from 'react'
import { getErrorMessage } from '../api/client'
import { listReviews } from '../api/movies'
import type { Page, Review } from '../api/types'
import { formatReviewDate } from '../utils/format'
import { Pagination } from './Pagination'
import { RatingBadge } from './RatingBadge'

interface ReviewListProps {
  movieId: string
  // Muda sempre que uma avaliação nova é criada, para recarregar a lista
  refreshKey: number
}

export function ReviewList({ movieId, refreshKey }: ReviewListProps) {
  const [page, setPage] = useState(1)
  const [reviews, setReviews] = useState<Page<Review> | null>(null)
  const [error, setError] = useState('')

  // Uma avaliação nova aparece no topo, então volta para a primeira página
  useEffect(() => {
    setPage(1)
  }, [refreshKey])

  useEffect(() => {
    // AbortController cancela a requisição anterior se a página mudar antes da resposta
    const controller = new AbortController()
    listReviews(movieId, page, controller.signal)
      .then((data) => {
        setReviews(data)
        setError('')
      })
      .catch((err) => {
        if (!controller.signal.aborted) setError(getErrorMessage(err))
      })
    return () => controller.abort()
  }, [movieId, page, refreshKey])

  if (error) return <p className="text-sm text-red-400">{error}</p>
  if (!reviews) return <p className="text-sm">Carregando avaliações...</p>
  if (reviews.items.length === 0) {
    return <p className="py-6 text-center text-sm">Nenhuma avaliação ainda. Seja o primeiro!</p>
  }

  return (
    <div>
      <ul className="divide-borda divide-y">
        {reviews.items.map((review) => (
          <li key={review.id} className="py-3">
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="font-semibold text-white">{review.nome}</span>
              <RatingBadge nota={review.nota} />
              <span className="text-xs">{formatReviewDate(review.created_at)}</span>
            </div>
            <p className="mt-1 text-sm whitespace-pre-line">{review.comentario}</p>
          </li>
        ))}
      </ul>
      <div className="mt-4">
        <Pagination page={page} pages={reviews.pages} onChange={setPage} />
      </div>
    </div>
  )
}
