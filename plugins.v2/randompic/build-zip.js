import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import archiver from 'archiver'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const pluginName = 'randompic'
const outputFilePath = path.join(__dirname, `${pluginName}.zip`)
const requiredFiles = [
  '__init__.py',
  'network_image_provider.py',
]

for (const file of requiredFiles) {
  if (!fs.existsSync(path.join(__dirname, file))) {
    throw new Error(`缺少打包必需文件: ${file}`)
  }
}

const distDir = path.join(__dirname, 'dist')
if (!fs.existsSync(path.join(distDir, 'assets', 'remoteEntry.js'))) {
  throw new Error('缺少前端构建产物 dist/assets/remoteEntry.js，请先执行 npm run build:web')
}

const output = fs.createWriteStream(outputFilePath)
const archive = archiver('zip', {
  zlib: { level: 9 },
})

output.on('close', () => {
  console.log(`\n\x1b[32m[打包成功]\x1b[0m 已生成插件安装包: ${pluginName}.zip`)
  console.log(`\x1b[36m文件大小:\x1b[0m ${(archive.pointer() / 1024).toFixed(2)} KB`)
  console.log('可以直接在 MoviePilot 插件页面上传此 ZIP 文件。\n')
})

archive.on('warning', (error) => {
  if (error.code === 'ENOENT') {
    console.warn('\x1b[33m[打包警告]\x1b[0m', error.message)
    return
  }
  throw error
})

archive.on('error', (error) => {
  console.error('\x1b[31m[打包失败]\x1b[0m', error)
  throw error
})

archive.pipe(output)
for (const file of requiredFiles) {
  archive.file(path.join(__dirname, file), { name: file })
}
archive.directory(distDir, 'dist')
archive.finalize()
