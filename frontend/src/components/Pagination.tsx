interface PaginationProps {
  page: number
  pages: number
  onChange: (page: number) => void
}

export function Pagination({ page, pages, onChange }: PaginationProps) {
  if (pages <= 1) return null

  const buttonClass = 'bg-card rounded px-3 py-1.5 text-sm text-white hover:bg-borda disabled:opacity-40'

  return (
    <div className="flex items-center justify-center gap-3">
      <button className={buttonClass} disabled={page <= 1} onClick={() => onChange(page - 1)}>
        Anterior
      </button>
      <span className="text-sm">
        Página {page} de {pages.toLocaleString('pt-BR')}
      </span>
      <button className={buttonClass} disabled={page >= pages} onClick={() => onChange(page + 1)}>
        Próxima
      </button>
    </div>
  )
}
