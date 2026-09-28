import { formatNota, notaColor } from '../utils/format'

interface RatingBadgeProps {
  nota: number | null
  size?: 'small' | 'large'
}

// Mostra a nota no formato "8,5/10", com a cor de acordo com o valor
export function RatingBadge({ nota, size = 'small' }: RatingBadgeProps) {
  if (nota === null) {
    return <span className="text-xs">Sem notas</span>
  }

  if (size === 'large') {
    return (
      <span>
        <span className={`text-4xl font-bold ${notaColor(nota)}`}>{formatNota(nota)}</span>
        <span className="text-lg">/10</span>
      </span>
    )
  }

  return (
    <span className="text-xs">
      <span className={`font-semibold ${notaColor(nota)}`}>{formatNota(nota)}</span>/10
    </span>
  )
}
