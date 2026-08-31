'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');

const MoonRenderer = require('../moon-renderer.js');

const RADIUS = 100;

function diskSamples(resolution) {
  const samples = [];
  for (let yi = 0; yi <= resolution; yi++) {
    for (let xi = 0; xi <= resolution; xi++) {
      const x = -RADIUS + (2 * RADIUS * xi) / resolution;
      const y = -RADIUS + (2 * RADIUS * yi) / resolution;
      if (x * x + y * y <= RADIUS * RADIUS) {
        samples.push({ x, y });
      }
    }
  }
  return samples;
}

function avgBrightness(options, predicate) {
  const samples = diskSamples(40);
  let total = 0;
  let count = 0;
  for (const point of samples) {
    if (predicate && !predicate(point)) {
      continue;
    }
    total += MoonRenderer.lunarBrightnessAt(options, point.x, point.y, RADIUS);
    count++;
  }
  return count ? total / count : 0;
}

function rimBrightness(options, sideSign) {
  const res = 200;
  let total = 0;
  let count = 0;
  const inner = RADIUS * 0.9;
  for (let yi = 0; yi <= res; yi++) {
    for (let xi = 0; xi <= res; xi++) {
      const x = -RADIUS + (2 * RADIUS * xi) / res;
      const y = -RADIUS + (2 * RADIUS * yi) / res;
      const r2 = x * x + y * y;
      if (r2 >= inner * inner && r2 <= RADIUS * RADIUS && x * sideSign > 0) {
        total += MoonRenderer.lunarBrightnessAt(options, x, y, RADIUS);
        count++;
      }
    }
  }
  return count ? total / count : 0;
}

test('translatePhase maps common English phase names to Spanish', () => {
  assert.equal(MoonRenderer.translatePhase('New Moon'), 'Luna nueva');
  assert.equal(MoonRenderer.translatePhase('Waxing Crescent'), 'Luna creciente');
  assert.equal(MoonRenderer.translatePhase('First Quarter'), 'Cuarto creciente');
  assert.equal(MoonRenderer.translatePhase('Waxing Gibbous'), 'Gibosa creciente');
  assert.equal(MoonRenderer.translatePhase('Full Moon'), 'Luna llena');
  assert.equal(MoonRenderer.translatePhase('Waning Gibbous'), 'Gibosa menguante');
  assert.equal(MoonRenderer.translatePhase('Last Quarter'), 'Cuarto menguante');
  assert.equal(MoonRenderer.translatePhase('Waning Crescent'), 'Luna menguante');
  assert.equal(MoonRenderer.translatePhase('waning crescent'), 'Luna menguante');
  assert.equal(MoonRenderer.translatePhase('Fase desconocida'), 'Fase desconocida');
});

test('clampIllumination clamps to [0,1] and handles bad input', () => {
  assert.equal(MoonRenderer.clampIllumination(-0.2), 0);
  assert.equal(MoonRenderer.clampIllumination(1.7), 1);
  assert.equal(MoonRenderer.clampIllumination(0.065), 0.065);
  assert.equal(MoonRenderer.clampIllumination(0.5), 0.5);
  assert.equal(MoonRenderer.clampIllumination(NaN), 0);
  assert.equal(MoonRenderer.clampIllumination('no-numeric'), 0);
});

test('phaseParams flags waning vs waxing from the original phase name', () => {
  assert.equal(
    MoonRenderer.phaseParams({ illumination: 0.065, phase: 'Waning Crescent' }).waxing,
    false
  );
  assert.equal(
    MoonRenderer.phaseParams({ illumination: 0.065, phase: 'Waxing Crescent' }).waxing,
    true
  );
  assert.equal(MoonRenderer.phaseParams({ illumination: 1.5, phase: 'Full Moon' }).illumination, 1);
  assert.equal(MoonRenderer.phaseParams({ illumination: -0.3, phase: 'New Moon' }).illumination, 0);
});

test('phaseParams flags waning vs waxing from Spanish phase names', () => {
  assert.equal(
    MoonRenderer.phaseParams({ illumination: 0.065, phase: 'Luna menguante' }).waxing,
    false
  );
  assert.equal(
    MoonRenderer.phaseParams({ illumination: 0.3, phase: 'Cuarto menguante' }).waxing,
    false
  );
  assert.equal(
    MoonRenderer.phaseParams({ illumination: 0.9, phase: 'Gibosa menguante' }).waxing,
    false
  );
  assert.equal(
    MoonRenderer.phaseParams({ illumination: 0.065, phase: 'Luna creciente' }).waxing,
    true
  );
  assert.equal(
    MoonRenderer.phaseParams({ illumination: 0.5, phase: 'Cuarto creciente' }).waxing,
    true
  );
  assert.equal(
    MoonRenderer.phaseParams({ illumination: 0.9, phase: 'Gibosa creciente' }).waxing,
    true
  );
});

test('phaseParams falls back to options.waxing for unknown phase names', () => {
  assert.equal(MoonRenderer.phaseParams({ illumination: 0.5, phase: 'Fase misteriosa', waxing: false }).waxing, false);
  assert.equal(MoonRenderer.phaseParams({ illumination: 0.5, phase: 'Fase misteriosa', waxing: true }).waxing, true);
});

test('waning Spanish phases illuminate the left rim more than the right', () => {
  const phases = ['Luna menguante', 'Cuarto menguante', 'Gibosa menguante'];
  for (const phase of phases) {
    const params = MoonRenderer.phaseParams({ illumination: 0.065, phase });
    const options = { illumination: params.illumination, waxing: params.waxing };
    const left = rimBrightness(options, -1);
    const right = rimBrightness(options, 1);
    assert.ok(
      left > right + 0.01,
      phase + ': expected left rim (' + left + ') >> right rim (' + right + ')'
    );
  }
});

test('waxing Spanish phases illuminate the right rim more than the left', () => {
  const phases = ['Luna creciente', 'Cuarto creciente', 'Gibosa creciente'];
  for (const phase of phases) {
    const params = MoonRenderer.phaseParams({ illumination: 0.065, phase });
    const options = { illumination: params.illumination, waxing: params.waxing };
    const left = rimBrightness(options, -1);
    const right = rimBrightness(options, 1);
    assert.ok(
      right > left + 0.01,
      phase + ': expected right rim (' + right + ') >> left rim (' + left + ')'
    );
  }
});

test('full moon is sufficiently bright', () => {
  const params = MoonRenderer.phaseParams({ illumination: 1, phase: 'Full Moon' });
  const options = { illumination: params.illumination, waxing: params.waxing };
  const center = MoonRenderer.lunarBrightnessAt(options, 0, 0, RADIUS);
  assert.ok(center >= 0.7, 'full moon center should be near-white, got ' + center);
  const avg = avgBrightness(options);
  assert.ok(avg >= 0.45, 'full moon disk should be clearly bright, got ' + avg);
});

test('full moon stays bright regardless of side convention', () => {
  const waning = avgBrightness({ illumination: 1, waxing: false });
  const waxing = avgBrightness({ illumination: 1, waxing: true });
  assert.ok(Math.abs(waning - waxing) < 0.05, 'side must not matter for a full moon');
});

test('new moon is dark but shows subtle earthshine', () => {
  const params = MoonRenderer.phaseParams({ illumination: 0, phase: 'New Moon' });
  const options = { illumination: params.illumination, waxing: params.waxing };
  const avg = avgBrightness(options);
  assert.ok(avg > 0.005, 'new moon should show subtle earthshine, got ' + avg);
  assert.ok(avg < 0.1, 'new moon should be mostly dark, got ' + avg);
});

test('waning crescent illuminates the left rim more than the right', () => {
  const params = MoonRenderer.phaseParams({ illumination: 0.065, phase: 'Waning Crescent' });
  const options = { illumination: params.illumination, waxing: params.waxing };
  const left = rimBrightness(options, -1);
  const right = rimBrightness(options, 1);
  assert.ok(left > right + 0.01, 'expected left rim (' + left + ') >> right rim (' + right + ')');
});

test('waxing crescent illuminates the right rim more than the left', () => {
  const params = MoonRenderer.phaseParams({ illumination: 0.065, phase: 'Waxing Crescent' });
  const options = { illumination: params.illumination, waxing: params.waxing };
  const left = rimBrightness(options, -1);
  const right = rimBrightness(options, 1);
  assert.ok(right > left + 0.01, 'expected right rim (' + right + ') >> left rim (' + left + ')');
});

test('renderMoon draws a visible disk on a canvas-like context', () => {
  let drawn = null;
  const context = {
    createImageData(width, height) {
      return { width, height, data: new Uint8ClampedArray(width * height * 4) };
    },
    putImageData(imageData) {
      drawn = imageData;
    },
    beginPath() {},
    arc() {},
    stroke() {},
  };
  const canvas = { width: 0, height: 0, getContext() { return context; } };
  const result = MoonRenderer.renderMoon(canvas, { illumination: 1, phase: 'Full Moon', size: 100 });
  assert.equal(result, canvas);
  assert.equal(canvas.width, 100);
  assert.equal(canvas.height, 100);
  assert.ok(drawn && drawn.data, 'renderMoon should draw through putImageData');
  let lit = 0;
  for (let i = 0; i < drawn.data.length; i += 4) {
    if (drawn.data[i + 3] > 0) {
      lit++;
    }
  }
  const diskPixels = Math.PI * 50 * 50;
  assert.ok(lit > diskPixels * 0.9, 'most disk pixels should be painted, got ' + lit);
});

test('renderMoon caps backing resolution at DPR 2', () => {
  const previousWindow = global.window;
  global.window = { devicePixelRatio: 3 };
  try {
    const context = {
      createImageData(width, height) {
        return { width, height, data: new Uint8ClampedArray(width * height * 4) };
      },
      putImageData() {},
      beginPath() {},
      arc() {},
      stroke() {},
    };
    const canvas = { width: 0, height: 0, getContext() { return context; } };
    MoonRenderer.renderMoon(canvas, { illumination: 1, phase: 'Full Moon', size: 100 });
    assert.equal(canvas.width, 200);
    assert.equal(canvas.height, 200);
  } finally {
    if (previousWindow === undefined) {
      delete global.window;
    } else {
      global.window = previousWindow;
    }
  }
});

const PIXEL_SIZE = 280;

function renderPixels(options) {
  let drawn = null;
  const context = {
    createImageData(width, height) {
      return { width, height, data: new Uint8ClampedArray(width * height * 4) };
    },
    putImageData(imageData) {
      drawn = imageData;
    },
    beginPath() {},
    arc() {},
    stroke() {},
  };
  const canvas = { width: 0, height: 0, getContext() { return context; } };
  MoonRenderer.renderMoon(canvas, Object.assign({ size: PIXEL_SIZE }, options));
  assert.ok(drawn && drawn.data, 'renderMoon should draw through putImageData');
  assert.equal(canvas.width, PIXEL_SIZE);
  return { image: drawn, size: canvas.width };
}

function diskStats(image, size) {
  const radius = size / 2;
  const all = [];
  const lit = [];
  const dark = [];
  let left = 0;
  let leftN = 0;
  let right = 0;
  let rightN = 0;
  let leftBand = 0;
  let leftBandN = 0;
  let rightBand = 0;
  let rightBandN = 0;
  let max = 0;
  let white = 0;
  for (let py = 0; py < size; py++) {
    for (let px = 0; px < size; px++) {
      const i = (py * size + px) * 4;
      if (image.data[i + 3] === 0) {
        continue;
      }
      const x = px - radius + 0.5;
      const y = py - radius + 0.5;
      const g = (image.data[i] + image.data[i + 1] + image.data[i + 2]) / 3;
      all.push(g);
      if (g > max) {
        max = g;
      }
      if (g >= 230) {
        white++;
      }
      if (g >= 140) {
        lit.push(g);
      } else if (g < 100) {
        dark.push(g);
      }
      if (x < 0) {
        left += g;
        leftN++;
      } else {
        right += g;
        rightN++;
      }
      if (x < -0.55 * radius) {
        leftBand += g;
        leftBandN++;
      }
      if (x > 0.55 * radius) {
        rightBand += g;
        rightBandN++;
      }
    }
  }
  const mean = (arr) => (arr.length ? arr.reduce((s, v) => s + v, 0) / arr.length : NaN);
  const std = (arr) => {
    if (arr.length < 2) {
      return NaN;
    }
    const m = mean(arr);
    return Math.sqrt(arr.reduce((s, v) => s + (v - m) * (v - m), 0) / arr.length);
  };
  return {
    max,
    white,
    mean: mean(all),
    std: std(all),
    leftMean: left / leftN,
    rightMean: right / rightN,
    leftBandMean: leftBand / leftBandN,
    rightBandMean: rightBand / rightBandN,
    litCount: lit.length,
    litMean: mean(lit),
    litStd: std(lit),
    darkMean: mean(dark),
    darkStd: std(dark),
  };
}

test('renderMoon waning crescent shows a clearly brighter left crescent on real pixels', () => {
  const { image, size } = renderPixels({ illumination: 0.065, phase: 'Waning Crescent' });
  const s = diskStats(image, size);
  assert.ok(s.max >= 215, 'crescent peak should be near-white, got ' + s.max);
  assert.ok(s.litCount >= 120, 'a perceptible number of crescent pixels should be bright, got ' + s.litCount);
  assert.ok(
    s.leftBandMean >= s.rightBandMean + 18,
    'left limb (' + s.leftBandMean + ') should be clearly brighter than right limb (' + s.rightBandMean + ')'
  );
});

test('renderMoon waning crescent dark side is dark with subtle earthshine and texture', () => {
  const { image, size } = renderPixels({ illumination: 0.065, phase: 'Waning Crescent' });
  const s = diskStats(image, size);
  assert.ok(s.darkMean >= 12 && s.darkMean <= 46, 'dark face should be dark but not black, got ' + s.darkMean);
  assert.ok(s.darkStd >= 2.5, 'dark face should keep measurable texture, got ' + s.darkStd);
});

test('renderMoon full moon is predominantly light gray/white with albedo variation', () => {
  const { image, size } = renderPixels({ illumination: 1, phase: 'Full Moon' });
  const s = diskStats(image, size);
  const diskPixels = (Math.PI * size * size) / 4;
  assert.ok(s.mean >= 200, 'full moon mean should be light gray, got ' + s.mean);
  assert.ok(s.white >= diskPixels * 0.05, 'full moon should have many near-white pixels, got ' + s.white);
  assert.ok(s.std >= 18, 'full moon should show albedo/crater variation, got ' + s.std);
});
