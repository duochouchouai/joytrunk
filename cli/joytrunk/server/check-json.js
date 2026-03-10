const fs = require('fs');
const path = require('path');
const p = path.join(__dirname, 'openapi.json');
const s = fs.readFileSync(p, 'utf8');
let depth = 0;
let inStr = false;
let chr = '"';
let esc = false;
const lines = s.split(/\r?\n/);
for (let lineNum = 1; lineNum <= lines.length; lineNum++) {
  const line = lines[lineNum - 1];
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (!inStr) {
      if (c === '{') depth++;
      if (c === '}') depth--;
      if ((c === '"' || c === "'") && !esc) {
        inStr = true;
        chr = c;
      }
    } else {
      if (c === chr && !esc) inStr = false;
      if (c === '\\') esc = !esc;
      else esc = false;
    }
  }
  if (lineNum >= 78 && lineNum <= 95) console.log(lineNum, depth, line.trim().slice(0, 70));
  if (lineNum >= 190) console.log(lineNum, depth, line.trim().slice(0, 70));
}
console.log('Final depth:', depth);
