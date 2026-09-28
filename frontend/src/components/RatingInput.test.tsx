import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { RatingInput } from './RatingInput'

describe('RatingInput', () => {
  it('mostra um botão para cada nota de 0 a 10', () => {
    render(<RatingInput value={null} onChange={() => {}} />)
    expect(screen.getAllByRole('button')).toHaveLength(11)
  })

  it('avisa a nota escolhida e marca o botão selecionado', () => {
    const onChange = vi.fn()
    const { rerender } = render(<RatingInput value={null} onChange={onChange} />)

    fireEvent.click(screen.getByRole('button', { name: '8' }))
    expect(onChange).toHaveBeenCalledWith(8)

    rerender(<RatingInput value={8} onChange={onChange} />)
    expect(screen.getByRole('button', { name: '8' })).toHaveAttribute('aria-pressed', 'true')
  })
})
