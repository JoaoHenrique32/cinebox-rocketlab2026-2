import { describe, expect, it } from 'vitest'
import {
  formatDate,
  formatDuration,
  formatMoney,
  formatNota,
  formatReviewDate,
  notaColor,
} from './format'

describe('format', () => {
  it('formata a nota com uma casa decimal e vírgula', () => {
    expect(formatNota(8)).toBe('8,0')
    expect(formatNota(7.25)).toBe('7,3')
  })

  it('escolhe a cor da nota pela faixa de 0 a 10', () => {
    expect(notaColor(9)).toBe('text-verde')
    expect(notaColor(5)).toBe('text-laranja')
    expect(notaColor(2)).toBe('text-red-400')
  })

  it('formata duração em horas e minutos', () => {
    expect(formatDuration(135)).toBe('2h 15min')
    expect(formatDuration(45)).toBe('45min')
  })

  it('não muda o dia da data de lançamento por causa do fuso', () => {
    expect(formatDate('2024-03-15')).toBe('15/03/2024')
  })

  it('trata o created_at sem fuso como UTC', () => {
    expect(formatReviewDate('2026-09-27T12:00:00')).toBe(formatReviewDate('2026-09-27T12:00:00Z'))
  })

  it('ignora valores monetários vazios ou zerados', () => {
    expect(formatMoney(null)).toBeNull()
    expect(formatMoney('0.0')).toBeNull()
    expect(formatMoney('1500000')).toBe('$1,500,000')
  })
})
