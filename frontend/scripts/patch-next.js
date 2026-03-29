/**
 * Patches Next.js generateBuildId to handle undefined config.generateBuildId.
 * Required for Node.js 22+ where the config loading pipeline may drop the
 * generateBuildId function due to module resolution differences.
 */
const fs = require('fs');
const path = require('path');

const filePath = path.join(
  __dirname,
  '..',
  'node_modules',
  'next',
  'dist',
  'build',
  'generate-build-id.js'
);

if (!fs.existsSync(filePath)) {
  console.log('patch-next: next not installed yet, skipping');
  process.exit(0);
}

let code = fs.readFileSync(filePath, 'utf8');
const marker = '/* PATCHED */';

if (code.includes(marker)) {
  console.log('patch-next: already patched');
  process.exit(0);
}

code = code.replace(
  'async function generateBuildId(generate, fallback) {',
  `${marker}\nasync function generateBuildId(generate, fallback) {\n    if (typeof generate !== 'function') { generate = () => null; }`
);

fs.writeFileSync(filePath, code);
console.log('patch-next: patched generate-build-id.js for Node 22 compatibility');
