'use strict';

(function () {
  var DATA_PREFIX = 'data/';
  var MAX_AGE_HOURS = 48;

  var MODULES = ['apod', 'sky-today', 'moon', 'star-chart', 'near-earth'];

  var LABELS = {
    apod: 'Astronomía del día',
    'sky-today': 'Cielo hoy',
    moon: 'Luna',
    'star-chart': 'Carta celeste',
    'near-earth': 'Objetos cercanos'
  };

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== undefined && text !== null) {
      node.textContent = text;
    }
    return node;
  }

  function moduleContainer(name) {
    return document.querySelector('[data-module="' + name + '"]');
  }

  function moduleNotice(name, message) {
    var container = moduleContainer(name);
    if (!container) {
      return;
    }
    container.textContent = '';
    container.appendChild(el('p', 'module__notice', message));
    container.classList.add('is-unavailable');
  }

  function formatNumber(value) {
    return value.toLocaleString('es-ES', { maximumFractionDigits: 0 });
  }

  function formatAngle(value) {
    if (value === undefined || value === null || isNaN(value)) {
      return '—';
    }
    return value.toFixed(1) + '°';
  }

  function formatTimestamp(iso) {
    if (!iso) {
      return 'desconocida';
    }
    var date = new Date(iso);
    if (isNaN(date.getTime())) {
      return 'desconocida';
    }
    return date.toLocaleString('es-ES', { dateStyle: 'medium', timeStyle: 'short' });
  }

  function isStale(iso) {
    if (!iso) {
      return true;
    }
    var then = Date.parse(iso);
    if (isNaN(then)) {
      return true;
    }
    return (Date.now() - then) > MAX_AGE_HOURS * 60 * 60 * 1000;
  }

  function moduleImage(url, altText) {
    var img = el('img');
    img.src = url;
    img.alt = altText;
    img.loading = 'lazy';
    img.decoding = 'async';
    img.addEventListener('error', function () {
      var fallback = el('p', 'module__notice', 'Imagen no disponible en este momento.');
      img.replaceWith(fallback);
    });
    return img;
  }

  function addStat(list, label, value) {
    list.appendChild(el('dt', 'moon__stat-label', label));
    list.appendChild(el('dd', 'moon__stat-value', value === null || value === undefined ? '—' : value));
  }

  function renderApod(data) {
    var container = moduleContainer('apod');
    container.textContent = '';

    var media;
    if (data.media_type === 'video') {
      media = el('iframe', 'apod__media apod__media--video');
      media.src = data.url;
      media.title = 'Vídeo astronómico del día';
      media.loading = 'lazy';
      media.setAttribute('frameborder', '0');
      media.setAttribute('allowfullscreen', '');
      media.setAttribute('referrerpolicy', 'strict-origin-when-cross-origin');
      media.setAttribute('allow', 'encrypted-media; picture-in-picture');
    } else {
      media = moduleImage(data.url, 'Imagen astronómica del día');
      media.className = 'apod__media';
    }
    container.appendChild(media);

    var body = el('div', 'apod__body');
    var title = el('h3', 'apod__title', data.title || 'Imagen astronómica del día');
    body.appendChild(title);

    var meta = el('p', 'apod__meta');
    if (data.date) {
      meta.appendChild(el('span', 'apod__date', data.date));
    }
    if (data.copyright) {
      meta.appendChild(el('span', 'apod__credit', '© ' + data.copyright));
    }
    body.appendChild(meta);

    if (data.explanation) {
      body.appendChild(el('p', 'apod__explanation', data.explanation));
    }
    container.appendChild(body);
  }

  function renderSkyToday(data) {
    var container = moduleContainer('sky-today');
    container.textContent = '';

    if (!data.bodies || !data.bodies.length) {
      container.appendChild(el('p', 'module__notice', 'No hay cuerpos visibles registrados.'));
      return;
    }

    var table = el('table', 'sky-table');
    table.setAttribute('aria-label', 'Posiciones actuales de los cuerpos celestes desde Sevilla');

    var thead = el('thead');
    var headRow = el('tr');
    ['Cuerpo', 'Altitud', 'Acimut', 'Magnitud', 'Constelación'].forEach(function (label) {
      headRow.appendChild(el('th', null, label));
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    var tbody = el('tbody');
    data.bodies.forEach(function (body) {
      var row = el('tr');
      var nameCell = el('th', null, body.name || '—');
      nameCell.setAttribute('scope', 'row');
      row.appendChild(nameCell);
      row.appendChild(el('td', null, formatAngle(body.altitude)));
      row.appendChild(el('td', null, formatAngle(body.azimuth)));
      var magnitude = (body.magnitude === undefined || body.magnitude === null || isNaN(body.magnitude))
        ? '—'
        : body.magnitude.toFixed(1);
      row.appendChild(el('td', null, magnitude));
      row.appendChild(el('td', null, body.constellation || '—'));
      tbody.appendChild(row);
    });
    table.appendChild(tbody);

    var region = el('div', 'sky-table-region');
    region.setAttribute('role', 'region');
    region.setAttribute('aria-label', 'Posiciones actuales de los cuerpos celestes desde Sevilla: desplaza la tabla en horizontal.');
    region.setAttribute('tabindex', '0');
    region.appendChild(el('p', 'sky-table-region__hint', 'Desliza en horizontal para ver la tabla completa.'));
    region.appendChild(table);
    container.appendChild(region);
  }

  function renderMoon(data) {
    var container = moduleContainer('moon');
    container.textContent = '';

    if (!window.MoonRenderer) {
      container.appendChild(el('p', 'module__notice', 'La fase lunar no está disponible en este momento.'));
      return;
    }

    var params = window.MoonRenderer.phaseParams(data);
    var phaseEs = window.MoonRenderer.translatePhase(data.phase);
    var phaseLabel = phaseEs || 'Fase lunar';
    var illuminationPct = Math.round(params.illumination * 100);

    var figure = el('figure', 'moon__figure');
    var canvas = el('canvas', 'moon__canvas');
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', 'Fase lunar: ' + phaseLabel + ', iluminación al ' + illuminationPct + ' %.');
    window.MoonRenderer.renderMoon(canvas, {
      illumination: data.illumination,
      phase: data.phase,
      size: 280
    });
    figure.appendChild(canvas);
    figure.appendChild(el('figcaption', null, phaseLabel));
    container.appendChild(figure);

    var stats = el('dl', 'moon__stats');
    addStat(stats, 'Fase', phaseLabel);
    addStat(stats, 'Iluminación', illuminationPct + ' %');
    var distance = (data.distance_km === undefined || data.distance_km === null || isNaN(data.distance_km))
      ? '—'
      : formatNumber(data.distance_km) + ' km';
    addStat(stats, 'Distancia', distance);
    container.appendChild(stats);
  }

  function renderStarChart(data) {
    var container = moduleContainer('star-chart');
    container.textContent = '';

    if (!data.image_url) {
      container.appendChild(el('p', 'module__notice', 'Carta celeste no disponible.'));
      return;
    }

    var observerLabel = (data.observer && data.observer.label) ? data.observer.label : 'el observador';
    var figure = el('figure', 'chart__figure');
    figure.appendChild(moduleImage(data.image_url, 'Carta celeste para ' + observerLabel));
    figure.appendChild(el('figcaption', null, 'Carta celeste generada para ' + observerLabel));
    container.appendChild(figure);
  }

  function renderNearEarth(data) {
    var container = moduleContainer('near-earth');
    container.textContent = '';

    if (!data.asteroids || !data.asteroids.length) {
      container.appendChild(el('p', 'module__notice', 'No hay objetos cercanos registrados en esta ventana.'));
      return;
    }

    var list = el('ul', 'asteroid-list');
    data.asteroids.forEach(function (asteroid) {
      var item = el('li', 'asteroid');

      var heading = el('div', 'asteroid__heading');
      heading.appendChild(el('span', 'asteroid__name', asteroid.name || 'Objeto'));
      if (asteroid.hazardous) {
        heading.appendChild(el('span', 'badge badge--danger', 'Potencialmente peligroso'));
      } else {
        heading.appendChild(el('span', 'badge badge--ok', 'Sin riesgo'));
      }
      item.appendChild(heading);

      var stats = el('dl', 'asteroid__stats');
      addStat(stats, 'Fecha', asteroid.date || '—');
      var diameter = (asteroid.estimated_diameter_km && asteroid.estimated_diameter_km.min !== undefined)
        ? asteroid.estimated_diameter_km.min.toFixed(2) + ' – ' + asteroid.estimated_diameter_km.max.toFixed(2) + ' km'
        : '—';
      addStat(stats, 'Diámetro estimado', diameter);
      var miss = (asteroid.miss_distance_km === undefined || asteroid.miss_distance_km === null || isNaN(asteroid.miss_distance_km))
        ? '—'
        : formatNumber(asteroid.miss_distance_km) + ' km';
      addStat(stats, 'Distancia mínima', miss);
      var velocity = (asteroid.velocity_km_s === undefined || asteroid.velocity_km_s === null || isNaN(asteroid.velocity_km_s))
        ? '—'
        : asteroid.velocity_km_s.toFixed(1) + ' km/s';
      addStat(stats, 'Velocidad', velocity);
      item.appendChild(stats);

      if (asteroid.nasa_url) {
        var link = el('a', 'asteroid__link', 'Ficha en el JPL');
        link.href = asteroid.nasa_url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        item.appendChild(link);
      }

      list.appendChild(item);
    });
    container.appendChild(list);
  }

  var RENDERERS = {
    apod: renderApod,
    'sky-today': renderSkyToday,
    moon: renderMoon,
    'star-chart': renderStarChart,
    'near-earth': renderNearEarth
  };

  function updateStatus(results) {
    var list = document.querySelector('.data-status__list');
    var summary = document.querySelector('.data-status__summary');
    if (!list || !summary) {
      return;
    }
    list.textContent = '';

    var previewSeen = false;
    var staleSeen = false;
    var errorSeen = false;

    results.forEach(function (result) {
      var item = el('li', 'data-status__item');
      item.appendChild(el('span', 'data-status__name', result.label));

      if (!result.ok) {
        item.appendChild(el('span', 'data-status__state data-status__state--error', 'No disponible'));
        list.appendChild(item);
        errorSeen = true;
        return;
      }

      var data = result.data;
      var isPreview = data.status === 'preview';
      var stale = isStale(data.fetched_at);

      var stateText;
      var stateClass;
      if (isPreview) {
        stateText = 'Datos de muestra';
        stateClass = 'data-status__state--preview';
        previewSeen = true;
      } else if (stale) {
        stateText = 'Desactualizado';
        stateClass = 'data-status__state--stale';
        staleSeen = true;
      } else {
        stateText = 'En vivo';
        stateClass = 'data-status__state--live';
      }
      item.appendChild(el('span', 'data-status__state ' + stateClass, stateText));
      item.appendChild(el('span', 'data-status__source', data.source || ''));
      item.appendChild(el('span', 'data-status__time', 'actualizado: ' + formatTimestamp(data.fetched_at)));
      list.appendChild(item);
    });

    if (errorSeen) {
      summary.textContent = 'Algunos datos no están disponibles en este momento.';
    } else if (previewSeen) {
      summary.textContent = 'Mostrando datos de muestra: la recopilación en vivo está pendiente de configuración.';
    } else if (staleSeen) {
      summary.textContent = 'Algunos datos están desactualizados.';
    } else {
      summary.textContent = 'Todos los datos están disponibles.';
    }
  }

  function loadModule(name) {
    return fetch(DATA_PREFIX + name + '.json')
      .then(function (response) {
        if (!response.ok) {
          throw new Error('HTTP ' + response.status);
        }
        return response.json();
      })
      .then(function (data) {
        var render = RENDERERS[name];
        if (render) {
          render(data);
        }
        return { name: name, label: LABELS[name], ok: true, data: data };
      })
      .catch(function () {
        moduleNotice(name, 'Datos no disponibles en este momento.');
        return { name: name, label: LABELS[name], ok: false, data: null };
      });
  }

  function init() {
    var results = MODULES.map(loadModule);
    Promise.all(results).then(updateStatus);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
