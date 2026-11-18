// Check provenance wiring and the generated list's previously missing assumption groups.
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';

const root = fileURLToPath(new URL('../', import.meta.url));
const html = readFileSync(path.join(root, 'index.html'), 'utf8');
const block = id => {
  const match = html.match(new RegExp('<script[^>]*id="' + id + '"[^>]*>([\\s\\S]*?)</script>'));
  assert(match, 'Missing script ' + id);
  return match[1];
};
const data = {};
for (const match of html.matchAll(/<script type="application\/json" id="data-([^"]+)">([\s\S]*?)<\/script>/g)) {
  data[match[1]] = JSON.parse(match[2]);
}
new Function(block('evidence')).call(globalThis);
const assumptions = U505Evidence.assumptions(data);
for (const item of data.items.items) {
  assert(assumptions.some(r => r.path.endsWith('[' + item.id + ']') && r.fields.includes('weight')),
    'Item weight missing from assumptions: ' + item.id);
}
for (const group of ['compartments.hull', 'systems.doors', 'systems.drains', 'scenario', 'epilogue.awash']) {
  assert(assumptions.some(r => r.path.startsWith('game.' + group)), 'Missing assumption group: ' + group);
}
assert(assumptions.some(r => r.path.includes('sea_strainer')), 'Mixed strainer data must remain flagged');
assert(assumptions.some(r => r.path.endsWith('ballast_tanks')), 'Sibling status metadata must be collected');
assert.equal(data.codex.entries.length, 25);
for (const entry of data.codex.entries) {
  for (const key of entry.sources) assert(data.codex.sources[key], entry.id + ': unknown source ' + key);
  if (entry.flag === 'real') assert(entry.locator, entry.id + ': missing passage locator');
}
for (const source of Object.values(data.codex.sources)) {
  if (source.local_url) assert(existsSync(path.join(root, decodeURIComponent(source.local_url))),
    'Missing offline source: ' + source.local_url);
}
assert.equal(data.act2.start, data.scenario.boarding_at);
assert.equal(data.epilogue.awash.pump_type, 'electric_submersible');
assert(data.systems.pumps[data.epilogue.awash.pump_type], 'Missing 7 June pump model');
assert.equal(data.charges.charges.length, 2, 'Retain the two representative placeholders');
assert(data.charges.charges.every(r => r.placeholder && r.status === 'placeholder'));
assert.equal(data.scenario.power_available, false, 'Own-pump availability remains unresolved');
console.log(`Evidence checks passed: 25 codex entries, ${assumptions.length} assumption records, local sources and scene metadata.`);
