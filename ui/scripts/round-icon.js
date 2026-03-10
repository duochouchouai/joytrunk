/**
 * 生成带圆角的 Windows 任务栏图标：从 imgs/logo-white.png 生成 imgs/logo-white-rounded.png。
 * 在 ui 目录执行：node scripts/round-icon.js 或 npm run round-icon；prestart 会自动执行。
 */
const path = require('path');
const fs = require('fs');

const isInUi = __dirname.includes(path.sep + 'ui' + path.sep);
const rootDir = isInUi ? path.join(__dirname, '..', '..') : path.join(__dirname, '..');
const imgsDir = path.join(rootDir, 'imgs');
const inputPath = path.join(imgsDir, 'logo-white.png');
const outputPath = path.join(imgsDir, 'logo-white-rounded.png');

if (!fs.existsSync(inputPath)) {
  console.warn('round-icon: 未找到', inputPath, '，跳过生成。');
  process.exit(0);
}

let sharp;
try {
  sharp = require('sharp');
} catch (e) {
  console.warn('round-icon: 未安装 sharp，请执行 npm install sharp --save-dev 后重试。');
  process.exit(1);
}

/** 使用圆角矩形蒙版合成并写出 PNG */
async function run() {
  const image = sharp(inputPath);
  const meta = await image.metadata();
  const w = meta.width || 256;
  const h = meta.height || 256;
  const radius = Math.round(Math.min(w, h) * 0.22);

  const maskSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">
    <rect x="0" y="0" width="${w}" height="${h}" rx="${radius}" ry="${radius}" fill="white"/>
  </svg>`;

  await image
    .ensureAlpha()
    .png()
    .composite([{ input: Buffer.from(maskSvg), blend: 'dest-in' }])
    .png()
    .toFile(outputPath);

  console.log('round-icon: 已生成', outputPath);
}

run().catch((err) => {
  console.error('round-icon 失败:', err);
  process.exit(1);
});
