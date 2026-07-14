!pip install openet-geesebal earthengine-api geemap -q
import math
import ee
import openet.geesebal.model as gsmodel
from openet.geesebal.model import homogeneous_mask

_orig_hot = gsmodel.fexp_hot_pixel   # เก็บของเดิมไว้

def fexp_hot_pixel_global(
        time_start, albedo, ndvi, ndwi, lst_dem, rn, g,
        ndvi_hot, lst_hot, geometry_image, coords, proj, dem,
        calibration_points=10,
):
    """เหมือน geeSEBAL ต้นฉบับ แต่เปลี่ยน Tfac จาก GRIDMET (CONUS)
       -> CHIRPS (ฝน, global 50S-50N) + ERA5-Land (PET, global)"""

    pos_ndvi   = ndvi.updateMask(ndvi.gte(0)).rename('post_ndvi')
    ndvi_neg   = pos_ndvi.multiply(-1).rename('ndvi_neg')
    lst_neg    = lst_dem.multiply(-1).rename('lst_neg')
    lst_nw     = lst_dem.updateMask(ndwi.lte(0)).rename('lst_nw')
    stdev_ndvi = homogeneous_mask(ndvi, proj)

    images = pos_ndvi.addBands([ndvi, ndvi_neg, rn, g, pos_ndvi, lst_neg, lst_nw, coords])

    # --- เปอร์เซ็นไทล์ NDVI ต่ำ (ดินเปล่า) ---
    d_ndvi = (images.select('post_ndvi').updateMask(stdev_ndvi)
              .reduceRegion(ee.Reducer.percentile([ndvi_hot]), geometry_image, 30, maxPixels=1e9)
              .combine(ee.Dictionary({'post_ndvi': 100}), overwrite=False))
    i_low_NDVI = images.updateMask(
        images.select('post_ndvi').lte(ee.Number(d_ndvi.get('post_ndvi'))))

    # --- เปอร์เซ็นไทล์ LST สูง ---
    d_lst = (i_low_NDVI.select('lst_neg').updateMask(stdev_ndvi)
             .reduceRegion(ee.Reducer.percentile([lst_hot]), geometry_image, 30, maxPixels=1e9)
             .combine(ee.Dictionary({'lst_neg': 350}), overwrite=False))
    i_top_LST = (i_low_NDVI.updateMask(stdev_ndvi)
                 .updateMask(i_low_NDVI.select('lst_neg').lte(ee.Number(d_lst.get('lst_neg')))))

    c_int        = i_top_LST.select('lst_nw').min(1).max(1).int().rename('int')
    c_lst_hotpix = i_top_LST.addBands(c_int)

    # ===== ★ Tfac แบบ global (Allen et al. 2013 Eqn 8) =====
    d0, d1 = ee.Date(time_start).advance(-60, 'days'), ee.Date(time_start)

    # ฝนสะสม 60 วัน (mm) — CHIRPS ครอบคลุม 50S-50N รวมไทย
    p60 = (ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
           .filterDate(d0, d1).select('precipitation').sum())

    # PET สะสม 60 วัน (mm) — ERA5-Land (หน่วย m, ค่าติดลบตามคอนเวนชัน ECMWF)
    pet60 = (ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR')
             .filterDate(d0, d1).select('potential_evaporation_sum').sum()
             .abs().multiply(1000).max(1))          # -> mm, กันหารศูนย์

    ratio = p60.divide(pet60)
    Tfac  = ee.Image(ratio.expression('2.6 - 13 * r', {'r': ratio})
                     .where(ratio.gt(0.2), 0)).rename('Tfac').unmask(0)   # ★ unmask กัน dropNulls
    # ===================================================

    c_lst_hotpix = c_lst_hotpix.addBands(Tfac).select(
        ['ndvi', 'rn_inst', 'g_inst', 'lst_nw', 'longitude', 'latitude', 'int', 'Tfac'])

    n_hot = ee.Number(c_lst_hotpix.select('int')
                      .reduceRegion(ee.Reducer.sum(), geometry_image, 30, maxPixels=1e9)
                      .get('int'))

    return ee.FeatureCollection(ee.Algorithms.If(
        n_hot.gt(3000),
        c_lst_hotpix.stratifiedSample(
            numPoints=calibration_points, classBand='int',
            region=geometry_image, scale=30, dropNulls=True, geometries=True),
        ee.FeatureCollection([])
    ))

# เขียนทับฟังก์ชันเดิม
gsmodel.fexp_hot_pixel = fexp_hot_pixel_global
print('✅ patched fexp_hot_pixel -> CHIRPS + ERA5-Land')
try:
    from google.colab import output
    output.enable_custom_widget_manager()
except ImportError:
    pass

import ee, geemap
ee.Authenticate(); ee.Initialize(project='ee-dancingriver2')
import openet.geesebal as geesebal

aoi = ee.Geometry.Rectangle([102.3, 15.0, 102.8, 15.4])
START, END = '2024-01-01', '2024-03-31'

# ===== 1) ERA5-Land -> band names + หน่วย ที่ geeSEBAL ต้องการ =====
# หน่วยที่ถูกต้อง:
#   temperature        -> °C     (ไม่ใช่ K !!)
#   specific_humidity  -> kg/kg
#   pressure           -> Pa
#   wind_u / wind_v    -> m/s
#   shortwave_radiation-> W/m2
def era5_inst(img):
    t  = img.select('temperature_2m').subtract(273.15).rename('temperature')   # ★ K -> °C
    p  = img.select('surface_pressure').rename('pressure')                     # Pa
    u  = img.select('u_component_of_wind_10m').rename('wind_u')
    v  = img.select('v_component_of_wind_10m').rename('wind_v')
    sw = (img.select('surface_solar_radiation_downwards_hourly')
             .divide(3600).rename('shortwave_radiation'))                      # W/m2

    td = img.select('dewpoint_temperature_2m').subtract(273.15)                # °C
    ea = td.expression('0.6108*exp((17.27*Td)/(Td+237.3))', {'Td': td})        # kPa
    # โมเดลคำนวณย้อนกลับ: ea = (1/0.622)*q*P_kPa  -> q = 0.622*ea/P_kPa
    q  = ea.multiply(0.622).divide(p.divide(1000)).rename('specific_humidity')

    return ee.Image.cat([t, q, p, u, v, sw]).copyProperties(img, ['system:time_start'])

# daily: tmmn/tmmx เป็น K (โมเดล subtract 273.15 ให้เอง) — ห้ามแปลง!
def era5_daily(img):
    srad = img.select('surface_solar_radiation_downwards_sum').divide(86400).rename('srad')  # W/m2
    tmmn = img.select('temperature_2m_min').rename('tmmn')   # K  ← ปล่อยไว้
    tmmx = img.select('temperature_2m_max').rename('tmmx')   # K  ← ปล่อยไว้
    return ee.Image.cat([srad, tmmn, tmmx]).copyProperties(img, ['system:time_start'])

METEO_INST  = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY').filterDate(START, END).map(era5_inst)
METEO_DAILY = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR').filterDate(START, END).map(era5_daily)

# ===== 2) เลือกภาพ =====
coll = (ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
        .merge(ee.ImageCollection('LANDSAT/LC08/C02/T1_L2'))
        .filterBounds(aoi).filterDate(START, END)
        .filter(ee.Filter.lt('CLOUD_COVER', 10))
        .sort('CLOUD_COVER'))

ls_img   = ee.Image(coll.first())
scene_id = ls_img.get('system:index').getInfo()
date_str = ee.Date(ls_img.get('system:time_start')).format('YYYY-MM-dd').getInfo()
print(f'ภาพที่เลือก: {scene_id}  ({date_str})')

# ===== 3) PRE-FLIGHT CHECK — ตรวจ forcing ก่อนรัน (สำคัญ!) =====
t0 = ee.Date(ls_img.get('system:time_start'))
mi = METEO_INST.filterDate(t0.advance(-2,'hour'), t0.advance(2,'hour')).first()
md = METEO_DAILY.filterDate(t0.advance(-1,'day'), t0).first()

fi = mi.reduceRegion(ee.Reducer.mean(), aoi, 5000, maxPixels=1e9).getInfo()
fd = md.reduceRegion(ee.Reducer.mean(), aoi, 5000, maxPixels=1e9).getInfo()

print('\n--- forcing (inst) ---')
for k, v in fi.items():
    print(f'  {k:22s} {v:.4f}')
print('--- forcing (daily) ---')
for k, v in fd.items():
    print(f'  {k:22s} {v:.4f}')

# ค่าที่ควรได้แถบโคราช เดือน ก.พ. เวลา ~10:30 น.
# temperature        ~ 26-33   (°C  <- ถ้าเห็น ~300 แปลว่ายังเป็น K อยู่!)
# specific_humidity  ~ 0.010-0.018
# pressure           ~ 99000-101000
# shortwave_radiation~ 600-900
# srad               ~ 200-260   (W/m2 เฉลี่ยทั้งวัน)
# tmmn / tmmx        ~ 288-305   (K)
assert 5 < fi['temperature'] < 45, '❌ temperature ไม่ใช่ °C!'

# ===== 4) รัน geeSEBAL =====
model = geesebal.Image.from_landsat_c2_sr(
    ls_img,
    meteorology_source_inst  = METEO_INST,
    meteorology_source_daily = METEO_DAILY,
    elev_source = 'USGS/SRTMGL1_003',
    ndvi_cold=5, lst_cold=20, ndvi_hot=10, lst_hot=20,
    calibration_points=6, max_iterations=15,
)

et     = model.et.clip(aoi)
ndvi   = model.ndvi.clip(aoi)
lst_c  = model.lst.subtract(273.15).clip(aoi)
albedo = model.albedo.clip(aoi)

s = et.reduceRegion(
    ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True),
    aoi, 60, maxPixels=1e9, bestEffort=True).getInfo()
print('\nET (mm/day):', s)
assert s.get('et') is not None, '⚠️ ยังว่าง — ลองผ่อน ndvi_hot=20, calibration_points=3'

# ===== 5) Interactive map =====
vis_et   = {'min':0, 'max':8,   'palette':['#a50026','#f46d43','#fee090','#e0f3f8','#74add1','#313695']}
vis_ndvi = {'min':0, 'max':0.9, 'palette':['#8c510a','#d8b365','#f6e8c3','#c7eae5','#5ab4ac','#01665e']}
vis_lst  = {'min':22,'max':45,  'palette':['#2166ac','#67a9cf','#f7f7f7','#fddbc7','#ef8a62','#b2182b']}

M = geemap.Map(center=[15.2, 102.55], zoom=11, basemap='HYBRID')
M.addLayer(ls_img.clip(aoi), {'bands':['SR_B4','SR_B3','SR_B2'],'min':7000,'max':18000}, 'Landsat RGB', False)
M.addLayer(albedo, {'min':0.05,'max':0.35}, 'Albedo', False)
M.addLayer(ndvi,   vis_ndvi, 'NDVI', False)
M.addLayer(lst_c,  vis_lst,  'LST (°C)', False)
M.addLayer(et,     vis_et,   f'SEBAL ET {date_str} (mm/day)', True)
M.addLayer(ee.Image().paint(aoi, 0, 2), {'palette':'yellow'}, 'AOI')
M.add_colorbar(vis_et, label='SEBAL ET (mm/day)', orientation='horizontal')
M.addLayerControl()
M