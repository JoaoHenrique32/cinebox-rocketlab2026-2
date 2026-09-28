import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router'
import { getErrorMessage } from '../api/client'
import { listGenres, listMovies, listReleaseYears } from '../api/movies'
import { SORT_OPTIONS, type Genre, type MovieSort, type MovieSummary, type Page } from '../api/types'
import { MovieCard } from '../components/MovieCard'
import { Pagination } from '../components/Pagination'
import { SearchBar } from '../components/SearchBar'

const PAGE_SIZE = 24

const selectClass = 'bg-card border-borda w-full rounded border px-2 py-2 text-sm text-white'

export function CatalogPage() {
  // Os filtros ficam na URL (?q=...&page=2): dá para compartilhar o link
  // e o botão "voltar" do navegador funciona
  const [searchParams, setSearchParams] = useSearchParams()
  const q = searchParams.get('q') ?? ''
  const genero = searchParams.get('genero') ?? ''
  const ano = searchParams.get('ano') ?? ''
  const ordenar = (searchParams.get('ordenar') ?? 'populares') as MovieSort
  const page = Number(searchParams.get('page') ?? 1)

  const [movies, setMovies] = useState<Page<MovieSummary> | null>(null)
  const [genres, setGenres] = useState<Genre[]>([])
  const [years, setYears] = useState<number[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Busca os gêneros e os anos uma vez só, para preencher os filtros.
  // Se falhar, o filtro fica só com a opção "Todos" e o catálogo segue funcionando.
  useEffect(() => {
    const controller = new AbortController()
    listGenres()
      .then(setGenres)
      .catch(() => setGenres([]))
    listReleaseYears(controller.signal)
      .then(setYears)
      .catch(() => setYears([]))
    return () => controller.abort()
  }, [])

  // Recarrega os filmes sempre que algum filtro da URL mudar
  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)

    listMovies(
      {
        q: q || undefined,
        genero_id: genero || undefined,
        ano: ano ? Number(ano) : undefined,
        ordenar,
        page,
        size: PAGE_SIZE,
      },
      controller.signal,
    )
      .then((data) => {
        setMovies(data)
        setError('')
        setLoading(false)
      })
      .catch((err) => {
        // Requisição cancelada porque o filtro mudou: não é um erro de verdade
        if (controller.signal.aborted) return
        setError(getErrorMessage(err))
        setLoading(false)
      })

    return () => controller.abort()
  }, [q, genero, ano, ordenar, page])

  // Atualiza um filtro na URL. Trocar filtro volta para a página 1.
  const updateFilter = useCallback(
    (name: string, value: string) => {
      setSearchParams((current) => {
        const params = new URLSearchParams(current)
        if (value) params.set(name, value)
        else params.delete(name)
        if (name !== 'page') params.delete('page')
        return params
      })
    },
    [setSearchParams],
  )

  const handleSearch = useCallback((text: string) => updateFilter('q', text), [updateFilter])

  function goToPage(newPage: number) {
    updateFilter('page', String(newPage))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-6">
      <div className="mb-4 flex items-baseline justify-between">
        <h1 className="text-2xl font-bold text-white">Filmes</h1>
        {movies && <span className="text-sm">{movies.total.toLocaleString('pt-BR')} filmes</span>}
      </div>

      <div className="mb-6 space-y-3">
        <SearchBar value={q} onSearch={handleSearch} />

        {/* No celular os filtros ficam em 2 colunas; a partir de sm, 4 colunas */}
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <select
            className={selectClass}
            value={genero}
            onChange={(e) => updateFilter('genero', e.target.value)}
            aria-label="Gênero"
          >
            <option value="">Todos os gêneros</option>
            {genres.map((g) => (
              <option key={g.id} value={g.id}>
                {g.nome}
              </option>
            ))}
          </select>

          <select
            className={selectClass}
            value={ano}
            onChange={(e) => updateFilter('ano', e.target.value)}
            aria-label="Ano"
          >
            <option value="">Todos os anos</option>
            {years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>

          <select
            className={selectClass}
            value={ordenar}
            onChange={(e) => updateFilter('ordenar', e.target.value)}
            aria-label="Ordenar por"
          >
            {Object.entries(SORT_OPTIONS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          {(q || genero || ano) && (
            <button
              className="bg-borda rounded px-2 py-2 text-sm text-white hover:bg-gray-600"
              onClick={() => setSearchParams({})}
            >
              Limpar filtros
            </button>
          )}
        </div>
      </div>

      {error && <p className="text-center text-red-400">{error}</p>}

      {!error && !movies && <p className="py-10 text-center">Carregando filmes...</p>}

      {!error && movies && movies.items.length === 0 && (
        <p className="py-10 text-center">Nenhum filme encontrado.</p>
      )}

      {!error && movies && movies.items.length > 0 && (
        <>
          {/* Grade responsiva: 2 colunas no celular até 6 no desktop */}
          <div
            className={`grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 ${
              loading ? 'opacity-50' : ''
            }`}
          >
            {movies.items.map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>
          <div className="mt-8">
            <Pagination page={page} pages={movies.pages} onChange={goToPage} />
          </div>
        </>
      )}
    </div>
  )
}
