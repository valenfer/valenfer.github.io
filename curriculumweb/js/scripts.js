document.addEventListener("DOMContentLoaded", function() {
  const flechas = document.querySelectorAll(".flecha");

  flechas.forEach(flecha => {
      flecha.addEventListener("click", function() {
          const retractil = this.closest(".apartado").querySelector(".retractil");
          const otrosRetractiles = document.querySelectorAll(".retractil");

          otrosRetractiles.forEach(div => {
              if (div !== retractil) {
                  div.style.display = "none";
              }
          });

          if (retractil.style.display === "none" || retractil.style.display === "") {
              retractil.style.display = "block";
          } else {
              retractil.style.display = "none";
          }
      });
  });
});