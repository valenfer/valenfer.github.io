const btnAnterior = document.getElementById('btnAnterior');
const btnSiguiente = document.getElementById('btnSiguiente');
const contenedor = document.getElementById('contenedor');
const apartado = document.getElementById('apartado');
const menu = document.getElementById('menu');

let pagina = 1;
let url;
let opt;
const API_KEY = '3651389ee509c17c04e3ceff1b766695';

btnSiguiente.addEventListener('click', () => {
    if (pagina < 1000) {
        pagina += 1;
    }
    if (pagina === 1000) {
        btnSiguiente.classList.add('botonApagado');
        btnSiguiente.disabled = true;
    }
    if (pagina > 1) {
        btnAnterior.classList.remove('botonApagado');
        btnAnterior.disabled = false;
    }
    opcionSeleccionada(opt)
});

btnAnterior.addEventListener('click', () => {
    if (pagina > 1) {
        pagina -= 1;
        
    }
    if (pagina === 1) {
        btnAnterior.classList.add('botonApagado');
        btnAnterior.disabled = true;
    }
    if (pagina < 1000) {
        btnSiguiente.classList.remove('botonApagado');
        btnSiguiente.disabled = false;
    }
    opcionSeleccionada(opt);
});


function detalle(id){
    menu.classList.add('ocultar');
    apartado.classList.add('ocultar');
	const detallePelicula  = async () => {
		try {
			const respuesta = await fetch(`https://api.themoviedb.org/3/movie/${id}?api_key=${API_KEY}&language=es-ES`);
			if (respuesta.status === 200) {
				const pelicula = await respuesta.json();
				// Selecciona el div con la clase 'contenedor'
				const contenedor = document.querySelector('.contenedor');

				// Reemplaza la clase 'contenedor' con 'detallePelicula'
				contenedor.classList.replace('contenedor', 'detallePelicula');

				document.getElementById('contenedor').innerHTML = `
						<h1>${pelicula.title}</h1>
						<div class="info">
							<img src="https://image.tmdb.org/t/p/w500/${pelicula.poster_path}">
							<div>
                            <p>Sinopsis</p>
                            <p>${pelicula.overview}</p>
                            <p>Adultos: ${pelicula.adult?"No":"Si"}</p>
                            <p>Título Original: ${pelicula.original_title}</p>
                            <p>Nota media: ${pelicula.vote_average}</p>
                            </div>
						</div>
						<a href="index.html" class="boton btnVolver" >Volver</a>
				`
				document.querySelector('.paginacion').style.display = 'none';
			} else {
				console.log('No se pudo obtener la información de la película');
			}

		} catch (error) {
			console.log(error);
		}

	}
	detallePelicula();
}

function opcionSeleccionada(opcion){
    if (opcion==="masPopulares"){
        url=`https://api.themoviedb.org/3/movie/popular?api_key=${API_KEY}&language=es-ES&page=${pagina}`;
        apartado.innerHTML="Películas mas populares";
        
    }else if (opcion==="enPantalla"){
        url=`https://api.themoviedb.org/3/movie/now_playing?api_key=${API_KEY}&language=es-ES&page=${pagina}`;
        apartado.innerHTML="Películas en pantalla";
    }else if(opcion==="mejorValoradas"){
        url=`https://api.themoviedb.org/3/movie/top_rated?api_key=${API_KEY}&language=es-ES&page=${pagina}`;
        apartado.innerHTML="Películas mejor valoradas";
    }else if (opcion==="proximosEstrenos"){
        url=`https://api.themoviedb.org/3/movie/upcoming?api_key=${API_KEY}&language=es-ES&page=${pagina}`;
        apartado.innerHTML="Próximos estrenos";
    }
    else console.log("Hay un error al seleccionar la opción");
    opt=opcion;
    obtenerPeliculas();
}


/*Populares*/
const obtenerPeliculas = async () => {
    try {
        const respuesta = await fetch(url);
        console.log(respuesta.url);
        if (respuesta.status === 200) {
            const datos = await respuesta.json();
            let peliculas = '';
            datos.results.forEach(pelicula => {
                peliculas += `
                    <div class="pelicula" id="${pelicula.id}">
                        <img class="poster" src="https://image.tmdb.org/t/p/w500/${pelicula.poster_path}">
                        <h3 class="titulo">${pelicula.title}</h3>
                    </div>
                `;
            });
            contenedor.innerHTML = peliculas;
            document.querySelectorAll('.pelicula').forEach(pelicula => {
                pelicula.addEventListener('click', () => {
                    detalle(pelicula.id);
                });
           });

        } else if (respuesta.status === 401) {
            console.log('KEY API Incorrecta');
        } else if (respuesta.status === 404) {
            console.log('La pelicula no existe');
        } else {
           console.log('Hubo un error');
        }

    } catch (error) {
        console.log(error);
    }
}
opcionSeleccionada("masPopulares");//Por defeco cartgamos las mas populares