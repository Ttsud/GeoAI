# WebMapApp

ตัวอย่างเว็บแอปแสดงแผนที่ (Web Map) ด้วย React เปรียบเทียบไลบรารีแผนที่ยอดนิยม 3 ตัว ได้แก่ [Leaflet](https://leafletjs.com/), [MapLibre GL](https://maplibre.org/) และ [CesiumJS](https://cesium.com/platform/cesiumjs/) พร้อมตัวอย่างการซูมไปยังจังหวัดต่าง ๆ ของประเทศไทย

## Project structure

```
WebMapApp/
├── frontend/   # React + Vite single-page app (map demos)
└── backend/    # Static file host scaffold; serves the built frontend
```

### Frontend

- **Stack:** React 19, React Router, Vite
- **Map libraries:** Leaflet, MapLibre GL, CesiumJS
- **Data:** `frontend/public/data/provinces.json` (Thailand province boundaries used for the zoom dropdown)

### Backend

- Currently a scaffold that serves the frontend's production build.
- `frontend/dist` is copied into `backend/static/` via the frontend's `postbuild` script (`frontend/scripts/copy-dist-to-backend.js`).

## Prerequisites

- Node.js 20+ and npm

## Getting started

```bash
cd frontend
npm install
npm run dev
```

The dev server prints a local URL (default `http://localhost:5173`).

## Available scripts (frontend)

| Command           | Description                                              |
| ----------------- | --------------------------------------------------------- |
| `npm run dev`      | Start the Vite dev server with hot module reload          |
| `npm run build`    | Build for production, then copy `dist/` into `backend/static/` |
| `npm run preview`  | Preview the production build locally                      |
| `npm run lint`     | Lint the codebase with Oxlint                              |

## Deployment

Run `npm run build` inside `frontend/`; the compiled static assets land in `backend/static/`, ready to be served by whatever backend/static host is set up.
