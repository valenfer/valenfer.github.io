window.addEventListener('load', obtenerDatos);

function obtenerDatos() {
    const APIKEY = "9BShQca9kJaLbuY1Cx2DPqTUeRnOPdVU7ySnidGN";
    const ruta = `https://api.nasa.gov/planetary/apod?api_key=${APIKEY}`;

    fetch(ruta)
        .then(respuesta => respuesta.json())
        .then(resultado => mostarDatos(resultado))
}

function mostarDatos({ date, explanation, media_type, title, url }) {
    let titulo = document.querySelector('#title');
    let fecha = document.querySelector('#date');
    let description = document.querySelector('#description');
    let multimedia = document.querySelector('#multimedia');

    titulo.innerHTML = title;
    fecha.innerHTML = date;
    /* */
    let text = explanation;
    let index = 0;
    typeEffect();


    if (media_type == "video") {
        multimedia.innerHTML = `<iframe class="embed-responsive-item" src="${url}"></iframe>`;
    } else {
        multimedia.innerHTML = `<img src="${url}" class="img-fluid" alt="${url}">`;
    }

    function typeEffect() {
        description.textContent = text.slice(0, index++);
        if (index <= text.length) {
            setTimeout(typeEffect, 10); 
        }
    }
}

