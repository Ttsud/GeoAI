import { existsSync, rmSync, cpSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const frontendDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const distDir = path.join(frontendDir, 'dist')
const targetDir = path.join(frontendDir, '..', 'backend', 'static')

if (!existsSync(distDir)) {
  throw new Error(`dist not found at ${distDir} — run "vite build" first`)
}

rmSync(targetDir, { recursive: true, force: true })
cpSync(distDir, targetDir, { recursive: true })

console.log(`Copied ${distDir} -> ${targetDir}`)
