/* dashboard.js  – actualiza los mini-charts de “Promedio de entrada”
   cada 30 min consultando /api/entradas-por-rol/
   Endpoint devuelve JSON:
   {
     "labels": ["07:00","07:30",…],         # intervalos locales
     "series": {
        "estudiante": [10,12,…],
        "docente":    [3,2,…],
        "administrativo":[1,…],
        "visitante":[4,…],
        "operativo":[0,…]
     }
   }
*/

// ───────────────── CONFIG BASE ─────────────────
const baseAreaChart = {
  chart:  { height: 80, type: "area", toolbar: { show: false }},
  stroke: { width: 2 },
  grid:   { show: false },
  dataLabels: { enabled: false },
  xaxis: { type: "category", axisBorder:{show:false}, axisTicks:{show:false}, labels:{show:false} },
  yaxis: { labels:{show:false} },
  tooltip:{ x:{ format:"HH:mm" } }
};

// Colores por rol
const ROL_COLORS = {
  estudiante:     "#5350e9",
  docente:        "#008b75",
  administrativo: "#dc3545",
  visitante:      "#f59e0b",
  operativo:      "#f43f5e",
};

// Map role→chart element id
const ROLE_TARGET = {
  estudiante:     "#chart-europe",
  docente:        "#chart-america",
  administrativo: "#chart-indonesia",
  visitante:      "#chart-africa",
  operativo:      "#chart-peru",
};

// Guardaremos instancias Apex para actualizarlas
const charts = {};

// ───────────────── FUNCIÓN DE CARGA ─────────────────
async function fetchRoleSeries() {
  try {
    const resp = await fetch("/api/entradas-por-rol/");
    if (!resp.ok) throw new Error("API error");
    return await resp.json();
  } catch (err) {
    console.error("No se pudo obtener datos de roles", err);
    return null;
  }
}

// Inicializa o actualiza los gráficos
function renderCharts(payload) {
  if (!payload) return;

  const { labels, series } = payload;

  Object.entries(series).forEach(([rol, data]) => {
    const opts = {
      ...baseAreaChart,
      colors: [ROL_COLORS[rol]],
      xaxis: { ...baseAreaChart.xaxis, categories: labels },
      series: [{ name: rol, data }]
    };

    if (charts[rol]) {
      // actualizar
      charts[rol].updateOptions(opts);
    } else {
      // crear
      const el = document.querySelector(ROLE_TARGET[rol]);
      charts[rol] = new ApexCharts(el, opts);
      charts[rol].render();
    }
  });
}

// ───────────────── INICIO ─────────────────
document.addEventListener("DOMContentLoaded", async () => {
  // Carga inicial
  renderCharts(await fetchRoleSeries());

  // Refresca cada 30 minutos
  setInterval(async () => {
    renderCharts(await fetchRoleSeries());
  }, 30 * 60 * 1000);
});

/* ------------- GRÁFICOS QUE YA TENÍAS ------------- */
/*  Profile visit bar y donut visitors (sin cambios)  */

var optionsProfileVisit = {
  annotations:{position:"back"}, dataLabels:{enabled:false},
  chart:{type:"bar", height:300}, fill:{opacity:1},
  series:[{name:"sales",data:[9,20,30,20,10,20,30,20,10,20,30,20]}],
  colors:"#435ebe",
  xaxis:{categories:["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]}
};
new ApexCharts(document.querySelector("#chart-profile-visit"),optionsProfileVisit).render();

let optionsVisitorsProfile = {
  series:[70,30], labels:["Male","Female"], colors:["#435ebe","#55c6e8"],
  chart:{type:"donut", width:"100%", height:"350px"}, legend:{position:"bottom"},
  plotOptions:{pie:{donut:{size:"30%"}}}
};
new ApexCharts(document.querySelector("#chart-visitors-profile"),optionsVisitorsProfile).render();
