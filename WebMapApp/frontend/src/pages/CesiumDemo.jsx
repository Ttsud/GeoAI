import { useEffect, useRef } from 'react'
import * as Cesium from 'cesium'
import 'cesium/Source/Widgets/widgets.css'

const BANGKOK = { longitude: 100.5018, latitude: 13.7563, height: 15000 }

function CesiumDemo() {
  const containerRef = useRef(null)

  useEffect(() => {
    const viewer = new Cesium.Viewer(containerRef.current, {
      baseLayer: new Cesium.ImageryLayer(
        new Cesium.OpenStreetMapImageryProvider({
          url: 'https://tile.openstreetmap.org/',
        }),
      ),
      baseLayerPicker: false,
      geocoder: false,
      homeButton: false,
      sceneModePicker: false,
      navigationHelpButton: false,
    })

    viewer.camera.setView({
      destination: Cesium.Cartesian3.fromDegrees(
        BANGKOK.longitude,
        BANGKOK.latitude,
        BANGKOK.height,
      ),
    })

    return () => viewer.destroy()
  }, [])

  return <div ref={containerRef} className="map-container" />
}

export default CesiumDemo
