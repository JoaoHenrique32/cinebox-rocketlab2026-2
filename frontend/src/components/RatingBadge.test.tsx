import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { RatingBadge } from './RatingBadge'

describe('RatingBadge', () => {
  it('mostra a nota na escala de 0 a 10', () => {
    render(<RatingBadge nota={8.5} />)
    expect(screen.getByText('8,5')).toBeInTheDocument()
    expect(screen.getByText(/\/10/)).toBeInTheDocument()
  })

  it('mostra "Sem notas" quando o filme não tem avaliações', () => {
    render(<RatingBadge nota={null} />)
    expect(screen.getByText('Sem notas')).toBeInTheDocument()
  })
})
