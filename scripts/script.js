/*Función para mostrar el menú responsivo*/
function responsiveMenu(){
    var menu=document.getElementById("nav");
    if(menu.className===""){
        menu.className="responsive";
    }else{
        menu.className="";
    } 
}

/*Función para  modificar los estilos a las opciones de menú seleccionadas*/
function seleccionar(link){
    var opciones=document.querySelectorAll('#links a');
    opciones[0].className="";
    opciones[1].className="";
    opciones[2].className="";
    opciones[3].className="";
    opciones[4].className="";

    link.className="seleccionado";
    //Hacemos desaparecer el menu una vez seleccionada una opción en el menú responsivo
    var menu=document.getElementById("nav");
    menu.className="";
}

function ultimaActualizacion(){
    var lastUpdated = new Date(document.lastModified);

    // Formatea la fecha a un formato legible
    var formattedDate = lastUpdated.getDate() + "-" + (lastUpdated.getMonth()+1) + "-" + lastUpdated.getFullYear();
    return formattedDate;
}

