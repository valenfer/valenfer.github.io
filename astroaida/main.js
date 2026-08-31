'use strict';

(function () {
  var DATA_PREFIX = 'data/';
  var MAX_AGE_HOURS = 48;
  var LOCATION_STORAGE_KEY = 'astroaida.location.v1';
  var DEFAULT_LOCATION = { label: 'Sevilla', latitude: 37.38283, longitude: -5.97317, elevation: 0, source: 'default' };

  var MODULES = ['launches', 'apod', 'sky-today', 'moon', 'star-chart', 'near-earth', 'ephemerides'];

  var LABELS = {
    launches: 'Lanzamientos',
    apod: 'Astronomía del día',
    'sky-today': 'Cielo hoy',
    moon: 'Luna',
    'star-chart': 'Carta celeste',
    'near-earth': 'Objetos cercanos',
    ephemerides: 'Efemérides'
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

  var BODY_NAMES_ES = {
    Sun: 'Sol', Moon: 'Luna', Mercury: 'Mercurio', Venus: 'Venus',
    Mars: 'Marte', Jupiter: 'Júpiter', Saturn: 'Saturno',
    Uranus: 'Urano', Neptune: 'Neptuno'
  };

  var CONSTELLATION_NAMES_ES = {
    Aries: 'Aries', Taurus: 'Tauro', Gemini: 'Géminis', Cancer: 'Cáncer',
    Leo: 'León', Virgo: 'Virgo', Libra: 'Libra', Scorpius: 'Escorpio',
    Sagittarius: 'Sagitario', Capricornus: 'Capricornio', Aquarius: 'Acuario',
    Pisces: 'Piscis', Orion: 'Orión', Ophiuchus: 'Ofiuco',
    'Ursa Mayor': 'Osa Mayor', 'Ursa Minor': 'Osa Menor',
    Cygnus: 'Cisne', Cassiopeia: 'Casiopea', Hercules: 'Hércules',
    Lyra: 'Lira', Andromeda: 'Andrómeda', Pegasus: 'Pegaso',
    Perseus: 'Perseo', Auriga: 'Auriga', Boötes: 'Boyeros',
    'Corona Borealis': 'Corona Boreal', Serpens: 'Serpiente',
    Delphinus: 'Delfín', 'Piscis Austrinus': 'Piscis Austral',
    Grus: 'Grulla', Phoenix: 'Fénix', Tucana: 'Tucán',
    Indus: 'Indio', Musca: 'Mosca', Carina: 'Quilla',
    Vela: 'Vela', Puppis: 'Popa', Lupus: 'Lobo', Ara: 'Ara',
    Triangulum: 'Triángulo', Cetus: 'Cetus', Eridanus: 'Eridano',
    Hydra: 'Hidra', Corvus: 'Cuervo', Crux: 'Cruz',
    'Canis Minor': 'Can Menor', 'Canis Major': 'Can Mayor',
    Monoceros: 'Monoceros', Columba: 'Paloma', Lepus: 'Liebre',
    Scutum: 'Escudo', Sagitta: 'Flecha', Equuleus: 'Equuleo',
    Horologium: 'Reloj', Reticulum: 'Reticulante', Octans: 'Octante',
    Chamaeleon: 'Camaleón', Volans: 'Volante', Sculptor: 'Escultor',
    Fornax: 'Horno', Caelum: 'Cincel', Pavo: 'Pavo'
  };

  function translateBodyName(name) {
    return BODY_NAMES_ES[name] || name;
  }

  function translateConstellation(name) {
    return CONSTELLATION_NAMES_ES[name] || name;
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
    return date.toLocaleString('es-ES', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Europe/Madrid' });
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

  function parseCoordinate(value, min, max) {
    var text = String(value === null || value === undefined ? '' : value).replace(',', '.').trim();
    if (text === '') { return null; }
    var parsed = Number(text);
    if (!isFinite(parsed) || parsed < min || parsed > max) {
      return null;
    }
    return parsed;
  }

  function loadStoredLocation() {
    try {
      var raw = window.localStorage && window.localStorage.getItem(LOCATION_STORAGE_KEY);
      if (!raw) { return DEFAULT_LOCATION; }
      var parsed = JSON.parse(raw);
      if (typeof parsed.latitude !== 'number' || typeof parsed.longitude !== 'number') {
        return DEFAULT_LOCATION;
      }
      return parsed;
    } catch (error) {
      return DEFAULT_LOCATION;
    }
  }

  function saveLocation(location) {
    try {
      window.localStorage.setItem(LOCATION_STORAGE_KEY, JSON.stringify(location));
    } catch (error) {
      // La geolocalización sigue siendo útil aunque el navegador bloquee localStorage.
    }
  }

  function clearLocation() {
    try {
      window.localStorage.removeItem(LOCATION_STORAGE_KEY);
    } catch (error) {}
    applyLocation(DEFAULT_LOCATION, 'Ubicación restablecida: Sevilla.');
  }

  function formatLocation(location) {
    var elevation = Number.isFinite(location.elevation) ? ' · ' + Math.round(location.elevation) + ' m' : '';
    return location.label + ' · ' + location.latitude.toFixed(5) + ', ' + location.longitude.toFixed(5) + elevation;
  }

  function applyLocation(location, message) {
    var titleSpan = document.querySelector('.site-header__title span');
    var observerLabel = document.querySelector('[data-role="observer-label"]');
    var status = document.querySelector('[data-role="location-status"]');
    if (titleSpan) { titleSpan.textContent = location.label; }
    if (observerLabel) { observerLabel.textContent = location.label; }
    if (status) {
      status.textContent = message || ('Ubicación actual: ' + formatLocation(location) + '.');
    }
  }

  function initLocationControls() {
    var panel = moduleContainer('location');
    if (!panel) { return; }
    var current = loadStoredLocation();
    applyLocation(current);

    var form = panel.querySelector('[data-role="location-form"]');
    if (form) {
      form.latitude.value = current.latitude;
      form.longitude.value = current.longitude;
      form.elevation.value = Number.isFinite(current.elevation) ? current.elevation : '';
      form.addEventListener('submit', function (event) {
        event.preventDefault();
        var latitude = parseCoordinate(form.latitude.value, -90, 90);
        var longitude = parseCoordinate(form.longitude.value, -180, 180);
        var elevation = parseCoordinate(form.elevation.value || '0', -500, 9000);
        form.latitude.setAttribute('aria-invalid', latitude === null ? 'true' : 'false');
        form.longitude.setAttribute('aria-invalid', longitude === null ? 'true' : 'false');
        form.elevation.setAttribute('aria-invalid', elevation === null ? 'true' : 'false');
        if (latitude === null || longitude === null || elevation === null) {
          applyLocation(loadStoredLocation(), 'Coordenadas no válidas. Latitud -90 a 90, longitud -180 a 180.');
          return;
        }
        form.latitude.setAttribute('aria-invalid', 'false');
        form.longitude.setAttribute('aria-invalid', 'false');
        form.elevation.setAttribute('aria-invalid', 'false');
        var manual = { label: 'Tu ubicación', latitude: latitude, longitude: longitude, elevation: elevation, source: 'manual' };
        saveLocation(manual);
        applyLocation(manual, 'Ubicación guardada en este navegador: ' + formatLocation(manual) + '.');
      });
    }

    var gpsButton = panel.querySelector('[data-action="gps"]');
    if (gpsButton) {
      gpsButton.addEventListener('click', function () {
        if (!navigator.geolocation) {
          applyLocation(loadStoredLocation(), 'Este navegador no permite geolocalización. Usa coordenadas manuales.');
          return;
        }
        gpsButton.disabled = true;
        applyLocation(loadStoredLocation(), 'Solicitando permiso GPS…');
        navigator.geolocation.getCurrentPosition(function (position) {
          var coords = position.coords;
          var location = {
            label: 'Tu ubicación',
            latitude: coords.latitude,
            longitude: coords.longitude,
            elevation: Number.isFinite(coords.altitude) ? coords.altitude : 0,
            accuracy: Number.isFinite(coords.accuracy) ? Math.round(coords.accuracy) : null,
            source: 'gps'
          };
          saveLocation(location);
          if (form) {
            form.latitude.value = location.latitude.toFixed(6);
            form.longitude.value = location.longitude.toFixed(6);
            form.elevation.value = Math.round(location.elevation);
          }
          var accuracy = location.accuracy ? ' Precisión aproximada: ±' + location.accuracy + ' m.' : '';
          applyLocation(location, 'GPS capturado y guardado localmente: ' + formatLocation(location) + '.' + accuracy);
          gpsButton.disabled = false;
        }, function (error) {
          var reasons = { 1: 'Permiso denegado.', 2: 'Ubicación no disponible.', 3: 'Tiempo de espera agotado.' };
          applyLocation(loadStoredLocation(), (reasons[error.code] || 'No se pudo capturar el GPS.') + ' Puedes introducir coordenadas manualmente.');
          gpsButton.disabled = false;
        }, { enableHighAccuracy: true, timeout: 12000, maximumAge: 300000 });
      });
    }

    var clearButton = panel.querySelector('[data-action="clear-location"]');
    if (clearButton) {
      clearButton.addEventListener('click', clearLocation);
    }
  }

  function isSafeHttpUrl(url) {
    return typeof url === 'string' && /^https:\/\//i.test(url);
  }

  function formatLaunchDate(iso) {
    if (!iso) { return 'Fecha pendiente'; }
    var date = new Date(iso);
    if (isNaN(date.getTime())) { return 'Fecha pendiente'; }
    return date.toLocaleString('es-ES', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Madrid' });
  }

  function formatCountdown(iso) {
    var date = new Date(iso);
    if (isNaN(date.getTime())) { return 'Cuenta atrás pendiente'; }
    var diff = date.getTime() - Date.now();
    if (diff <= 0) { return 'Ventana de lanzamiento abierta'; }
    var days = Math.floor(diff / 86400000);
    var hours = Math.floor((diff % 86400000) / 3600000);
    var minutes = Math.floor((diff % 3600000) / 60000);
    if (days > 0) { return 'T− ' + days + ' d ' + hours + ' h'; }
    return 'T− ' + hours + ' h ' + minutes + ' min';
  }

  function renderLaunches(data) {
    var container = moduleContainer('launches');
    container.textContent = '';
    if (!data.launches || !data.launches.length) {
      container.appendChild(el('p', 'module__notice', 'No hay lanzamientos próximos disponibles.'));
      return;
    }
    var list = el('div', 'launch-grid');
    data.launches.slice(0, 6).forEach(function (launch, index) {
      var card = el('article', 'launch-card' + (index === 0 ? ' launch-card--next' : ''));
      card.appendChild(el('p', 'launch-card__kicker', index === 0 ? 'Próximo lanzamiento' : (launch.agency || 'Evento espacial')));
      card.appendChild(el('h3', 'launch-card__title', launch.name || 'Lanzamiento espacial'));
      card.appendChild(el('p', 'launch-card__date', formatLaunchDate(launch.net)));
      card.appendChild(el('p', 'launch-card__countdown', formatCountdown(launch.net)));
      var facts = el('dl', 'launch-card__facts');
      addStat(facts, 'Agencia', launch.agency || '—');
      addStat(facts, 'Cohete', launch.rocket || '—');
      addStat(facts, 'Lugar', launch.location || launch.pad || '—');
      addStat(facts, 'Estado', launch.status || '—');
      card.appendChild(facts);
      if (launch.mission_description) {
        card.appendChild(el('p', 'launch-card__description', launch.mission_description));
      }
      if (isSafeHttpUrl(launch.webcast_url)) {
        var webcast = el('a', 'launch-card__link', 'Ver webcast');
        webcast.href = launch.webcast_url; webcast.target = '_blank'; webcast.rel = 'noopener noreferrer';
        card.appendChild(webcast);
      }
      if (isSafeHttpUrl(launch.url)) {
        var link = el('a', 'launch-card__link', 'Ficha del lanzamiento');
        link.href = launch.url; link.target = '_blank'; link.rel = 'noopener noreferrer';
        card.appendChild(link);
      }
      list.appendChild(card);
    });
    container.appendChild(list);
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
    var titleText = data.title_es || data.title || 'Imagen astronómica del día';
    var title = el('h3', 'apod__title', titleText);
    body.appendChild(title);

    var meta = el('p', 'apod__meta');
    if (data.date) {
      meta.appendChild(el('span', 'apod__date', formatTimestamp(data.date + 'T12:00:00')));
    }
    if (data.copyright) {
      meta.appendChild(el('span', 'apod__credit', '© ' + data.copyright));
    }
    body.appendChild(meta);

    var explanationText = data.explanation_es || data.explanation;
    if (explanationText) {
      body.appendChild(el('p', 'apod__explanation', explanationText));
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
      var bodyName = body.name_es || translateBodyName(body.name) || '—';
      var nameCell = el('th', null, bodyName);
      nameCell.setAttribute('scope', 'row');
      row.appendChild(nameCell);
      row.appendChild(el('td', null, formatAngle(body.altitude)));
      row.appendChild(el('td', null, formatAngle(body.azimuth)));
      var magnitude = (body.magnitude === undefined || body.magnitude === null || isNaN(body.magnitude))
        ? '—'
        : body.magnitude.toFixed(1);
      row.appendChild(el('td', null, magnitude));
      var constellation = body.constellation_es || translateConstellation(body.constellation) || '—';
      row.appendChild(el('td', null, constellation));
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

  function renderEphemerides(data) {
    var container = moduleContainer('ephemerides');
    container.textContent = '';

    if (!data.events || !data.events.length) {
      container.appendChild(el('p', 'module__notice', 'No hay efemérides registradas para esta fecha.'));
      return;
    }

    if (data.target_date) {
      var targetDate = new Date(data.target_date + 'T12:00:00');
      var formattedDate = isNaN(targetDate.getTime()) ? data.target_date :
        targetDate.toLocaleDateString('es-ES', { dateStyle: 'long' });
      container.appendChild(el('p', 'ephem__date', 'Fecha: ' + formattedDate));
    }

    if (data.observation_window && data.observation_window.start_local && data.observation_window.end_local) {
      var windowText = 'Ventana de observación (hora de Sevilla): ' +
        formatTimestamp(data.observation_window.start_local) + ' — ' +
        formatTimestamp(data.observation_window.end_local);
      container.appendChild(el('p', 'ephem__window', windowText));
    }

    var list = el('ul', 'ephem__list');
    data.events.forEach(function (event) {
      var card = el('li', 'ephem__card');

      var header = el('div', 'ephem__card-header');
      var eventTitle = event.title_es || event.title || '';
      if (event.title_translation_status === 'unavailable') {
        eventTitle += ' (título original en inglés)';
      }
      header.appendChild(el('span', 'ephem__card-title', eventTitle));
      if (event.start_local) {
        header.appendChild(el('span', 'ephem__card-time', formatTimestamp(event.start_local)));
      }
      card.appendChild(header);

      if (event.summary_es) {
        card.appendChild(el('p', 'ephem__card-summary', event.summary_es));
      }

      if (event.visibility) {
        var visClass = 'ephem__visibility ephem__visibility--' + (event.visibility.status || 'uncertain');
        card.appendChild(el('span', visClass, event.visibility.label || event.visibility.status || ''));
        if (event.visibility.reason) {
          card.appendChild(el('p', 'ephem__card-summary', event.visibility.reason));
        }
      }

      if (event.source && event.source.url && event.source.name) {
        var link = el('a', 'ephem__link', 'Fuente: ' + event.source.name);
        link.href = event.source.url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        card.appendChild(link);
      }

      list.appendChild(card);
    });
    container.appendChild(list);

    if (data.weather) {
      var weatherDiv = el('div', 'ephem__weather');
      weatherDiv.appendChild(el('h3', 'ephem__weather-title', 'Condiciones meteorológicas'));
      var wstats = el('dl', 'ephem__weather-stats');
      if (data.weather.cloud_cover !== undefined && data.weather.cloud_cover !== null) {
        addStat(wstats, 'Nubosidad', data.weather.cloud_cover + ' %');
      }
      if (data.weather.visibility !== undefined && data.weather.visibility !== null) {
        addStat(wstats, 'Visibilidad', formatNumber(data.weather.visibility) + ' m');
      }
      if (data.weather.precipitation_probability !== undefined && data.weather.precipitation_probability !== null) {
        addStat(wstats, 'Prob. precipitación', data.weather.precipitation_probability + ' %');
      }
      if (data.weather.temperature !== undefined && data.weather.temperature !== null) {
        addStat(wstats, 'Temperatura', data.weather.temperature + ' °C');
      }
      weatherDiv.appendChild(wstats);
      container.appendChild(weatherDiv);
    }

    if (data.sources && data.sources.length) {
      var sourcesList = el('ul', 'ephem__sources');
      data.sources.forEach(function (src) {
        var li = el('li');
        if (src.url) {
          var a = el('a');
          a.href = src.url;
          a.target = '_blank';
          a.rel = 'noopener noreferrer';
          a.textContent = src.name || src.url;
          li.appendChild(a);
        } else {
          li.textContent = src.name || '';
        }
        sourcesList.appendChild(li);
      });
      container.appendChild(sourcesList);
    }
  }

  var RENDERERS = {
    launches: renderLaunches,
    apod: renderApod,
    'sky-today': renderSkyToday,
    moon: renderMoon,
    'star-chart': renderStarChart,
    'near-earth': renderNearEarth,
    ephemerides: renderEphemerides
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
    initLocationControls();
    var results = MODULES.map(loadModule);
    Promise.all(results).then(updateStatus);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
