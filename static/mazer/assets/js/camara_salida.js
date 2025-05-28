// static/mazer/assets/js/camara_salida.js
// Trigger de salida al pulsar ENTER, con mensaje de despedida

document.addEventListener("DOMContentLoaded", async () => {
  const videoEl    = document.getElementById("video");
  const statusBox  = document.getElementById("status-container");
  const statusSpan = document.getElementById("registro-status");

  function update(type, msg) {
    statusBox.className = `alert alert-${type} text-center mt-3`;
    statusSpan.textContent = msg;
  }

  function getCookie(name) {
    const m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return m ? m.pop() : "";
  }

  // 1) Iniciar cámara
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    videoEl.srcObject = stream;
    await videoEl.play();
    update("warning", "Cámara iniciada. Presiona ENTER para registrar salida.");
  } catch (err) {
    console.error("Error cámara:", err);
    return update("danger", "No se pudo acceder a la cámara");
  }

  // 2) Al pulsar ENTER
  document.addEventListener("keydown", async (e) => {
    if (e.key !== "Enter") return;
    update("info", "Capturando foto…");

    // Captura snapshot
    const canvas = document.createElement("canvas");
    canvas.width  = videoEl.videoWidth;
    canvas.height = videoEl.videoHeight;
    canvas.getContext("2d").drawImage(videoEl, 0, 0);

    canvas.toBlob(async (blob) => {
      update("warning", "Enviando foto para verificación…");
      const fd = new FormData();
      fd.append("snapshot", blob, "snapshot.png");

      try {
        const resp = await fetch("/recognition/verify-face/", {
          method: "POST",
          headers: { "X-CSRFToken": getCookie("csrftoken") },
          body: fd
        });
        const json = await resp.json();

        if (json.status === "ok") {
          // Mensaje de despedida
          update("success", `Hasta luego, ${json.name} (${json.id}) — Salida registrada`);
        } else if (json.status === "unknown") {
          update("danger", "Usuario no en el sistema");
        } else if (json.status === "no_face") {
          update("warning", "No se detectó rostro");
        } else {
          update("danger", "Error inesperado");
        }
      } catch (err) {
        console.error("fetch error:", err);
        update("danger", "Error de red");
      }
    }, "image/png");
  });
});
