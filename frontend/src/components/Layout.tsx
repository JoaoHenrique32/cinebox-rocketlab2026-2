import { Link, Outlet } from 'react-router'

export function Layout() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-borda border-b bg-black/30">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link to="/" className="flex items-center gap-2">
            <span className="flex gap-0.5">
              <span className="bg-laranja h-3 w-3 rounded-full" />
              <span className="bg-verde h-3 w-3 rounded-full" />
              <span className="bg-azul h-3 w-3 rounded-full" />
            </span>
            <span className="text-xl font-bold text-white">Cinebox</span>
          </Link>
          <Link
            to="/filmes/novo"
            className="bg-verde rounded px-3 py-1.5 text-sm font-semibold text-black hover:opacity-90"
          >
            + Novo filme
          </Link>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-borda border-t py-4 text-center text-xs">
        Cinebox · RocketLab 2026.2
      </footer>
    </div>
  )
}
