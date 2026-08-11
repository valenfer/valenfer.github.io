'use strict';

(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.MoonRenderer = factory();
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var DEFAULT_EARTHSHINE = 0.07;
  var DEFAULT_SIZE = 280;

  var TONE_GAMMA = 0.28;
  var TEX_LOW = 0.55;
  var TEX_GAIN = 0.45;
  var GRAY_BASE = 18;
  var GRAY_GAIN = 270;

  var PHASE_TRANSLATIONS = {
    'new moon': 'Luna nueva',
    'waxing crescent': 'Luna creciente',
    'first quarter': 'Cuarto creciente',
    'waxing gibbous': 'Gibosa creciente',
    'full moon': 'Luna llena',
    'waning gibbous': 'Gibosa menguante',
    'last quarter': 'Cuarto menguante',
    'waning crescent': 'Luna menguante'
  };

  var MARIA = [
    { x: -0.22, y: 0.28, r: 0.34, a: 0.22 },
    { x: 0.16, y: 0.04, r: 0.30, a: 0.18 },
    { x: 0.38, y: 0.38, r: 0.20, a: 0.14 },
    { x: -0.08, y: -0.38, r: 0.24, a: 0.14 },
    { x: 0.08, y: 0.52, r: 0.16, a: 0.12 },
    { x: -0.36, y: 0.02, r: 0.20, a: 0.10 },
    { x: 0.30, y: -0.22, r: 0.16, a: 0.09 },
    { x: 0.02, y: -0.52, r: 0.14, a: 0.08 }
  ];

  var CRATERS = [
    { x: -0.02, y: 0.24, r: 0.055, a: 0.10 },
    { x: -0.10, y: -0.06, r: 0.045, a: 0.08 },
    { x: -0.16, y: 0.02, r: 0.032, a: 0.08 },
    { x: -0.21, y: -0.04, r: 0.030, a: 0.10 },
    { x: -0.05, y: -0.30, r: 0.040, a: 0.06 },
    { x: 0.14, y: 0.22, r: 0.045, a: 0.08 },
    { x: 0.02, y: 0.42, r: 0.060, a: 0.05 },
    { x: -0.27, y: 0.16, r: 0.050, a: 0.05 },
    { x: -0.03, y: -0.48, r: 0.050, a: 0.05 },
    { x: 0.28, y: -0.28, r: 0.045, a: 0.05 }
  ];

  function clampIllumination(value) {
    value = Number(value);
    if (!isFinite(value)) {
      return 0;
    }
    return Math.min(1, Math.max(0, value));
  }

  function normalizePhaseName(name) {
    return String(name || '').trim().toLowerCase().replace(/\s+/g, ' ');
  }

  function translatePhase(name) {
    var key = normalizePhaseName(name);
    if (Object.prototype.hasOwnProperty.call(PHASE_TRANSLATIONS, key)) {
      return PHASE_TRANSLATIONS[key];
    }
    return String(name || '');
  }

  function phaseParams(options) {
    options = options || {};
    var phase = normalizePhaseName(options.phase);
    var illumination = clampIllumination(options.illumination);
    var waxing = true;
    if (phase.indexOf('waning') !== -1 || phase.indexOf('menguante') !== -1) {
      waxing = false;
    } else if (phase.indexOf('waxing') !== -1 || phase.indexOf('creciente') !== -1) {
      waxing = true;
    } else if (typeof options.waxing === 'boolean') {
      waxing = options.waxing;
    }
    return { illumination: illumination, waxing: waxing };
  }

  function hash2(x, y) {
    var h = (x | 0) * 374761393 + (y | 0) * 668265263;
    h = (h ^ (h >>> 13)) * 1274126177;
    h = h ^ (h >>> 16);
    return (h >>> 0) / 4294967296;
  }

  function smoothstep(t) {
    return t * t * (3 - 2 * t);
  }

  function valueNoise(x, y) {
    var xi = Math.floor(x);
    var yi = Math.floor(y);
    var xf = x - xi;
    var yf = y - yi;
    var a = hash2(xi, yi);
    var b = hash2(xi + 1, yi);
    var c = hash2(xi, yi + 1);
    var d = hash2(xi + 1, yi + 1);
    var u = smoothstep(xf);
    var v = smoothstep(yf);
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
  }

  function albedo(ux, uy) {
    var maria = 0;
    for (var i = 0; i < MARIA.length; i++) {
      var m = MARIA[i];
      var dx = ux - m.x;
      var dy = uy - m.y;
      var d2 = dx * dx + dy * dy;
      maria += m.a * Math.exp(-d2 / (m.r * m.r));
    }
    var craterGlow = 0;
    for (var c = 0; c < CRATERS.length; c++) {
      var k = CRATERS[c];
      var kx = ux - k.x;
      var ky = uy - k.y;
      var kd = Math.sqrt(kx * kx + ky * ky);
      var ring = (kd - k.r) / (k.r * 0.16);
      craterGlow += k.a * Math.exp(-ring * ring);
    }
    var coarse = valueNoise(ux * 9 + 7.3, uy * 9 + 2.1);
    var fine = valueNoise(ux * 31 + 1.7, uy * 31 + 5.9);
    var factor = 1 - maria * 0.62 - (coarse - 0.5) * 0.12 - (fine - 0.5) * 0.05 + craterGlow;
    return Math.min(1, Math.max(0.55, factor));
  }

  function lunarBrightnessAt(options, x, y, radius) {
    options = options || {};
    radius = Number(radius) || 1;
    var ux = x / radius;
    var uy = y / radius;
    var d2 = ux * ux + uy * uy;
    if (d2 > 1) {
      return 0;
    }
    var z = Math.sqrt(1 - d2);
    var illumination = clampIllumination(options.illumination);
    var waxing = options.waxing !== false;
    var cosA = 2 * illumination - 1;
    var sinA = Math.sqrt(Math.max(0, 1 - cosA * cosA));
    var side = waxing ? 1 : -1;
    var sunlit = side * sinA * ux + cosA * z;
    if (sunlit < 0) {
      sunlit = 0;
    }
    var earthshine = (typeof options.earthshine === 'number')
      ? options.earthshine
      : DEFAULT_EARTHSHINE;
    var lit = sunlit + earthshine * z * (1 - sunlit);
    var texture = options.texture === false ? 1 : albedo(ux, uy);
    return lit * texture;
  }

  function renderMoon(canvas, options) {
    options = options || {};
    var size = options.size || DEFAULT_SIZE;
    var dpr = Math.min(2, (typeof window !== 'undefined' && window.devicePixelRatio) || 1);
    var backing = Math.round(size * dpr);
    canvas.width = backing;
    canvas.height = backing;
    var ctx = canvas.getContext && canvas.getContext('2d');
    if (!ctx || typeof ctx.createImageData !== 'function') {
      return canvas;
    }
    var imageData = ctx.createImageData(backing, backing);
    var pixels = imageData.data;
    var radius = backing / 2;
    var params = phaseParams(options);
    var illumination = params.illumination;
    var earthshine = (typeof options.earthshine === 'number')
      ? options.earthshine
      : DEFAULT_EARTHSHINE;
    var useTexture = options.texture !== false;
    var cosA = 2 * illumination - 1;
    var sinA = Math.sqrt(Math.max(0, 1 - cosA * cosA));
    var side = params.waxing ? 1 : -1;
    var index = 0;
    for (var py = 0; py < backing; py++) {
      var y = py - radius + 0.5;
      for (var px = 0; px < backing; px++) {
        var x = px - radius + 0.5;
        var ux = x / radius;
        var uy = y / radius;
        var d2 = ux * ux + uy * uy;
        var gray = -1;
        if (d2 <= 1) {
          var z = Math.sqrt(1 - d2);
          var sunlit = side * sinA * ux + cosA * z;
          if (sunlit < 0) {
            sunlit = 0;
          }
          var tex = useTexture ? albedo(ux, uy) : 1;
          var display;
          if (sunlit > 0) {
            display = Math.pow(sunlit, TONE_GAMMA) * (TEX_LOW + TEX_GAIN * tex);
          } else {
            display = earthshine * z * tex;
          }
          gray = GRAY_BASE + GRAY_GAIN * display;
        }
        if (gray >= 0) {
          pixels[index] = Math.min(255, Math.round(gray));
          pixels[index + 1] = Math.min(255, Math.round(gray + 4));
          pixels[index + 2] = Math.min(255, Math.round(gray + 8));
          pixels[index + 3] = 255;
        }
        index += 4;
      }
    }
    ctx.putImageData(imageData, 0, 0);
    ctx.beginPath();
    ctx.arc(radius, radius, radius - 0.5, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
    ctx.lineWidth = 1;
    ctx.stroke();
    return canvas;
  }

  return {
    DEFAULT_EARTHSHINE: DEFAULT_EARTHSHINE,
    DEFAULT_SIZE: DEFAULT_SIZE,
    clampIllumination: clampIllumination,
    translatePhase: translatePhase,
    phaseParams: phaseParams,
    lunarBrightnessAt: lunarBrightnessAt,
    renderMoon: renderMoon
  };
});
