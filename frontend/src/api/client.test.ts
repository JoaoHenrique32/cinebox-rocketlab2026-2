import { AxiosError, type AxiosResponse } from 'axios'
import { describe, expect, it } from 'vitest'
import { getErrorMessage, isNotFound } from './client'

function httpError(status: number, data: unknown) {
  return new AxiosError('erro', 'ERR', undefined, undefined, { status, data } as AxiosResponse)
}

describe('getErrorMessage', () => {
  it('usa o detail em texto do FastAPI', () => {
    const error = httpError(404, { detail: 'Filme x não encontrado' })
    expect(getErrorMessage(error)).toBe('Filme x não encontrado')
  })

  it('junta os erros de validação (422) por campo', () => {
    const error = httpError(422, {
      detail: [{ loc: ['body', 'nota'], msg: 'Input should be less than or equal to 10' }],
    })
    expect(getErrorMessage(error)).toBe('nota: Input should be less than or equal to 10')
  })

  it('avisa quando a API está fora do ar', () => {
    expect(getErrorMessage(new AxiosError('Network Error'))).toContain('backend')
  })

  it('identifica respostas 404', () => {
    expect(isNotFound(httpError(404, {}))).toBe(true)
    expect(isNotFound(httpError(500, {}))).toBe(false)
  })
})
