import axios from 'axios'
import type { ApiError } from './types'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1',
})

// Transforma o erro do axios em uma mensagem que dá para mostrar na tela
export function getErrorMessage(error: unknown): string {
  if (!axios.isAxiosError<ApiError>(error)) {
    return 'Ocorreu um erro inesperado.'
  }
  if (!error.response) {
    return 'Não foi possível conectar à API. O backend está rodando?'
  }

  const detail = error.response.data?.detail
  if (typeof detail === 'string') {
    return detail
  }
  // Erro 422 do FastAPI: lista com um item por campo inválido
  if (Array.isArray(detail)) {
    return detail.map((item) => `${item.loc.at(-1)}: ${item.msg}`).join(' | ')
  }
  return `Erro ${error.response.status}`
}

export function isNotFound(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 404
}
