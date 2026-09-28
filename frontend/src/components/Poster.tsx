import { useState } from 'react'

interface PosterProps {
  url: string | null
  title: string
}

export function Poster({ url, title }: PosterProps) {
  // Se a imagem não carregar, mostramos o título no lugar
  const [error, setError] = useState(false)

  if (!url || error) {
    return (
      <div className="bg-card border-borda flex aspect-[2/3] items-center justify-center rounded border p-2 text-center text-sm">
        {title}
      </div>
    )
  }

  return (
    <img
      src={url}
      alt={`Pôster de ${title}`}
      loading="lazy"
      onError={() => setError(true)}
      className="border-borda aspect-[2/3] w-full rounded border object-cover"
    />
  )
}
