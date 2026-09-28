import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { SearchBar } from './SearchBar'

describe('SearchBar', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('só chama a busca depois que a pessoa para de digitar (debounce)', () => {
    const onSearch = vi.fn()
    render(<SearchBar value="" onSearch={onSearch} />)
    const input = screen.getByLabelText('Buscar filme')

    fireEvent.change(input, { target: { value: 'mat' } })
    fireEvent.change(input, { target: { value: 'matrix' } })
    act(() => vi.advanceTimersByTime(300))
    expect(onSearch).not.toHaveBeenCalled()

    act(() => vi.advanceTimersByTime(100))
    expect(onSearch).toHaveBeenCalledTimes(1)
    expect(onSearch).toHaveBeenCalledWith('matrix')
  })

  it('atualiza o campo quando a busca muda por fora (botão voltar)', () => {
    const onSearch = vi.fn()
    const { rerender } = render(<SearchBar value="matrix" onSearch={onSearch} />)

    rerender(<SearchBar value="" onSearch={onSearch} />)
    act(() => vi.advanceTimersByTime(500))

    expect(screen.getByLabelText('Buscar filme')).toHaveValue('')
    expect(onSearch).not.toHaveBeenCalled()
  })
})
