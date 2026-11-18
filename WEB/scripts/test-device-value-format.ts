import assert from 'node:assert/strict';
import { formatDeviceValue, normalizeDecimalPlaces } from '../src/utils/deviceValue';

assert.equal(formatDeviceValue(28.700000000000003), '28.7');
assert.equal(formatDeviceValue('28.7', 2), '28.70');
assert.equal(formatDeviceValue('30', 0), '30');
assert.equal(formatDeviceValue(false, 2), 'false');
assert.equal(formatDeviceValue('01 03 02 00 1E', 2), '01 03 02 00 1E');
assert.equal(formatDeviceValue('9223372036854775807'), '9223372036854775807');
assert.equal(formatDeviceValue('9223372036854775807', 2), '9223372036854775807.00');
assert.equal(normalizeDecimalPlaces(12), 10);
assert.equal(normalizeDecimalPlaces(-1), 0);
assert.equal(normalizeDecimalPlaces(''), undefined);

console.log('device value format contract: ok');
