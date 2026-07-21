import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const BANGKOK = [13.7563, 100.5018]

function LeafletDemo() {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const markerRef = useRef(null)
  const [provinces, setProvinces] = useState([])

  useEffect(() => {
    const map = L.map(containerRef.current).setView(BANGKOK, 12)
    mapRef.current = map

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map)

    markerRef.current = L.marker(BANGKOK).addTo(map).bindPopup('Bangkok').openPopup()

    fetch('/data/provinces.json')
      .then((res) => res.json())
      .then((data) =>
        setProvinces([...data].sort((a, b) => a.name_th.localeCompare(b.name_th, 'th'))),
      )

    return () => map.remove()
  }, [])

  const handleSelect = (event) => {
    const code = event.target.value
    const province = provinces.find((p) => p.code === code)
    const map = mapRef.current
    if (!province || !map) return

    const [minLon, minLat, maxLon, maxLat] = province.bbox
    map.fitBounds([
      [minLat, minLon],
      [maxLat, maxLon],
    ])

    const [lon, lat] = province.center
    markerRef.current.setLatLng([lat, lon])
    markerRef.current
      .bindPopup(`${province.name_th} (${province.name_en})`)
      .openPopup()
  }

  return (
    <div className="map-page">
      <div className="map-controls">
        <label htmlFor="province-select">จังหวัด</label>
        <select id="province-select" onChange={handleSelect} defaultValue="">
          <option value="" disabled>
            เลือกจังหวัด
          </option>
          {provinces.map((p) => (
            <option key={p.code} value={p.code}>
              {p.name_th}
            </option>
          ))}
        </select>
      </div>
      <div ref={containerRef} className="map-container" />
    </div>
  )
}

export default LeafletDemo
