// static/mazer/assets/js/camara_mediapipe.js

document.addEventListener("DOMContentLoaded", async () => {
  console.log("▶️ camara_mediapipe.js iniciado");

  const videoElement = document.getElementById("video");
  let blinkCounter = 0;
  let blinking    = false;

  // Ajusta estos umbrales según tu cámara/luz
  const EAR_THRESHOLD    = 0.32;  // EAR por debajo de este valor cuenta como ojo cerrado
  const REQUIRED_CONSEC  = 2;     // Frames consecutivos

  // Función de cálculo EAR
  function calcEAR(landmarks, indices) {
    const d = (i, j) => {
      const dx = landmarks[i].x - landmarks[j].x;
      const dy = landmarks[i].y - landmarks[j].y;
      return Math.hypot(dx, dy);
    };
    const A = d(indices[1], indices[5]);
    const B = d(indices[2], indices[4]);
    const C = d(indices[0], indices[3]);
    return (A + B) / (2 * C);
  }

  // Callback cuando MediaPipe devuelve resultados
  function onResults(results) {
    if (!results.multiFaceLandmarks || !results.multiFaceLandmarks.length) {
      console.log("⚠️ No face detected");
      blinkCounter = 0;
      return;
    }
    const lm = results.multiFaceLandmarks[0];
    // Seis puntos que rodean cada ojo en FaceMesh
    const LEFT  = [33,160,158,133,153,144];
    const RIGHT = [263,387,385,362,380,373];

    const earL = calcEAR(lm, LEFT);
    const earR = calcEAR(lm, RIGHT);
    const ear  = (earL + earR) / 2;
    console.log(`👁 EAR L:${earL.toFixed(3)} R:${earR.toFixed(3)} → avg:${ear.toFixed(3)}`);

    if (ear < EAR_THRESHOLD) {
      blinkCounter++;
      console.log(`   ↓ ojo cerrado (contador=${blinkCounter})`);
    } else {
      if (blinkCounter >= REQUIRED_CONSEC && !blinking) {
        console.log(`✨ Blink detectado tras ${blinkCounter} frames`);
        blinking = true;
        captureAndSendSnapshot();
      }
      blinkCounter = 0;
    }
  }

  // Inicializa FaceMesh
  const faceMesh = new FaceMesh({
    locateFile: file => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`
  });
  faceMesh.setOptions({
    maxNumFaces: 1,
    refineLandmarks: true,
    minDetectionConfidence: 0.3,
    minTrackingConfidence: 0.3
  });
  faceMesh.onResults(onResults);

  // Inicia cámara
  const camera = new Camera(videoElement, {
    onFrame: async () => {
      await faceMesh.send({ image: videoElement });
    },
    width: 640,
    height: 480
  });
  await camera.start();
  console.log("📷 Cámara MediaPipe iniciada");

  // Captura y envía snapshot
  function captureAndSendSnapshot() {
    const canvas = document.createElement("canvas");
    canvas.width  = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(async blob => {
      console.log("📸 Enviando snapshot…");
      const fd = new FormData();
      fd.append("snapshot", blob, "snap.png");
      try {
        const resp = await fetch("/recognition/verify-face/", {
          method: "POST",
          headers: { "X-CSRFToken": getCookie("csrftoken") },
          body: fd
        });
        const json = await resp.json();
        console.log("[JS] verify-face response:", json);
        updateStatus(json.status === "ok", json.name, json.id);
      } catch (err) {
        console.error("❌ verify-face error:", err);
        updateStatus(false);
      } finally {
        blinking = false;
      }
    }, "image/png");
  }

  // Helpers
  function getCookie(name) {
    const m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return m ? m.pop() : "";
  }

  function updateStatus(ok, name = "", id = "") {
    const c = document.getElementById("status-container"),
          s = document.getElementById("registro-status");
    c.classList.remove("alert-warning","alert-success","alert-danger");
    if (ok) {
      c.classList.add("alert-success");
      s.textContent = `${name} (${id})`;
    } else {
      c.classList.add("alert-danger");
      s.textContent = "Usuario no en el sistema";
    }
  }
});
