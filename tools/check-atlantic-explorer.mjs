import assert from 'node:assert/strict';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const asset = path.join(root, 'art', 'atlantic_explorer');

function parseGlb(bytes) {
  assert.equal(bytes.toString('ascii', 0, 4), 'glTF', 'GLB magic');
  assert.equal(bytes.readUInt32LE(4), 2, 'GLB version');
  assert.equal(bytes.readUInt32LE(8), bytes.length, 'GLB declared length');
  let offset = 12, json, bin;
  while (offset < bytes.length) {
    const length = bytes.readUInt32LE(offset);
    const type = bytes.toString('ascii', offset + 4, offset + 8);
    const chunk = bytes.subarray(offset + 8, offset + 8 + length);
    if (type === 'JSON') json = JSON.parse(chunk.toString('utf8').trim());
    if (type === 'BIN\0') bin = chunk;
    offset += 8 + length;
  }
  assert(json && bin, 'GLB contains JSON and binary chunks');
  return { json, bin };
}

function imageDimensions(bytes) {
  if (bytes.length >= 24 && bytes.toString('hex', 0, 8) === '89504e470d0a1a0a') {
    return [bytes.readUInt32BE(16), bytes.readUInt32BE(20)];
  }
  if (bytes[0] === 0xff && bytes[1] === 0xd8) {
    let offset = 2;
    while (offset + 9 < bytes.length) {
      if (bytes[offset] !== 0xff) { offset += 1; continue; }
      const marker = bytes[offset + 1];
      const length = bytes.readUInt16BE(offset + 2);
      if ([0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf].includes(marker)) {
        return [bytes.readUInt16BE(offset + 7), bytes.readUInt16BE(offset + 5)];
      }
      offset += 2 + length;
    }
  }
  throw new Error('Unsupported embedded image format');
}

function embeddedImageSizes(glb) {
  return (glb.json.images || []).map(image => {
    const view = glb.json.bufferViews[image.bufferView];
    const start = view.byteOffset || 0;
    return imageDimensions(glb.bin.subarray(start, start + view.byteLength));
  });
}

function triangleCount(json) {
  return (json.meshes || []).reduce((sum, mesh) => sum + mesh.primitives.reduce((meshSum, primitive) => {
    assert.equal(primitive.mode ?? 4, 4, `mesh ${mesh.name} uses triangles`);
    return meshSum + json.accessors[primitive.indices].count / 3;
  }, 0), 0);
}

function requireNames(json, names) {
  const available = new Set((json.nodes || []).map(node => node.name));
  for (const name of names) assert(available.has(name), `missing node ${name}`);
}

const renderPath = path.join(asset, 'atlantic_explorer_vr.glb');
const dracoPath = path.join(asset, 'atlantic_explorer_vr_draco.glb');
const collisionPath = path.join(asset, 'atlantic_explorer_collision.glb');
const [render, draco, collision] = await Promise.all([
  readFile(renderPath).then(parseGlb),
  readFile(dracoPath).then(parseGlb),
  readFile(collisionPath).then(parseGlb),
]);

const failureNodes = [
  'Viewport_Pilot', 'Viewport_Passenger',
  'Lights_PilotEnd', 'Lights_PassengerEnd', 'Lights_Cabin',
  'Thruster_PilotEnd_Port_Horizontal', 'Thruster_PilotEnd_Port_Vertical',
  'Thruster_PilotEnd_Starboard_Horizontal', 'Thruster_PilotEnd_Starboard_Vertical',
  'Thruster_PassengerEnd_Port_Horizontal', 'Thruster_PassengerEnd_Port_Vertical',
  'Thruster_PassengerEnd_Starboard_Horizontal', 'Thruster_PassengerEnd_Starboard_Vertical',
];
const anchors = [
  'XR_ORIGIN', 'XR_HEAD_PILOT', 'XR_HANDS_PILOT',
  'ANCHOR_VIEWPORT_PILOT', 'ANCHOR_VIEWPORT_PASSENGER',
  'ANCHOR_PRESSURE_HULL', 'ANCHOR_BATTERY', 'ANCHOR_LIFE_SUPPORT',
  'ANCHOR_AUDIO_HULL', 'ANCHOR_LEAK_PILOT', 'ANCHOR_LEAK_PASSENGER',
];
requireNames(render.json, [...failureNodes, ...anchors]);
requireNames(collision.json, [
  'COL_ExteriorHull', 'COL_CabinFloor', 'COL_CabinCeiling',
  'COL_CabinPort', 'COL_CabinStarboard', 'COL_CabinPilotEnd', 'COL_CabinPassengerEnd',
]);

const triangles = triangleCount(render.json);
assert.equal(triangles, 120380, 'render triangle count remains stable');
assert.equal(triangleCount(draco.json), triangles, 'Draco and plain GLBs describe the same geometry');
assert.equal((collision.json.meshes || []).length, 7, 'collision proxy count');
assert(draco.json.extensionsUsed?.includes('KHR_draco_mesh_compression'), 'Draco extension present');
assert(!render.json.extensionsUsed?.includes('KHR_draco_mesh_compression'), 'plain GLB needs no Draco decoder');

const imageSizes = embeddedImageSizes(render);
assert(imageSizes.length > 0, 'render GLB embeds textures');
for (const [width, height] of imageSizes) {
  assert(width <= 2048 && height <= 2048, `texture exceeds VR limit: ${width}x${height}`);
}
const glass = render.json.materials.find(material => material.name === 'TransparentItems');
assert(glass && glass.alphaMode !== 'OPAQUE', 'viewport material exports with alpha');

const [plainBytes, dracoBytes] = await Promise.all([stat(renderPath), stat(dracoPath)]);
assert(dracoBytes.size < plainBytes.size, 'Draco build is smaller than plain build');
console.log(`Atlantic Explorer VR OK: ${triangles.toLocaleString()} triangles, ${render.json.meshes.length} meshes, ${imageSizes.length} embedded textures`);
console.log(`Plain ${(plainBytes.size / 1048576).toFixed(1)} MiB · Draco ${(dracoBytes.size / 1048576).toFixed(1)} MiB · max texture 2048 px`);
