import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { parse } from '@vue/compiler-sfc';

const filename = resolve(
  process.cwd(),
  'src/views/camera/components/AlgorithmTask/index.vue',
);
const source = readFileSync(filename, 'utf8');
const parsed = parse(source, { filename });

assert.deepEqual(parsed.errors, [], 'AlgorithmTask/index.vue must remain a valid Vue SFC');
assert.match(
  source,
  /:grid="\{\s*gutter:\s*12,\s*xs:\s*1,\s*sm:\s*1,\s*md:\s*2,\s*lg:\s*2,\s*xl:\s*3,\s*xxl:\s*4\s*\}"/,
  'task cards must use breakpoints that preserve a usable card width',
);
assert.match(source, /\.title\s*\{[\s\S]*?-webkit-line-clamp:\s*2;/);
assert.match(source, /\.btns\s*\{[\s\S]*?max-width:\s*280px;/);

console.log('algorithm task card layout: ok');
