import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

const BANGKOK = [100.5018, 13.7563]

function MapLibreDemo() {
  const containerRef = useRef(null)

  useEffect(() => {
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: 'https://demotiles.maplibre.org/style.json',
      center: BANGKOK,
      zoom: 10,
    })

    map.addControl(new maplibregl.NavigationControl())
    new maplibregl.Marker().setLngLat(BANGKOK).addTo(map)

    return () => map.remove()
  }, [])

  return <div ref={containerRef} className="map-container" />
}

export default MapLibreDemo
