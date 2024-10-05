$(function() {
    const KEY='F9AYP67TXSZ5PS6LUHCZJY5QB';//>Guardamos la key de la API en una constante
    let  divcontenido = $("#contenido"); // Seleccionamos el div "contenido"
    let divsuperior = $("#superior"); // Seleccionamos el div "superior"

    let mensaje = $('<div>').attr('id', "mensaje");// Creamos el div para mensaje de inicio
    divcontenido.append(mensaje);
    $("#mensaje").html(`
            <h1> OPCIONES </h1>
            <h3> TIEMPO ACTUAL: Tiempo detallado del día de hoy en la ubicación introducida</h3>
            <h3> PROXIMOS 1O DIAS: Tiempo con temperaturas máximas y mínimas de los próximos 10 días en la ubicación introducida</h3>
            <h3> POSICION GPS: Tiempo con temperaturas máximas y mínimas de los próximos 10  y días detalle del dia actual de la ubicación por GPS</h3>
        `);


    /**
     * 
     * Con esta función dibujamos el contenido de la sección que tiene los datos detallas y el mapa
     * 
     */
    function dibujarContenido(datos){
        let icono=datos.days[0].icon;//Capturamos el icono sugeriodo por los datos recibidos
        let rutaIcono=`./icons/${icono}.svg`;//Generamos al ruta de acceso al icono correspondiente
        //Rellenamos los datos
        divcontenido.html(`
            <div id="datos">
                <p>${datos.days[0].datetime}</p>
                <img src="${rutaIcono}">
                <P><span>Probabilidad de precipitaciones: </span> ${datos.days[0].precipprob}  </p>
                <P><span>Tipo de precipitación: </span> ${datos.days[0].preciptype}  </p>
                <p><spam class="enunciado">Temperaturas:</spam> Máxima: ${datos.days[0].tempmax} - Mínima: ${datos.days[0].tempmin}</p>
                <p><spam class="enunciado">Viento:</spam> Velocidad: ${datos.days[0].windspeed} - Dirección: ${datos.days[0].winddir}</p>
                <p>${datos.days[0].description}</p>
                <p>
                <p><spam class="enunciado">Visibilidad:</spam> ${datos.days[0].visibility}</p>
                <p><spam class="enunciado">Latitud:</spam> ${datos.latitude}</p>
                <p><spam class="enunciado">Longitud:</spam> ${datos.longitude}</p>
            </div>
            <div id="mapa">
            </div>                                                                                        
        `);
        //Añadimos codigo necesario para generar mapa de openstreetmap
        let map=L.map('mapa').setView([datos.latitude,datos.longitude],12);//Iniciamos mapa con leaflet
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map); //Añadimos capas
    }

    /**
     * Esta función dibuja las tarjetas con los 10 días de la localización seleccionada
     * @param {*} datos Datos obtenidos de la consulta a la API 
     */
    function dibujarContenidoDias(datos){
        
        let fechas = intervaloFechas();// Obtenemos el array de fechas
        $.each(fechas, function(indice, fecha) {// Recorrer el array de fechas con jquery
            let icono=datos.days[indice].icon;
            let rutaIcono=`./icons/${icono}.svg`;
            let divFecha = $('<div>').addClass('dia').attr('id', indice);// Creamos el div para cada fecha asignándole una clase y un id
            divcontenido.append(divFecha);// Insertamos el div en el contenido
            $(`#${indice}`).html(`
                <img src="${rutaIcono}">
                <p><spam class="enunciado">${datos.days[indice].datetime}</p>
                <p><spam class="enunciado">T. Máx:</spam>${datos.days[indice].tempmax}</p> 
                <p><spam class="enunciado">T. Min:</spam>${datos.days[indice].tempmin}</p>
            `);
        });  
    }

    /**
     * Esta función genera un array con los 10 días siguientes desde la fecha actual en formato yyyy-mm-dd
     * @returns array con fechas de los próximos 10 días
     */
    //Intevalo de fechas
    function intervaloFechas(){
        let fechaActual = new Date();// Obtenemos la fecha actual
        let fechas = [];// Crear un array para almacenar las fechas
        fechas.push(fechaActual.toISOString().substring(0, 10)); // Agregamos la fecha actual al array
        for (let i = 1; i <= 9; i++) {// Generar las fechas para los siguientes 9 días
            let fechaSiguiente = new Date(fechaActual.getTime() + i * 24 * 60 * 60 * 1000);//Calculamos el día siguiente
            fechas.push(fechaSiguiente.toISOString().substring(0, 10));//Lo fomateamos yyy-mm-dd y lo guardamos en el array
        }
        return fechas;
    }
     /**
     * Función para extraer los datos de la localidad indicada en el campo de texto en la fecha actual
     * Realizado con FETCH
     * 
     */
    function posicionGPS() {
        limpiar();
        let fechas=intervaloFechas();
        if (navigator.geolocation) {//S el navegador soporta geolocalización
            divsuperior.html("<img src='balls64.gif'>");//Cargamos gif para ajax
            navigator.geolocation.getCurrentPosition(posicion => {//Capturamos la geolocalización
                let latitud =  posicion.coords.latitude;//Latitud
                let longitud = posicion.coords.longitude;  //Longitud
                //Reralizamos la consulta a la API para el dia actual de la localizacion GPS
                let url=`https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/${latitud}%2C%20${longitud}/${fechas[0]}/${fechas[0]}?unitGroup=metric&elements=datetime%2Cname%2Caddress%2CresolvedAddress%2Clatitude%2Clongitude%2Ctempmax%2Ctempmin%2Ctemp%2Cprecip%2Cprecipprob%2Cpreciptype%2Cwindspeed%2Cwinddir%2Cvisibility%2Cconditions%2Cdescription%2Cicon&include=statsfcst%2Cobs%2Cstats%2Cremote%2Cevents%2Cdays%2Chours%2Calerts%2Ccurrent%2Cfcst&key=${KEY}&options=stnslevel1&contentType=json&degreeDayTempBase=-1&lang=es`
                fetch(url)
                .then((resultado) => resultado.json())
                .then((datos)=>{//Procesamos los datos del JSON obtenido tras la consulta
                    //Visualizamos el contenido del div superior con la longitud y la latitud
                    divsuperior.html(`
                        <div><spam class="enunciado">Longitud</spam><br>${longitud}</div>
                        <div><spam class="enunciado">Latitud</spam><br>${latitud}</div>        
                    `);
                    dibujarContenido(datos);//Visualizamos los datos en el div del contenido principal
                })
                .catch(err => {
                    console.error(err);
                });
                //Reralizamos la consulta a la API para los 10 dias de la localizacion GPS
                let fechaInicio=fechas[0];
                let fechaFin=fechas[fechas.length-1];
                url=`https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/${latitud}%2C%20${longitud}/${fechaInicio}/${fechaFin}?unitGroup=metric&elements=datetime%2Cname%2Caddress%2CresolvedAddress%2Clatitude%2Clongitude%2Ctempmax%2Ctempmin%2Ctemp%2Cprecip%2Cprecipprob%2Cpreciptype%2Cwindspeed%2Cwinddir%2Cvisibility%2Cconditions%2Cdescription%2Cicon&include=statsfcst%2Cobs%2Cstats%2Cremote%2Cevents%2Cdays%2Chours%2Calerts%2Ccurrent%2Cfcst&key=${KEY}&options=stnslevel1&contentType=json&degreeDayTempBase=-1&lang=es`
                fetch(url)
                .then((resultado) => resultado.json())
                .then((datos)=>{//Procesamos los datos del JSON obtenido tras la consulta
                    $.each(fechas, function(indice, fecha) {// Recorrer el array de fechas con jquery
                        let icono=datos.days[indice].icon;
                        let rutaIcono=`./icons/${icono}.svg`;
                        let divFecha = $('<div>').addClass('dia').attr('id', indice);// Creamos el div para cada fecha asignándole una clase y un id
                        $("#inferior").append(divFecha);// Insertamos el div en el contenido
                        $(`#${indice}`).html(`
                            <img src="${rutaIcono}">
                            <p><spam class="enunciado">${datos.days[indice].datetime}</p>
                            <p><spam class="enunciado">T. Máx:</spam>${datos.days[indice].tempmax}</p> 
                            <p><spam class="enunciado">T. Min:</spam>${datos.days[indice].tempmin}</p>
                        `);
                    });  
                })
                .catch(err => {
                    console.error(err);
                });

            });
        } else {
            divsuperior.html("Su navegador no soporta la API de geolocalización.");
            divsuperior.css('color','red');
            divcontenido.html(``);
        }
    }

    /**
     * Función para extraer los datos de la localidad indicada en el campo de texto en la fecha actual
     * Realizado con ASYNC AWAIT
     */

    async function tiempoActual() {
        limpiar();
        let localidad = $("#localidad").val(); // Obtenemos el valor del input
        let fechas=intervaloFechas();
        if (localidad.trim() !== "") {// Si el input no está vacío
            if (!localidad.endsWith(",es"))  localidad = localidad + ",es";//Si no se especifica que pedimos ciudad de España, lo resolvemos
            divsuperior.html("<img src='balls64.gif'>");//Gif animado 
            try{
            let respuesta= await fetch(`https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/${localidad}/${fechas[0]}/${fechas[0]}?unitGroup=metric&elements=datetime%2Cname%2Caddress%2CresolvedAddress%2Clatitude%2Clongitude%2Ctempmax%2Ctempmin%2Ctemp%2Cprecip%2Cprecipprob%2Cpreciptype%2Cwindspeed%2Cwinddir%2Cvisibility%2Cconditions%2Cdescription%2Cicon%2Csource&include=statsfcst%2Cobs%2Cstats%2Cremote%2Cevents%2Cdays%2Chours%2Calerts%2Ccurrent%2Cfcst&key=${KEY}&options=stnslevel1&contentType=json&degreeDayTempBase=-1&lang=es`);
            let datos=await respuesta.json();
            let zonas=datos["resolvedAddress"].split(",");//Extraemos los datos de pais, población y región
            divsuperior.css('color','black');//Cambiamos css desde jquery
            divsuperior.html(`
                <div><spam class="enunciado">Población</spam><br>${zonas[0]}</div>
                <div><spam class="enunciado">País</spam><br>${zonas[2]}</div>
                <div><spam class="enunciado">Región</spam><br>${zonas[1]}</div>        
            `);
            dibujarContenido(datos);
            }catch(error){
                divsuperior.html('<h1>Error: No se han obtenido datos de la API</h1>');
                divsuperior.css('color','red');
                divcontenido.html(``);
                console.log(error);
            }
        } else {
            {// Si el input está vacío
                divsuperior.html('<h1>Error: La localidad no puede estar vacia</h1>');
                divsuperior.css('color','red');
                divcontenido.html(``);
            }
        }
    }

    
     //Creamos la función para los próximos 10 días de la localización seleccionada,
    
    function proximos(){
        limpiar();
        let fechas=intervaloFechas();
        let fechaInicio=fechas[0];
        let fechaFin=fechas[fechas.length-1];
        let localidad = $("#localidad").val(); // Obtenemos el valor del input
        if (localidad.trim() !== "") {// Si el input no está vacío
            if (!localidad.endsWith(",es"))  localidad = localidad + ",es";//Si no se especifica que pedimos ciudad de España, lo resolvemos
            $.ajax({
                url: `https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/${localidad}/${fechaInicio}/${fechaFin}?unitGroup=metric&key=${KEY}&contentType=json&lang=es`, 
                method: 'GET', 
                data: {
                  // Request parameters go here
                  // e.g., { appid: 'YOUR_API_KEY', q: 'London' }
                },
                success: function(response) {
                    dibujarContenidoDias(response);   
                },
                error: function(error) {
                  console.error("Error:", error);
                }
              });
        } else {
            {// Si el input está vacío
                divsuperior.html('<h1>Error: La localidad no puede estar vacia</h1>');
                divsuperior.css('color','red');
                divcontenido.html(``);
            }
        }
       
    }
    
    // Evento click para el botón "Tiempo actual"
    $("#actual").click(tiempoActual);
    
    // Evento click para el botón "posicion" 
    $("#posicion").click(posicionGPS);

    // Evento click para el botón "proximos 10 días" 
    $("#proximos").click(proximos);

    //Funcion para limpiar todos los divs cada vez que se pulsa un botón
    function limpiar(){
        $('#superior').html('');
        $('#contenido').html('');
        $('#inferior').html('');
    }
});



  