/*Función para mostrar el menú responsivo*/
function responsiveMenu(){
    var x=document.getElementById("nav");
    if(x.className===""){
        x.className="responsive";
    }else{
        x.className="";
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
    var x=document.getElementById("nav");
    x.className="";
}

