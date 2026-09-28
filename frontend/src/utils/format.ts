// Funções pequenas de formatação usadas em várias telas

export function formatNota(nota: number): string {
  return nota.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
}

// Cor da nota: verde para boas, laranja para medianas, vermelho para ruins
export function notaColor(nota: number): string {
  if (nota >= 7) return 'text-verde'
  if (nota >= 4) return 'text-laranja'
  return 'text-red-400'
}

export function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  return hours > 0 ? `${hours}h ${rest}min` : `${rest}min`
}

// Datas "2024-03-15" vêm sem fuso; uso UTC para não aparecer o dia anterior
export function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString('pt-BR', { timeZone: 'UTC' })
}

// O created_at vem do SQLite em UTC mas sem o "Z" no final
export function formatReviewDate(isoDateTime: string): string {
  const utc = isoDateTime.endsWith('Z') ? isoDateTime : `${isoDateTime}Z`
  return new Date(utc).toLocaleDateString('pt-BR')
}

export function formatMoney(value: string | null): string | null {
  if (!value || Number(value) <= 0) return null
  return Number(value).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  })
}
