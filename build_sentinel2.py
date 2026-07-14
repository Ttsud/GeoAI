"""Build Sentinel2.html: cloud-free median Sentinel-2 composite for Thailand, 2026,
on a Google Satellite basemap. Uses ee (Earth Engine) directly + folium.

Run: py -3 build_sentinel2.py
"""
import json
import ee
import folium
from shapely.geometry import shape, mapping

ee.Initialize(project="ee-sudchayaman")

# --- 1. Thailand boundary from existing project geojson ---
# The source file has ~280k vertices (11.5MB) which exceeds Earth Engine's
# inline request payload limit (10MB) when embedded in ee.FeatureCollection
# calls. Simplify client-side first; ~0.001 deg (~100m) tolerance keeps the
# coastline recognizable at country scale while cutting the payload drastically.
with open("thailand.geojson", encoding="utf-8") as f:
    thailand_gj_raw = json.load(f)

raw_geom = shape(thailand_gj_raw["features"][0]["geometry"])
simplified_geom = raw_geom.simplify(0.001, preserve_topology=True)
thailand_gj = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": thailand_gj_raw["features"][0].get("properties", {}),
            "geometry": mapping(simplified_geom),
        }
    ],
}
print(f"Simplified geometry: {len(json.dumps(thailand_gj))} bytes "
      f"(was {len(json.dumps(thailand_gj_raw))} bytes)")

thailand_fc = ee.FeatureCollection(thailand_gj)
thailand_geom = thailand_fc.geometry()

minx, miny, maxx, maxy = simplified_geom.bounds
lons, lats = [minx, maxx], [miny, maxy]
center = [(miny + maxy) / 2, (minx + maxx) / 2]

# --- 2. Sentinel-2 SR collection, 2026, filtered to Thailand ---
START = "2026-01-01"
END = "2026-12-31"

s2_sr = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterDate(START, END)
    .filterBounds(thailand_geom)
)

s2_clouds = (
    ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")
    .filterDate(START, END)
    .filterBounds(thailand_geom)
)

# join SR images with matching cloud-probability images by system:index
s2_joined = ee.ImageCollection(
    ee.Join.saveFirst("cloud_mask").apply(
        primary=s2_sr,
        secondary=s2_clouds,
        condition=ee.Filter.equals(leftField="system:index", rightField="system:index"),
    )
)

CLOUD_PROB_THRESHOLD = 40  # % — pixels above this are masked out


def mask_clouds(img):
    clouds = ee.Image(img.get("cloud_mask")).select("probability")
    scl = img.select("SCL")
    # also drop cloud-shadow / cirrus / snow classes from Scene Classification Layer
    scl_mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    is_clear = clouds.lt(CLOUD_PROB_THRESHOLD).And(scl_mask)
    return img.updateMask(is_clear).divide(10000).copyProperties(img, ["system:time_start"])


s2_clean = ee.ImageCollection(s2_joined).map(mask_clouds)

composite = s2_clean.median().clip(thailand_geom)

# --- 3. Visualization params ---
true_color_vis = {"bands": ["B4", "B3", "B2"], "min": 0.0, "max": 0.3, "gamma": 1.3}
false_color_vis = {"bands": ["B8", "B4", "B3"], "min": 0.0, "max": 0.4, "gamma": 1.3}


def get_tile_url(image, vis_params):
    map_id = ee.Image(image).getMapId(vis_params)
    return map_id["tile_fetcher"].url_format


true_color_url = get_tile_url(composite, true_color_vis)
false_color_url = get_tile_url(composite, false_color_vis)

# --- 4. Build folium map ---
m = folium.Map(location=center, zoom_start=6, tiles=None, control_scale=True)

folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    attr="Google Satellite",
    name="Google Satellite",
    overlay=False,
    control=True,
    max_zoom=20,
).add_to(m)

folium.TileLayer(
    tiles=true_color_url,
    attr="Google Earth Engine",
    name="Sentinel-2 True Color (2026 median, cloud-free)",
    overlay=True,
    control=True,
    show=True,
    max_zoom=14,
).add_to(m)

folium.TileLayer(
    tiles=false_color_url,
    attr="Google Earth Engine",
    name="Sentinel-2 False Color / NIR (2026 median, cloud-free)",
    overlay=True,
    control=True,
    show=False,
    max_zoom=14,
).add_to(m)

folium.GeoJson(
    thailand_gj,
    name="Thailand boundary",
    style_function=lambda f: {"color": "#ffff00", "weight": 1.5, "fillOpacity": 0},
).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

m.save("Sentinel2.html")
print("Saved Sentinel2.html")
print("True color tile URL:", true_color_url)
print("False color tile URL:", false_color_url)
