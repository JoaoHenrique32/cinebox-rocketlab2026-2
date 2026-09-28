import { BrowserRouter, Route, Routes } from 'react-router'
import { Layout } from './components/Layout'
import { CatalogPage } from './pages/CatalogPage'
import { MovieDetailPage } from './pages/MovieDetailPage'
import { MovieFormPage } from './pages/MovieFormPage'
import { NotFoundPage } from './pages/NotFoundPage'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<CatalogPage />} />
          <Route path="/filmes/novo" element={<MovieFormPage />} />
          <Route path="/filmes/:id" element={<MovieDetailPage />} />
          <Route path="/filmes/:id/editar" element={<MovieFormPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
