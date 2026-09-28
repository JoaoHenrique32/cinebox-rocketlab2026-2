import { api } from './client'
import type {
  Genre,
  MovieDetail,
  MovieFilters,
  MovieInput,
  MovieSummary,
  Page,
  Review,
  ReviewCreate,
} from './types'

// O `signal` permite cancelar a requisição se o usuário mudar de página antes da resposta
export async function listMovies(filters: MovieFilters, signal?: AbortSignal) {
  const response = await api.get<Page<MovieSummary>>('/movies', { params: filters, signal })
  return response.data
}

export async function getMovie(id: string, signal?: AbortSignal) {
  const response = await api.get<MovieDetail>(`/movies/${id}`, { signal })
  return response.data
}

export async function createMovie(movie: MovieInput) {
  const response = await api.post<MovieDetail>('/movies', movie)
  return response.data
}

export async function updateMovie(id: string, movie: Partial<MovieInput>) {
  const response = await api.patch<MovieDetail>(`/movies/${id}`, movie)
  return response.data
}

export async function deleteMovie(id: string) {
  await api.delete(`/movies/${id}`)
}

export async function listReviews(movieId: string, page: number, signal?: AbortSignal) {
  const response = await api.get<Page<Review>>(`/movies/${movieId}/reviews`, {
    params: { page, size: 10 },
    signal,
  })
  return response.data
}

export async function createReview(movieId: string, review: ReviewCreate) {
  const response = await api.post<Review>(`/movies/${movieId}/reviews`, review)
  return response.data
}

// Os gêneros praticamente não mudam, então guardo a lista depois da primeira busca
let cachedGenres: Genre[] | null = null

export async function listGenres() {
  if (!cachedGenres) {
    const response = await api.get<Genre[]>('/genres')
    cachedGenres = response.data
  }
  return cachedGenres
}
