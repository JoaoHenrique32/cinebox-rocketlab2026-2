import { Link } from 'react-router'

export function NotFoundPage() {
  return (
    <div className="py-20 text-center">
      <p className="text-laranja text-5xl font-bold">404</p>
      <p className="mt-2 text-white">Página ou filme não encontrado.</p>
      <Link to="/" className="text-azul mt-4 inline-block hover:underline">
        Voltar para o catálogo
      </Link>
    </div>
  )
}
