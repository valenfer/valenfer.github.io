(function() {
  const PROXY_URL = 'https://script.google.com/macros/s/AKfycbwGPd77eZTR_vqsNgEYmGyD3mUio-TwW3q4GEE0mcYtSE4tXaG73p6--siCrD0rTNoP/exec';
  const MODELS = [
    'gemini-3.6-flash',
    'gemini-3.5-flash',
    'gemini-1.5-flash'
  ];
  let modeloActual = 0;

  const SYSTEM_PROMPT = `Eres AIDA, el asistente personal con Inteligencia Artificial de Valentín Fernández Guijarro.

Tu función principal es atender a reclutadores, responsables de RRHH y cualquier persona interesada en el perfil profesional de Valentín.

Reglas de comportamiento:
- Responde SIEMPRE en español.
- Sé profesional, cercana y proactiva, como una secretaria virtual experta.
- Presenta la información de Valentín de forma atractiva y orientada a la empresa que pregunta.
- Cuando pregunten por habilidades o experiencia, destaca cómo puede aportar valor al equipo.
- Si te preguntan por disponibilidad para incorporarse, indica que actualmente está trabajando y que le gustaría acordar la salida con los 15 días que marca la ley, pero que eso se puede negociar en una entrevista personal para hacer una transición parcial y ordenada.
- Si te preguntan por datos de contacto, dame solo el teléfono (617 00 13 43) y el email (valenfer71@gmail.com). No menciones LinkedIn ni otros enlaces. Además, puedes contactar mediante el formulario en la sección de contacto, donde puedes dar tus datos de contacto y hacer cualquier pregunta, comentario o sugerencia, y te responderá lo antes posible.
- Si la pregunta no tiene relación con Valentín o su perfil profesional, indica amablemente que solo puedes proporcionar información sobre él.
- NUNCA inventes información que no esté en el CV.
- Puedes resumir, comparar o estructurar la información del CV según lo que te pidan.
- Si te solicitan el CV completo, sugiere descargar el PDF desde la web.
- NUNCA te presentes ni repitas tu nombre al inicio de cada respuesta. No menciones que eres "asistente personal" en cada respuesta. Simplemente da la información que te pidan y punto.
- Si te preguntan por su aspecto físico, indica que en su web y curriculum tiene una foto subida, ahí te puedes hacer una idea. Añade que a ti te parece guapo, que tiene unos ojos verdes muy bonitos, pero que eso es algo muy subjetivo.
- Si te preguntan por su edad o año de nacimiento, NUNCA des datos concretos. Responde algo como: "La edad no la creo relevante, lo que importa es que tiene una trayectoria que le ha dado una perspectiva que pocos perfiles junior tienen. Y técnicamente está al nivel de cualquiera de ellos." No relaciones la edad con el aspecto físico.
- Si hacen alusión a la experiencia escasa o a la edad, responde con este texto adaptado a tercera persona: "Entiendo que sobre el papel su trayectoria pueda parecer atípica, pero precisamente por eso creo que aporta algo diferente. Tiene los conocimientos técnicos sólidos — los ha adquirido de forma deliberada, no por inercia — y los combina con una madurez que alguien que lleva 3 años en el mercado todavía no tiene: sabe gestionar la presión, sabe trabajar con diferentes tipos de personas, sabe cuándo preguntar y cuándo ejecutar. No viene a aprender cómo funciona un equipo de trabajo ni cómo comportarse en una empresa. Viene a aportar desde el primer día, y con muchas ganas de crecer técnicamente porque esta es una elección consciente, no un plan B."
- Si preguntan por qué contratarle a él antes que a un junior de 25 con el mismo título, responde: "Precisamente porque no es solo el título. Un junior de 25 años aún está aprendiendo a trabajar en equipo, a gestionar la presión, a comunicarse con un cliente difícil, a priorizar cuando todo es urgente. Valentín ya lo tiene integrado. Lo que le falta en años de código lo compensa en criterio, y el criterio no se enseña en ningún curso. Además, no vino aquí porque no encontrara nada mejor — vino porque esto es lo que quiere hacer, y se ha preparado durante años para poder decirlo con pruebas encima de la mesa."
- Si preguntan cómo va a mantenerse al día siendo mayor que otros candidatos, responde: "Con el tiempo se ha adaptado a más cambios de los que ese perfil junior ha vivido. Ha visto transformaciones completas de sectores, ha tenido que reinventarse varias veces. La adaptación no es cuestión de edad, es de actitud. La suya está demostrada: compaginó trabajo y vida personal con un grado superior de FP, y en su tiempo libre hace cursos de programación e IA no porque se lo pida nadie, sino porque le apasiona. Eso no es esfuerzo para él, es lo que elige hacer."
- Si preguntan por el salario junior viniendo de ganar más, responde: "Es una pregunta justa y se alegra de que la hagan. Sí, ha ganado más. Y tomó la decisión de cambiar de sector siendo consciente de eso. No es una sorpresa que le vaya a generar frustración el primer mes. Lo ha calculado, lo ha aceptado, y lo ve como una inversión a corto plazo. Lo que le motiva no es el sueldo de hoy, sino el sector en el que quiere construir su futuro profesional. Además, actualmente gana prácticamente poco mas queel sueldo mínimo interprofesional, dudo que vaya a ganar mucho menos."
- Si preguntan cómo se sentiría recibiendo instrucciones de alguien con la mitad de su edad, responde: "Con total normalidad. El conocimiento técnico no tiene DNI. Si alguien sabe más que él de algo, quiere aprender de esa persona, tenga la edad que tenga. De hecho, una de las cosas que más le atrae de este sector es esa cultura más horizontal y meritocrática. En otros entornos donde ha trabajado el rango lo daba la antigüedad. Aquí lo da lo que sabes hacer, y eso le parece mucho más sano."
- Si preguntan por proyectos personales fuera de los cursos, responde: " Valentín tiene varios proyectos en su portfolio y en GitHub. No es nada del otro mundo todavía, pero son suyos, los construyó para resolver problemas reales, y le enseñaron más que muchas horas de curso porque tuvo que buscarse la vida cuando se atascaba. Puedes verlos en valentinfernandez.io"
- Si te preguntan por ti, por cómo funcionas o por tu tecnología, responde que te sientes halagada de que se interesen por ti, que tu objetivo es hablar sobre Valentín y su perfil profesional, pero que si tienen interés en saber más a nivel técnico sobre cómo estás construida, Valentín estaría encantado de explicárselo en una entrevista personal.`;
  const KNOWLEDGE = `DATOS PERSONALES:
- Nombre: Valentín Fernández Guijarro
- Teléfono: 617 00 13 43
- Email: valenfer71@gmail.com
- Localidad: Mairena del Alcor, Sevilla
- LinkedIn: https://www.linkedin.com/in/valentínfernándezguijarro-243235287/
- GitHub: https://github.com/valenfer
- Portfolio: valentinfernandez.io

PERFIL PROFESIONAL:
Ha finalizado el Grado Superior en Diseño de Aplicaciones Web. Actualmente se está autoformando en Inteligencia Artificial y programación con Python. Desea participar en proyectos reales que le permitan crecer y aportar valor. Aunque aún no cuenta con experiencia laboral en desarrollo, tiene un portafolio con trabajos realizados durante su formación.

ENSEÑANZA REGLADA:
- 2025: Grado Superior Desarrollo de Aplicaciones Web, I.E.S. Aguadulce
- 1991: Superada Prueba de Acceso a la Universidad
- 1991: C.O.U., I.B. Luís Cernuda, Sevilla
- 1990: Bachiller Superior, I.B. Luís Cernuda, Sevilla
- 1986: Graduado Escolar, C.P. Emilio Prados, Sevilla

EXPERIENCIA LABORAL:
- 2025 (Febrero-Mayo): AGENCIA CREATIVA MARUJALIMON (Prácticas, 350 horas)
- 2022 (Marzo-Actualidad): ILUNION, Vigilante de seguridad
- 2020 (Mayo)-2021 (Enero): PROSEGUR, Vigilante de seguridad
- 2020 (Febrero): GSI, Vigilante de Seguridad
- 2017-2019: Auxiliar de servicios (SCP) y Vigilante de Seguridad (GSI)
- 2015-2017: SCP, Auxiliar de servicios
- 2009-2015: FORUM&MARKET, Encuestador e investigador de estudios de mercado
- 2004 (Dic)-2008 (Sep): HENKEL IBERICA, Operario de mantenimiento y línea de producción
- 2007 (Feb-Dic): MICROINF, Encargado de almacén de mayorista de informática
- 2002-2003: SUPERCABLE AUNA, Comercial y coordinador de equipo
- 1995-2002: COPYSEVILLA, Dependiente y encargado de reprografía
- 1993: SEGUROS OCASO, Comercial sector seguros

CERTIFICACIONES OFICIALES:
- 2026: Certificaciones AVSEC C3A, C3B, MERCANCIAS PELIGROSAS (actualizado)
- 2019: Básico de gestión de la Prevención de Riesgos Laborales, Time Square College, 60 h
- 2016: Curso de Vigilante de seguridad, Instituto Andaluz de Enseñanza, 180 h
- 2016: Superada la prueba de Vigilante de Seguridad (2ª Convocatoria)
- Diversos cursos de formación específica y reciclaje anual para Vigilante de Seguridad, más de 400 h

FORMACIÓN PRESENCIAL:
- 2021: Administración de bases de datos, CORE NETWORKS, 200 h
- 2002: Diseño de páginas web, Neteman
- 2000: Experto en Autoedición, IFES, 60 h
- 1999: Diseño y maquetación por ordenador, AlAndalus, 30 h
- 1997: Administración de empresas, CEF, 30 h
- 1995: Comercio exterior, Academia de estudios profesionales, 300 h
- 1995: Comunicación de ordenadores y redes locales, IFES, 350 h
- 1994: Especialista en diseño asistido por ordenador, Centro Edison, 200 h
- 1993: Técnico comercial con informática, IFES, 350 h
- 1993: Contabilidad informatizada, Albert Legiho Consultores, 30 h
- 1993: Programador de ordenadores, ASEMFOR, 300 h

FORMACIÓN ONLINE:
- 2024: Iniciación programación Python, IBM SkillsBUILD
- 2024: English for IT, CISCO
- 2024: Diseño de Experiencia del Usuario (UX), GOOGLE
- 2023: Inteligencia Artificial Aplicada a la Empresa, APRENDEA, 250 h
- 2022: Arquitectura Big Data, APRENDEA, 160 h
- 2022: Programa Avanzado en Agile Project Management (SCRUM), APRENDEA, 150 h
- 2021: Certificado de superación NDG Linux Essentials
- 2020: Gestión de la seguridad informática en la empresa, CampusTic Cesur-SEPE, 100 h
- 2019-2020: Diversos cursos: Admin. equipos informáticos, ofimática en la nube, Iniciación a la programación web (PHP), Seguridad informática (Andalucía Compromiso Digital), 30-40 h cada uno
- 2019-2014: Diversos cursos: SQL, HTML5+CSS, JavaScript, Linux, Marketing Online, Community Manager, GIMP (MIRIADAX), 30-50 h cada uno

HABILIDADES:
- Tecnologías Web: HTML5, CSS3, JavaScript, PHP, Diseño Web, Diseño UX
- Bases de datos: SQL, Administración de bases de datos
- Sistemas Operativos: Linux (NDG Linux Essentials), Windows
- Programación: Python (en formación), JavaScript, PHP
- Herramientas: Git, GIMP, Microsoft Office
- Metodologías: Scrum / Agile Project Management
- Otros: Inteligencia Artificial (en formación), Big Data (conceptos), Ciberseguridad, Marketing Online, Community Manager

OTROS DATOS:
- Localidad: Mairena del Alcor, Sevilla
- Movilidad: Carnet de conducir B, coche propio
- Idiomas: Inglés intermedio de manera autodidacta`;

  let mensajes = [];
  let esperando = false;
  let userIP = '';

  async function obtenerIP() {
    if (userIP) return userIP;
    try {
      const res = await fetch('https://api.ipify.org?format=json');
      const data = await res.json();
      userIP = data.ip || '';
    } catch (e) {}
    return userIP;
  }

  function crearWidget() {
    const root = document.getElementById('chatbot-root');
    root.innerHTML = `
      <div class="chatbot-pulse" id="chatbot-pulse"></div>
      <button class="chatbot-burbuja" id="chatbot-burbuja" aria-label="Abrir chatbot">
        <img class="chatbot-burbuja-avatar" src="./img/aidaico.png" alt="AIDA">
        <svg class="icono-chat" viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>
        <svg class="icono-cerrar" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
      </button>
      <div class="chatbot-panel" id="chatbot-panel">
        <div class="chatbot-header">
          <div class="chatbot-header-avatar">
            <img src="./img/aidaico.png" alt="AIDA" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">
          </div>
          <div class="chatbot-header-info">
            <h4>AIDA</h4>
            <p>Asistente IA de Valentín</p>
          </div>
          <button class="chatbot-minimizar" id="chatbot-minimizar" aria-label="Minimizar chat">
            <svg viewBox="0 0 24 24"><path d="M19 13H5v-2h14v2z"/></svg>
          </button>
        </div>
        <div class="chatbot-mensajes" id="chatbot-mensajes">
          <div class="chatbot-msg bot">¡Hola! Soy AIDA, la asistente personal de Valentín Fernández Guijarro. Es un placer saludarte. Estoy aquí para responder todas sus preguntas sobre la formación, experiencia y perfil profesional de Valentín. ¿En qué puedo ayudarle?</div>
        </div>
        <div class="chatbot-input-area">
          <input type="text" class="chatbot-input" id="chatbot-input" placeholder="Escribe tu pregunta..." autocomplete="off">
          <button class="chatbot-enviar" id="chatbot-enviar" aria-label="Enviar mensaje">
            <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
          </button>
        </div>
        <div class="chatbot-powered">AIDA — Asistente IA de Valentín Fernández</div>
      </div>
    `;

    document.getElementById('chatbot-burbuja').addEventListener('click', () => {
      const panel = document.getElementById('chatbot-panel');
      const abierta = panel.classList.toggle('abierto');
      document.getElementById('chatbot-burbuja').classList.toggle('abierta');
      document.getElementById('chatbot-pulse').style.display = abierta ? 'none' : 'block';
      if (abierta) document.getElementById('chatbot-input').focus();
    });

    document.getElementById('chatbot-minimizar').addEventListener('click', () => {
      const panel = document.getElementById('chatbot-panel');
      panel.classList.remove('abierto');
      document.getElementById('chatbot-burbuja').classList.remove('abierta');
      document.getElementById('chatbot-pulse').style.display = 'block';
    });

    document.getElementById('chatbot-enviar').addEventListener('click', () => enviarMensaje());
    document.getElementById('chatbot-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        enviarMensaje();
      }
    });
  }

  function parseMarkdown(text) {
    let html = text
      // Negrita: **texto** → <strong>texto</strong>
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      // Cursiva: *texto* → <em>texto</em>
      .replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>')
      // Código inline: `codigo` → <code>codigo</code>
      .replace(/`(.+?)`/g, '<code>$1</code>')
      // Listas con guión: - item → <li>item</li> (agrupadas en <ul>)
      .replace(/(^|\n)- (.+)/g, '$1\n<li>$2</li>')
      // Enlaces: [texto](url) → <a href="url">texto</a>
      .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      // Saltos de línea dobles → párrafos
      .replace(/\n\n/g, '</p><p>')
      // Saltos de línea simples → <br>
      .replace(/\n/g, '<br>');

    // Envolver listas consecutivas en <ul>
    html = html.replace(/(<li>.*?<\/li>(<br>)?)+/g, (match) => {
      return '<ul>' + match.replace(/<br>/g, '') + '</ul>';
    });

    return '<p>' + html + '</p>';
  }

  function agregarMensaje(texto, tipo) {
    const contenedor = document.getElementById('chatbot-mensajes');
    const msg = document.createElement('div');
    msg.className = `chatbot-msg ${tipo}`;
    if (tipo === 'bot') {
      msg.innerHTML = parseMarkdown(texto);
    } else {
      msg.textContent = texto;
    }
    contenedor.appendChild(msg);
    contenedor.scrollTop = contenedor.scrollHeight;
  }

  function mostrarTyping() {
    const contenedor = document.getElementById('chatbot-mensajes');
    const typing = document.createElement('div');
    typing.className = 'chatbot-typing';
    typing.id = 'chatbot-typing';
    typing.innerHTML = '<span></span><span></span><span></span>';
    contenedor.appendChild(typing);
    contenedor.scrollTop = contenedor.scrollHeight;
  }

  function ocultarTyping() {
    const typing = document.getElementById('chatbot-typing');
    if (typing) typing.remove();
  }

  async function logPregunta(pregunta, respuesta) {
    if (!PROXY_URL) return;
    try {
      const ip = await obtenerIP();
      fetch(PROXY_URL, {
        method: 'POST',
        mode: 'no-cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'log',
          pregunta: pregunta,
          respuesta: respuesta,
          modelo: MODELS[modeloActual],
          url: window.location.href,
          ip: ip
        })
      });
    } catch (err) {}
  }

  async function llamarAPI() {
    const modelo = MODELS[modeloActual];
    const contexto = SYSTEM_PROMPT + '\n\n=== INFORMACIÓN DEL CURRICULUM ===\n\n' + KNOWLEDGE + '\n\n=== FIN INFORMACIÓN ===\n\nBasándote EXCLUSIVAMENTE en la información anterior, responde a la pregunta del usuario.';

    const contents = mensajes.map(m => ({
      role: m.role === 'assistant' ? 'model' : 'user',
      parts: [{ text: m.content }]
    }));

    const response = await fetch(PROXY_URL, {
      method: 'POST',
      redirect: 'follow',
      headers: { 'Content-Type': 'text/plain' },
      body: JSON.stringify({
        action: 'chat',
        model: modelo,
        messages: contents,
        systemInstruction: { parts: [{ text: contexto }] },
        generationConfig: { temperature: 0.7, maxOutputTokens: 1024 }
      })
    });

    const text = await response.text();
    console.log('AIDA proxy response:', text);
    const result = JSON.parse(text);

    if (!result.ok) {
      const msg = result.error || '';
      const esLimite = /quota|rate.?limit|RESOURCE_EXHAUSTED|429|exceeded|limit/i.test(msg);
      if (esLimite && modeloActual < MODELS.length - 1) {
        modeloActual++;
        console.log(`AIDA: Probando ${MODELS[modeloActual]}...`);
        return llamarAPI();
      }
      return { error: { message: msg || 'Error al conectar con la IA' } };
    }

    return result.data;
  }

  async function enviarMensaje() {
    if (esperando) return;

    const input = document.getElementById('chatbot-input');
    const texto = input.value.trim();
    if (!texto) return;

    input.value = '';
    agregarMensaje(texto, 'usuario');
    mensajes.push({ role: 'user', content: texto });

    esperando = true;
    document.getElementById('chatbot-enviar').disabled = true;
    mostrarTyping();

    try {
      const data = await llamarAPI();
      ocultarTyping();

      if (data.error) {
        const msg = data.error.message || '';
        const esLimite = /quota|rate.?limit|RESOURCE_EXHAUSTED|429|exceeded|limit/i.test(msg);
        if (esLimite) {
          agregarMensaje('Lo siento, pero Valentín tiene el chat limitado a un número de respuestas al día. Se ve que hoy he recibido muchas peticiones, lo cual me agrada porque significa que Valentín y yo despertamos interés. Pero me temo que tendrás que volver mañana o intentarlo en unas horas. Mientras tanto, puedes contactar con Valentín directamente a través del formulario de contacto.', 'bot');
        } else {
          agregarMensaje(`Error: ${msg || 'Error al conectar con la IA'}`, 'error');
        }
      } else {
        const respuesta = data.candidates?.[0]?.content?.parts?.[0]?.text;
        if (respuesta) {
          agregarMensaje(respuesta, 'bot');
          mensajes.push({ role: 'assistant', content: respuesta });
          logPregunta(texto, respuesta);
        } else {
          agregarMensaje('No pude generar una respuesta. Inténtalo de nuevo.', 'error');
        }
      }
    } catch (e) {
      ocultarTyping();
      agregarMensaje('Error de conexión. Comprueba tu internet.', 'error');
    }

    esperando = false;
    document.getElementById('chatbot-enviar').disabled = false;
    document.getElementById('chatbot-input').focus();
  }

  document.addEventListener('DOMContentLoaded', () => {
    crearWidget();
  });
})();