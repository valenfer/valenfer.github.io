function ultimaActualizacion(){
    var lastUpdated = new Date(document.lastModified);

// Formatea la fecha a un formato legible
var formattedDate = lastUpdated.getDate() + "-" + (lastUpdated.getMonth()+1) + "-" + lastUpdated.getFullYear();
return formattedDate;
}

function myFunction() {
            var x = document.getElementById("myNavbar");
            if (x.className === "navbar") {
                x.className += " responsive";
            } else {
                x.className = "navbar";
            }
        }

function cargarContenido(pagina) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', pagina, true);
    xhr.onreadystatechange = function () {
        if (this.readyState !== 4) return;
        if (this.status !== 200) return; // or whatever error handling you want
        document.getElementById('contenido').innerHTML = this.responseText;
    };
    xhr.send();
}

function ultimaActualizacion(){
            var lastUpdated = new Date(document.lastModified);

            // Formatea la fecha a un formato legible
            var formattedDate = lastUpdated.getDate() + "-" + (lastUpdated.getMonth()+1) + "-" + lastUpdated.getFullYear();
            return formattedDate;
        }