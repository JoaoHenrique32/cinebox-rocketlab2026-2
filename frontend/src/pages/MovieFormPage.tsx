import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { getErrorMessage } from '../api/client'
import { createMovie, getMovie, listGenres, updateMovie } from '../api/movies'
import { MOVIE_STATUSES, type Genre, type MovieInput, type MovieStatus } from '../api/types'

// Estado do formulário: os inputs HTML trabalham com texto
const emptyForm = {
  titulo: '',
  diretores: '', // nomes separados por vírgula
  data_lancamento: '',
  ano_lancamento: '',
  duracao_minutos: '',
  status_filme: '',
  sinopse: '',
  url_poster: '',
  url_backdrop: '',
  genero_ids: [] as string[],
}
type FormState = typeof emptyForm

// Converte o formulário para o formato que a API espera (campo vazio vira null)
function toMovieInput(form: FormState): MovieInput {
  const toNumber = (value: string) => (value ? Number(value) : null)
  return {
    titulo: form.titulo.trim(),
    diretores: form.diretores
      .split(',')
      .map((name) => name.trim())
      .filter(Boolean),
    data_lancamento: form.data_lancamento || null,
    // Com a data preenchida, o backend calcula o ano sozinho
    ano_lancamento: form.data_lancamento ? null : toNumber(form.ano_lancamento),
    duracao_minutos: toNumber(form.duracao_minutos),
    status_filme: (form.status_filme || null) as MovieStatus | null,
    sinopse: form.sinopse.trim() || null,
    url_poster: form.url_poster.trim() || null,
    url_backdrop: form.url_backdrop.trim() || null,
    genero_ids: form.genero_ids,
  }
}

const inputClass = 'bg-card border-borda focus:border-azul w-full rounded border px-3 py-2 text-white outline-none'

export function MovieFormPage() {
  // Sem id na URL = cadastro; com id = edição
  const { id } = useParams()
  const isEditing = Boolean(id)
  const navigate = useNavigate()

  const [form, setForm] = useState<FormState>(emptyForm)
  const [genres, setGenres] = useState<Genre[]>([])
  const [loading, setLoading] = useState(isEditing)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    listGenres()
      .then(setGenres)
      .catch(() => setGenres([]))
  }, [])

  // Na edição, preenche o formulário com os dados atuais do filme
  useEffect(() => {
    if (!id) return
    getMovie(id)
      .then((movie) => {
        setForm({
          titulo: movie.titulo,
          diretores: movie.diretores.map((d) => d.nome).join(', '),
          data_lancamento: movie.data_lancamento ?? '',
          ano_lancamento: movie.ano_lancamento ? String(movie.ano_lancamento) : '',
          duracao_minutos: movie.duracao_minutos ? String(movie.duracao_minutos) : '',
          status_filme: movie.status_filme ?? '',
          sinopse: movie.sinopse ?? '',
          url_poster: movie.url_poster ?? '',
          url_backdrop: movie.url_backdrop ?? '',
          genero_ids: movie.generos.map((g) => g.id),
        })
      })
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [id])

  function setField(name: keyof FormState, value: string) {
    setForm({ ...form, [name]: value })
  }

  function toggleGenre(genreId: string) {
    const selected = form.genero_ids.includes(genreId)
    setForm({
      ...form,
      genero_ids: selected
        ? form.genero_ids.filter((g) => g !== genreId)
        : [...form.genero_ids, genreId],
    })
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const movie = id
        ? await updateMovie(id, toMovieInput(form))
        : await createMovie(toMovieInput(form))
      navigate(`/filmes/${movie.id}`)
    } catch (err) {
      setError(getErrorMessage(err))
      setSaving(false)
    }
  }

  if (loading) return <p className="py-10 text-center">Carregando...</p>

  return (
    <div className="mx-auto max-w-2xl px-4 py-6">
      <h1 className="mb-6 text-2xl font-bold text-white">
        {isEditing ? 'Editar filme' : 'Cadastrar filme'}
      </h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block">
          <span className="text-sm">Título *</span>
          <input
            className={inputClass}
            value={form.titulo}
            onChange={(e) => setField('titulo', e.target.value)}
            required
            maxLength={500}
          />
        </label>

        <label className="block">
          <span className="text-sm">Diretor(es)</span>
          <input
            className={inputClass}
            value={form.diretores}
            onChange={(e) => setField('diretores', e.target.value)}
            placeholder="Separe os nomes por vírgula"
          />
        </label>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <label className="col-span-2 block sm:col-span-1">
            <span className="text-sm">Data de lançamento</span>
            <input
              type="date"
              className={inputClass}
              value={form.data_lancamento}
              onChange={(e) => setField('data_lancamento', e.target.value)}
            />
          </label>
          <label className="block">
            <span className="text-sm">Ano</span>
            <input
              type="number"
              className={inputClass}
              min={1870}
              max={2100}
              // Se tem data, o ano vem dela
              value={form.data_lancamento ? form.data_lancamento.slice(0, 4) : form.ano_lancamento}
              disabled={Boolean(form.data_lancamento)}
              onChange={(e) => setField('ano_lancamento', e.target.value)}
            />
          </label>
          <label className="block">
            <span className="text-sm">Duração (min)</span>
            <input
              type="number"
              className={inputClass}
              min={1}
              value={form.duracao_minutos}
              onChange={(e) => setField('duracao_minutos', e.target.value)}
            />
          </label>
        </div>

        <label className="block">
          <span className="text-sm">Status</span>
          <select
            className={inputClass}
            value={form.status_filme}
            onChange={(e) => setField('status_filme', e.target.value)}
          >
            <option value="">Não informado</option>
            {MOVIE_STATUSES.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </label>

        <fieldset>
          <legend className="mb-1 text-sm">Gêneros</legend>
          <div className="flex flex-wrap gap-2">
            {genres.map((genre) => (
              <label
                key={genre.id}
                className="bg-card border-borda flex cursor-pointer items-center gap-1 rounded border px-2 py-1 text-sm text-white"
              >
                <input
                  type="checkbox"
                  checked={form.genero_ids.includes(genre.id)}
                  onChange={() => toggleGenre(genre.id)}
                  className="accent-verde"
                />
                {genre.nome}
              </label>
            ))}
          </div>
        </fieldset>

        <label className="block">
          <span className="text-sm">Sinopse</span>
          <textarea
            className={inputClass}
            rows={5}
            value={form.sinopse}
            onChange={(e) => setField('sinopse', e.target.value)}
            maxLength={4000}
          />
        </label>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block">
            <span className="text-sm">URL do pôster</span>
            <input
              type="url"
              className={inputClass}
              value={form.url_poster}
              onChange={(e) => setField('url_poster', e.target.value)}
              placeholder="https://..."
            />
          </label>
          <label className="block">
            <span className="text-sm">URL do backdrop</span>
            <input
              type="url"
              className={inputClass}
              value={form.url_backdrop}
              onChange={(e) => setField('url_backdrop', e.target.value)}
              placeholder="https://..."
            />
          </label>
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <div className="flex justify-end gap-2">
          <Link
            to={id ? `/filmes/${id}` : '/'}
            className="bg-borda rounded px-4 py-2 text-sm text-white hover:bg-gray-600"
          >
            Cancelar
          </Link>
          <button
            type="submit"
            disabled={saving || !form.titulo.trim()}
            className="bg-verde rounded px-4 py-2 text-sm font-semibold text-black disabled:opacity-50"
          >
            {saving ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </form>
    </div>
  )
}
