import { Link } from 'react-router'
import type { MovieSummary } from '../api/types'
import { Poster } from './Poster'
import { RatingBadge } from './RatingBadge'

export function MovieCard({ movie }: { movie: MovieSummary }) {
  return (
    <Link to={`/filmes/${movie.id}`} className="group block">
      <div className="transition group-hover:scale-[1.03]">
        <Poster url={movie.url_poster} title={movie.titulo} />
      </div>
      <h3 className="group-hover:text-verde mt-2 truncate text-sm font-semibold text-white">
        {movie.titulo}
      </h3>
      <div className="flex justify-between text-xs">
        <span>{movie.ano_lancamento ?? '-'}</span>
        <RatingBadge nota={movie.avaliacao.nota_media} />
      </div>
    </Link>
  )
}
