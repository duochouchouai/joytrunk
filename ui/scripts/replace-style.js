const fs = require('fs');
const path = require('path');
const htmlPath = path.join(__dirname, '..', 'main.html');
let h = fs.readFileSync(htmlPath, 'utf8');
h = h.replace(/<style>[\s\S]*?<\/style>/, '<link rel="stylesheet" href="css/main.css">');
fs.writeFileSync(htmlPath, h);
console.log('Replaced inline style with link to css/main.css');
