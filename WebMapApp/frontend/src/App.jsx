import { NavLink, Route, Routes } from 'react-router-dom'
import Home from './pages/Home.jsx'
import LeafletDemo from './pages/LeafletDemo.jsx'
import MapLibreDemo from './pages/MapLibreDemo.jsx'
import CesiumDemo from './pages/CesiumDemo.jsx'
import './App.css'

function App() {
  return (
    <div className="app">
      <nav className="app-nav">
        <NavLink to="/" end>
          WebMapApp
        </NavLink>
        <NavLink to="/leaflet">Leaflet</NavLink>
        <NavLink to="/maplibre">MapLibre GL</NavLink>
        <NavLink to="/cesium">CesiumJS</NavLink>
      </nav>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/leaflet" element={<LeafletDemo />} />
          <Route path="/maplibre" element={<MapLibreDemo />} />
          <Route path="/cesium" element={<CesiumDemo />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
