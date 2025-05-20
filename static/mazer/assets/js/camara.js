// static/mazer/assets/js/camara.js
// Cuenta atrás de 5 s. Si hay rostro al llegar a 0, envía el fotograma
// a /recognition/verify-face/ .  No hay botones.

console.log('▶️ camara.js cargado');

document.addEventListener('DOMContentLoaded', async () => {
  const video  = document.getElementById('video');
  const select = document.getElementById('cams');
  const cdDom  = document.getElementById('cd');
  const stat   = document.getElementById('status');

  /* 1 – Abrir webcam */
  const cams = (await navigator.mediaDevices.enumerateDevices())
               .filter(d => d.kind === 'videoinput');
  if (!cams.length) { stat.textContent = '❌ No hay cámara'; return; }

  select.innerHTML = cams.map(
    (c,i)=>`<option value="${c.deviceId}">${c.label||'Cam '+(i+1)}</option>`).join('');
  select.onchange = () => startStream(select.value);
  await startStream(cams[0].deviceId);

  /* 2 – Cargar modelo de rostro */
  const faceModel = await faceLandmarksDetection.load(
    faceLandmarksDetection.SupportedPackages.mediapipeFacemesh);

  /* 3 – Contador + lógica en un solo setInterval */
  let counter = 5;
  cdDom.textContent = counter;

  setInterval(async () => {
    counter--;
    cdDom.textContent = counter;

    if (counter > 0) return;          // aún no toca

    counter = 5;                      // reiniciar YA el contador
    cdDom.textContent = counter;

    if (video.readyState < 2) return; // no hay frame

    const faces = await faceModel.estimateFaces({input: video});
    if (!faces.length) {
      stat.className = 'alert alert-warning text-center mt-3 mx-auto';
      stat.textContent = '⛔ Sin rostro — próxima captura en 5 s';
      return;
    }

    /* hay rostro → capturar y enviar */
    stat.className = 'alert alert-info text-center mt-3 mx-auto';
    stat.textContent = '📤 Enviando…';

    const canvas = document.createElement('canvas');
    canvas.width  = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    const blob = await new Promise(r => canvas.toBlob(r, 'image/png'));
    const fd   = new FormData();
    fd.append('snapshot', blob, 'snap.png');

    try {
      const resp = await fetch('/recognition/verify-face/', {
        method : 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body   : fd
      });
      const j = await resp.json();
      console.log('verify-face:', j);
      if (j.status === 'ok') {
        stat.className = 'alert alert-success text-center mt-3 mx-auto';
        stat.textContent = `✅ ${j.name} (${j.id})`;
      } else {
        stat.className = 'alert alert-danger text-center mt-3 mx-auto';
        stat.textContent = '❌ Usuario no en el sistema';
      }
    } catch (e) {
      console.error(e);
      stat.className = 'alert alert-danger text-center mt-3 mx-auto';
      stat.textContent = '❌ Error al enviar';
    }
  }, 1000);

  /* helpers */
  async function startStream(id){
    if (window.stream) window.stream.getTracks().forEach(t=>t.stop());
    window.stream = await navigator.mediaDevices.getUserMedia({
      video:{deviceId:{exact:id}}, audio:false});
    video.srcObject = window.stream; await video.play();
  }
  function getCookie(n){
    const m=document.cookie.match('(^|;)\\s*'+n+'=\\s*([^;]+)');return m?m.pop():'';
  }
});
