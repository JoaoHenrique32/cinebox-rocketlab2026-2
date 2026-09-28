import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { getErrorMessage, isNotFound } from '../api/client'
import { deleteMovie, getMovie } from '../api/movies'
import type { MovieDetail } from '../api/types'
import { Poster } from '../components/Poster'
import { RatingBadge } from '../components/RatingBadge'
import { ReviewForm } from '../components/ReviewForm'
import { ReviewList } from '../components/ReviewList'
import { formatDate, formatDuration, formatMoney, formatNota } from '../utils/format'
import { NotFoundPage } from './NotFoundPage'

export function MovieDetailPage() {
  const { id = '' } = useParams()
  const navigate = useNavigate()

  const [movie, setMovie] = useState<MovieDetail | null>(null)
  const [error, setError] = useState<unknown>(null)
  // Incrementado a cada avaliação nova: recarrega o filme (média) e a lista
  const [reviewsVersion, setReviewsVersion] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    getMovie(id, controller.signal)
      .then((data) => {
        setMovie(data)
        setError(null)
      })
      .catch((err) => {
        if (!controller.signal.aborted) setError(err)
      })
    return () => controller.abort()
  }, [id, reviewsVersion])

  async function handleDelete() {
    if (!movie) return
    const confirmed = window.confirm(`Remover "${movie.titulo}" e todas as suas avaliações?`)
    if (!confirmed) return

    try {
      await deleteMovie(movie.id)
      navigate('/')
    } catch (err) {
      alert(getErrorMessage(err))
    }
  }

  if (isNotFound(error)) return <NotFoundPage />
  if (error) return <p className="py-10 text-center text-red-400">{getErrorMessage(error)}</p>
  if (!movie) return <p className="py-10 text-center">Carregando...</p>

  const budget = formatMoney(movie.desempenho?.orcamento_usd ?? null)
  const revenue = formatMoney(movie.desempenho?.receita_usd ?? null)
  const imdb = movie.desempenho?.nota_imdb

  return (
    <div>
      {movie.url_backdrop && (
        <img
          src={movie.url_backdrop}
          alt=""
          className="h-48 w-full object-cover object-top opacity-40 sm:h-80"
        />
      )}

      <div className="mx-auto grid max-w-5xl gap-6 px-4 py-6 md:grid-cols-[220px_1fr]">
        {/* Coluna da esquerda: pôster, média e ações */}
        <div className="space-y-4">
          <div className="mx-auto w-40 md:w-full">
            <Poster url={movie.url_poster} title={movie.titulo} />
          </div>

          <div className="bg-card rounded p-4 text-center">
            <p className="text-xs uppercase">Média geral</p>
            <RatingBadge nota={movie.avaliacao.nota_media} size="large" />
            <p className="text-xs">
              {movie.avaliacao.total_avaliacoes}{' '}
              {movie.avaliacao.total_avaliacoes === 1 ? 'avaliação' : 'avaliações'}
            </p>
          </div>

          <div className="flex gap-2">
            <Link
              to={`/filmes/${movie.id}/editar`}
              className="bg-borda flex-1 rounded py-2 text-center text-sm text-white hover:bg-gray-600"
            >
              Editar
            </Link>
            <button
              onClick={handleDelete}
              className="flex-1 rounded bg-red-600 py-2 text-sm text-white hover:bg-red-700"
            >
              Remover
            </button>
          </div>
        </div>

        {/* Coluna da direita: informações e avaliações */}
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-white">
              {movie.titulo}{' '}
              {movie.ano_lancamento && (
                <span className="text-xl font-normal">{movie.ano_lancamento}</span>
              )}
            </h1>

            {movie.diretores.length > 0 && (
              <p className="mt-1 text-sm">
                Dirigido por{' '}
                <span className="text-white">
                  {movie.diretores.map((d) => d.nome).join(', ')}
                </span>
              </p>
            )}

            <div className="mt-3 flex flex-wrap gap-2">
              {movie.generos.map((g) => (
                <Link
                  key={g.id}
                  to={`/?genero=${g.id}`}
                  className="bg-card rounded px-2 py-1 text-xs text-white hover:bg-borda"
                >
                  {g.nome}
                </Link>
              ))}
            </div>

            {movie.sinopse && <p className="mt-4 leading-relaxed">{movie.sinopse}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
            {movie.data_lancamento && <Info label="Lançamento" value={formatDate(movie.data_lancamento)} />}
            {movie.duracao_minutos && <Info label="Duração" value={formatDuration(movie.duracao_minutos)} />}
            {movie.status_filme && <Info label="Status" value={movie.status_filme} />}
            {imdb != null && <Info label="Nota IMDb" value={`${formatNota(imdb)}/10`} />}
            {budget && <Info label="Orçamento" value={budget} />}
            {revenue && <Info label="Bilheteria" value={revenue} />}
          </div>

          {movie.roteiristas.length > 0 && (
            <Info label="Roteiro" value={movie.roteiristas.map((p) => p.nome).join(', ')} />
          )}
          {movie.elenco.length > 0 && (
            <Info label="Elenco" value={movie.elenco.map((p) => p.nome).join(', ')} />
          )}
          {movie.produtoras.length > 0 && (
            <Info label="Produção" value={movie.produtoras.map((c) => c.nome).join(', ')} />
          )}

          <section className="space-y-4">
            <h2 className="border-borda border-b pb-2 text-lg font-semibold text-white">
              Avaliações
            </h2>
            <ReviewForm movieId={movie.id} onCreated={() => setReviewsVersion((v) => v + 1)} />
            <ReviewList movieId={movie.id} refreshKey={reviewsVersion} />
          </section>
        </div>
      </div>
    </div>
  )
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs uppercase">{label}</p>
      <p className="text-white">{value}</p>
    </div>
  )
}
