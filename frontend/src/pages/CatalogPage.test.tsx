import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as moviesApi from '../api/movies'
import type { MovieSummary, Page } from '../api/types'
import { CatalogPage } from './CatalogPage'

// Substitui as chamadas HTTP por funções falsas
vi.mock('../api/movies')

const page: Page<MovieSummary> = {
  items: [
    {
      id: 'm1',
      titulo: 'Matrix',
      ano_lancamento: 1999,
      url_poster: null,
      generos: [],
      avaliacao: { nota_media: 9, total_avaliacoes: 3 },
    },
    {
      id: 'm2',
      titulo: 'Filme Novo',
      ano_lancamento: 2024,
      url_poster: null,
      generos: [],
      avaliacao: { nota_media: null, total_avaliacoes: 0 },
    },
  ],
  total: 2,
  page: 1,
  size: 24,
  pages: 1,
}

describe('CatalogPage', () => {
  beforeEach(() => {
    vi.mocked(moviesApi.listGenres).mockResolvedValue([{ id: 'g1', nome: 'Drama' }])
    vi.mocked(moviesApi.listMovies).mockResolvedValue(page)
    vi.mocked(moviesApi.listReleaseYears).mockResolvedValue([2024, 1999])
  })

  it('lista os filmes com a nota de 0 a 10', async () => {
    render(
      <MemoryRouter>
        <CatalogPage />
      </MemoryRouter>,
    )

    // O pôster sem URL mostra o título, então o nome aparece duas vezes no card
    expect(await screen.findAllByText('Matrix')).not.toHaveLength(0)
    expect(screen.getByText('9,0')).toBeInTheDocument()
    expect(screen.getByText('Sem notas')).toBeInTheDocument()
    expect(screen.getByText('2 filmes')).toBeInTheDocument()
  })

  it('envia os filtros da URL para a API', async () => {
    render(
      <MemoryRouter initialEntries={['/?q=matrix&genero=g1&page=2']}>
        <CatalogPage />
      </MemoryRouter>,
    )

    await screen.findAllByText('Matrix')
    expect(moviesApi.listMovies).toHaveBeenCalledWith(
      expect.objectContaining({ q: 'matrix', genero_id: 'g1', page: 2 }),
      expect.any(AbortSignal),
    )
  })

  it('preenche o filtro de ano apenas com os anos vindos da API', async () => {
    render(
      <MemoryRouter>
        <CatalogPage />
      </MemoryRouter>,
    )

    const select = screen.getByRole('combobox', { name: 'Ano' })
    expect(await within(select).findByRole('option', { name: '2024' })).toBeInTheDocument()
    const options = within(select).getAllByRole('option').map((o) => o.textContent)
    expect(options).toEqual(['Todos os anos', '2024', '1999'])
  })
})
