import { useEffect, useState } from 'react'

interface SearchBarProps {
  value: string
  onSearch: (text: string) => void
}

export function SearchBar({ value, onSearch }: SearchBarProps) {
  const [text, setText] = useState(value)

  // Se a busca mudar por fora (ex.: botão "voltar" do navegador), atualiza o campo
  useEffect(() => {
    setText(value)
  }, [value])

  // Debounce: só busca 400ms depois que a pessoa para de digitar,
  // assim não fazemos uma requisição para cada tecla
  useEffect(() => {
    const timer = setTimeout(() => {
      if (text.trim() !== value) {
        onSearch(text.trim())
      }
    }, 400)
    return () => clearTimeout(timer)
  }, [text, value, onSearch])

  return (
    <input
      type="search"
      value={text}
      onChange={(e) => setText(e.target.value)}
      placeholder="Buscar filme pelo título..."
      aria-label="Buscar filme"
      className="bg-card border-borda focus:border-azul w-full rounded border px-3 py-2 text-white outline-none"
    />
  )
}
