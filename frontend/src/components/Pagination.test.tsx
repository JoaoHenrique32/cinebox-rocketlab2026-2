import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { Pagination } from './Pagination'

describe('Pagination', () => {
  it('não aparece quando só existe uma página', () => {
    const { container } = render(<Pagination page={1} pages={1} onChange={() => {}} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('desabilita "Anterior" na primeira página e avança com "Próxima"', () => {
    const onChange = vi.fn()
    render(<Pagination page={1} pages={5} onChange={onChange} />)

    expect(screen.getByText('Anterior')).toBeDisabled()
    fireEvent.click(screen.getByText('Próxima'))
    expect(onChange).toHaveBeenCalledWith(2)
  })

  it('desabilita "Próxima" na última página', () => {
    render(<Pagination page={5} pages={5} onChange={() => {}} />)
    expect(screen.getByText('Próxima')).toBeDisabled()
  })
})
