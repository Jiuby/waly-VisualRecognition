// static/mazer/assets/js/camara.js
// Flujo unificado: entrada vs salida según data-mode en <div class="page-heading" data-mode="entrada|salida">

document.addEventListener("DOMContentLoaded", async () => {
  const videoEl    = document.getElementById("video");
  const statusBox  = document.getElementById("status-container");
  const statusSpan = document.getElementById("registro-status");
  const headingDiv = document.querySelector(".page-heading");
  const mode       = headingDiv?.dataset.mode || "entrada";
  const enterText  = mode === "entrada"
                     ? "ENTER para verificar"
                     : "ENTER para registrar salida";
  const successMsg = mode === "entrada"
                     ? name => `Bienvenido: ${name} — Usuario registrado`
                     : name => `Hasta luego: ${name} — Salida registrada`;

  // Helper: actualizar recuadro de estado
  function update(type, msg) {
    statusBox.className = `alert alert-${type} text-center mt-3`;
    statusSpan.textContent = msg;
  }

  // Helper: CSRF token
  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)'));
    return match ? match.pop() : '';
  }

  // 1) Iniciar cámara
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    videoEl.srcObject = stream;
    await videoEl.play();
    update("warning", `Cámara iniciada. Presiona ${enterText}.`);
  } catch (err) {
    console.error(err);
    return update("danger", "No se pudo acceder a la cámara");
  }

  // 2) Al pulsar ENTER
  document.addEventListener("keydown", async e => {
    if (e.key !== "Enter") return;
    update("info", "Capturando foto…");

    // Crear snapshot
    const canvas = document.createElement("canvas");
    canvas.width  = videoEl.videoWidth;
    canvas.height = videoEl.videoHeight;
    canvas.getContext("2d").drawImage(videoEl, 0, 0);

    canvas.toBlob(async blob => {
      update("warning", "Verificando rostro…");

      // 2.1) Enviar snapshot para reconocimiento
      const fd = new FormData();
      fd.append("snapshot", blob, "snapshot.png");

      try {
        // Llamada al endpoint de reconocimiento facial
        const resp = await fetch("/recognition/verify-face/", {
          method: "POST",
          headers: { "X-CSRFToken": getCookie("csrftoken") },
          body: fd
        });
        const json = await resp.json();

        if (json.status === "ok") {
          const fullName = `${json.name} (${json.id})`;
          update("success", successMsg(fullName));

          // 2.2) Registrar entrada o salida en Django
          const endpoint = mode === 'entrada'
            ? "/accounts/registrar_entrada/"
            : "/recognition/RegistrarSalida/";

          await fetch(endpoint, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({
              identificacion: json.id,
              nombre:         json.name,
              apellido:       json.last_name || "",
              rol:            json.role    || "visitante",
              foto_url:       json.foto_url
            })
          });

          // (Opcional) Recargar la tabla de recientes o la página
          // window.location.reload();

        } else if (json.status === "unknown") {
          update("danger", "Usuario no registrado");
        } else if (json.status === "no_face") {
          update("warning", "No se detectó rostro");
        } else {
          update("danger", "Error inesperado");
        }
      } catch (err) {
        console.error(err);
        update("danger", "Error de red");
      }

    }, "image/png");
  });
});
