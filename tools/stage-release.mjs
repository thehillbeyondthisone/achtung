// Build the browser release from the current checkout and a pinned npm package.
import assert from 'node:assert/strict';
import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const output = path.join(root, 'dist', 'u505');
const three = path.resolve(process.argv[2] || path.join(root, 'dist', 'release-deps', 'node_modules', 'three'));
const version = '0.160.0';
const cdn = `https://cdn.jsdelivr.net/npm/three@${version}/`;
const vendor = './vendor/three/';
const sourcesToggle = "const onlineSources = new URLSearchParams(location.search).get('sources') === 'online';";
const decoderPath = 'examples/jsm/libs/draco/gltf/';

const projectFiles = [
  '.nojekyll',
  'ui/menus.css',
  'ui/menus.js',
  'art/u505_game.glb',
  'art/u505_interior.glb',
  'docs/visuals/blender/u505_hero_atlantic.jpg',
  'docs/visuals/blender/u505_broadside_atlantic.jpg',
];
const threeFiles = [
  'build/three.module.min.js',
  'examples/jsm/loaders/GLTFLoader.js',
  'examples/jsm/loaders/DRACOLoader.js',
  'examples/jsm/utils/BufferGeometryUtils.js',
  'examples/jsm/libs/draco/README.md',
  `${decoderPath}draco_decoder.js`,
  `${decoderPath}draco_decoder.wasm`,
  `${decoderPath}draco_wasm_wrapper.js`,
];

async function stageFile(source, relative) {
  const target = path.join(output, relative);
  await mkdir(path.dirname(target), { recursive: true });
  await copyFile(source, target);
}

try {
  const packageInfo = JSON.parse(await readFile(path.join(three, 'package.json'), 'utf8'));
  assert(packageInfo.name === 'three' && packageInfo.version === version, `Expected the three@${version} npm package at ${three}.`);

  const index = await readFile(path.join(root, 'index.html'), 'utf8');
  for (const relative of ['build/three.module.js', 'examples/jsm/', decoderPath]) {
    assert(index.includes(cdn + relative), `Missing expected Three.js path ${relative} in index.html.`);
  }
  assert(index.includes(sourcesToggle), 'Missing the expected historical source selector in index.html.');
  const localIndex = index
    .replace(cdn + 'build/three.module.js', vendor + 'build/three.module.min.js')
    .replaceAll(cdn, vendor)
    .replace(sourcesToggle, 'const onlineSources = true;');

  for (const file of projectFiles) await stageFile(path.join(root, file), file);
  for (const file of threeFiles) await stageFile(path.join(three, file), path.join('vendor', 'three', file));
  await stageFile(path.join(three, 'LICENSE'), path.join('vendor', 'three', 'LICENSE.txt'));
  await stageFile(path.join(root, 'tools', 'licenses', 'draco.txt'), path.join('vendor', 'three', 'DRACO-LICENSE.txt'));
  await writeFile(path.join(output, 'index.html'), localIndex, 'utf8');
  console.log(`Staged U-505 for static hosting at ${output}`);
} catch (error) {
  console.error(`Could not stage U-505. ${error.message}`);
  console.error('See docs/RELEASE.md for the pinned dependency setup.');
  process.exitCode = 1;
}
