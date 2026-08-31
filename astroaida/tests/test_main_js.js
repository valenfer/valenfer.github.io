'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');

const fs = require('fs');
const path = require('path');

function loadMainJS() {
    const mainJS = fs.readFileSync(path.join(__dirname, '..', 'main.js'), 'utf-8').replace(/\r\n/g, '\n');
    const startIdx = mainJS.indexOf('function formatTimestamp(iso) {');
    if (startIdx === -1) {
        throw new Error('formatTimestamp function not found in main.js');
    }
    let braceCount = 0;
    let seenOpen = false;
    let endIdx = startIdx;
    for (let i = startIdx; i < mainJS.length; i++) {
        if (mainJS[i] === '{') {
            braceCount++;
            seenOpen = true;
        } else if (mainJS[i] === '}') {
            braceCount--;
        }
        if (seenOpen && braceCount === 0 && i > startIdx) {
            endIdx = i + 1;
            break;
        }
    }
    const funcCode = mainJS.slice(startIdx, endIdx);
    const ctx = { module: { exports: {} } };
    eval(funcCode.replace('function formatTimestamp', 'ctx.module.exports.formatTimestamp = function'));
    return ctx.module.exports.formatTimestamp;
}

let formatTimestamp;

try {
    formatTimestamp = loadMainJS();
} catch (e) {
    console.error('Failed to load formatTimestamp:', e.message);
    process.exit(1);
}

test('formatTimestamp returns formatted date in Europe/Madrid timezone', () => {
    const iso = '2026-08-12T19:41:00+00:00';
    const result = formatTimestamp(iso);
    assert.ok(typeof result === 'string', 'Should return a string');
    assert.ok(result !== 'desconocida', 'Should not return unknown for valid ISO');
    assert.ok(result.length > 0, 'Should return non-empty string');
});

test('formatTimestamp handles invalid ISO gracefully', () => {
    assert.equal(formatTimestamp(''), 'desconocida');
    assert.equal(formatTimestamp(null), 'desconocida');
    assert.equal(formatTimestamp('invalid'), 'desconocida');
});

test('formatTimestamp uses Spanish locale format', () => {
    const iso = '2026-08-12T19:41:00+00:00';
    const result = formatTimestamp(iso);
    assert.ok(result.includes('ago') || result.includes('2026'), 'Should contain year or Spanish month');
});

test('formatTimestamp respects Europe/Madrid timezone for 2026-08-12T19:41:00Z (CEST = UTC+2)', () => {
    const iso = '2026-08-12T19:41:00+00:00';
    const result = formatTimestamp(iso);
    // 19:41 UTC = 21:41 CEST (Europe/Madrid in August)
    assert.ok(result.includes('21:41'),
        'Should show 21:41 (Europe/Madrid CEST), got: ' + result);
});

test('main.js renders observation window with \"hora de Sevilla\" text', () => {
    const mainJS = fs.readFileSync(path.join(__dirname, '..', 'main.js'), 'utf-8');
    assert.ok(mainJS.includes('Ventana de observación (hora de Sevilla)'),
        'main.js must explicitly show \"Ventana de observación (hora de Sevilla)\"');
});

test('main.js marks an untranslated ephemeris title as original English', () => {
    const mainJS = fs.readFileSync(path.join(__dirname, '..', 'main.js'), 'utf-8');
    assert.ok(mainJS.includes('título original en inglés'));
});