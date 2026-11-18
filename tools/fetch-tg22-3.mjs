// Preserve the archive's TG 22.3 report and indexed enclosures for offline review.
// DNS was verified through Google's DNS-over-HTTPS service on 2026-11-17.
// curl --resolve preserves the HTTPS hostname and certificate verification.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import crypto from 'node:crypto';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const folder = path.join(root, 'docs', 'sources', 'tg-22-3');
const base = 'https://www.uboatarchive.net/U-505A/';
const address = process.env.U505_ARCHIVE_IP || '65.254.227.224';
fs.mkdirSync(folder, { recursive: true });
const records = [];
const failures = [];

function fetchFile(name, role) {
  if (path.basename(name) !== name) throw new Error(`Unexpected path: ${name}`);
  const url = new URL(name, base).href;
  const destination = path.join(folder, name);
  const result = spawnSync('curl.exe', ['--silent', '--show-error', '--fail',
    '--location', '--connect-timeout', '15', '--max-time', '45',
    '--resolve', `www.uboatarchive.net:443:${address}`, url, '--output', destination],
    { encoding: 'utf8', windowsHide: true });
  if (result.status !== 0) throw new Error(`${url}: ${result.stderr || result.error}`);
  const bytes = fs.readFileSync(destination);
  if (!bytes.length) throw new Error(`Empty download: ${url}`);
  if (/\.htm$/i.test(name) && !/<html[\s>]/i.test(bytes.toString('latin1'))) {
    throw new Error(`Not an HTML document: ${url}`);
  }
  records.push({ file: `tg-22-3/${name}`, url, role, bytes: bytes.length,
    sha256: crypto.createHash('sha256').update(bytes).digest('hex') });
  console.log(`${role}: ${name} (${bytes.length} bytes)`);
  return bytes.toString('latin1');
}

const index = fetchFile('U-505.htm', 'archive index');
const enclosureNames = [...index.matchAll(/href="([^"]+)"/gi)]
  .map(match => match[1])
  .filter(name => /^U-505.*\.htm$/i.test(name));
// The index's first 17 links are the report and Enclosures A1-A8, B-I.
const documents = [...new Set(enclosureNames.slice(0, 17))];
if (documents[0] !== 'U-505TG22.3Report.htm' || documents.at(-1) !== 'U-505ASCruise.htm') {
  throw new Error('Archive index changed; review the enclosure selection.');
}
const assetNames = new Set();
for (const [i, name] of documents.entries()) {
  const photoDetail = /^U-505EnclG\d+\.htm$/i.test(name);
  let html;
  try {
    html = fetchFile(name, photoDetail ? 'photograph detail' : i === 0 ? 'main report' : 'indexed enclosure');
  } catch (error) {
    if (!photoDetail) throw error;
    failures.push({ file: name, error: String(error) });
    console.warn(String(error));
    continue;
  }
  for (const match of html.matchAll(/href="(U-505EnclG\d+\.htm)"/gi)) {
    if (!documents.includes(match[1])) documents.push(match[1]);
  }
  for (const match of html.matchAll(/(?:src|href)="([^"#?]+\.(?:jpe?g|gif|png))"/gi)) {
    const asset = match[1];
    if (!asset.includes('/') && !asset.includes('\\')) assetNames.add(asset);
  }
}
for (const name of assetNames) {
  try { fetchFile(name, 'linked image'); }
  catch (error) {
    failures.push({ file: name, error: String(error) });
    console.warn(String(error));
  }
}
fs.writeFileSync(path.join(folder, 'manifest.json'), JSON.stringify({
  retrieved: new Date().toISOString(), source: 'U-boat Archive',
  transport: 'HTTPS with certificate verification; curl --resolve after public DNS lookup',
  address, scope: 'Main report, all 16 indexed enclosure pages, linked photograph detail pages, and their local image links; not an original archival scan packet',
  files: records, failures
}, null, 2) + '\n');
console.log(`Saved ${records.length} files; manifest: docs/sources/tg-22-3/manifest.json`);
