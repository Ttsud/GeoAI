import { Link } from 'react-router-dom'

const demos = [
  {
    to: '/leaflet',
    name: 'Leaflet',
    description: 'Lightweight raster/vector map library with an OpenStreetMap base layer.',
  },
  {
    to: '/maplibre',
    name: 'MapLibre GL',
    description: 'Open-source vector tile rendering with WebGL.',
  },
  {
    to: '/cesium',
    name: 'CesiumJS',
    description: '3D globe and map rendering.',
  },
]

function Home() {
  return (
    <div className="home">
      <h1>Web Map API Examples</h1>
      <p>เลือกไลบรารีที่ต้องการดูตัวอย่าง</p>
      <ul className="demo-list">
        {demos.map((demo) => (
          <li key={demo.to}>
            <Link to={demo.to}>
              <h2>{demo.name}</h2>
              <p>{demo.description}</p>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default Home
