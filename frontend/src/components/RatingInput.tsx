interface RatingInputProps {
  value: number | null
  onChange: (nota: number) => void
}

const NOTAS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

// Um botão para cada nota de 0 a 10 (a escala usada no banco)
export function RatingInput({ value, onChange }: RatingInputProps) {
  return (
    <div className="flex flex-wrap gap-1" role="group" aria-label="Nota de 0 a 10">
      {NOTAS.map((nota) => (
        <button
          key={nota}
          type="button"
          onClick={() => onChange(nota)}
          aria-pressed={value === nota}
          className={`h-9 w-9 rounded text-sm font-semibold ${
            value === nota ? 'bg-verde text-black' : 'bg-borda text-white hover:bg-gray-600'
          }`}
        >
          {nota}
        </button>
      ))}
    </div>
  )
}
