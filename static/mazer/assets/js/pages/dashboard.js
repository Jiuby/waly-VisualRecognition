// === Profile Bar Chart ===
var optionsProfileVisit = {
    annotations: { position: 'back' },
    dataLabels: { enabled: false },
    chart: { type: 'bar', height: 300 },
    fill: { opacity: 1 },
    plotOptions: {},
    series: [{
        name: 'sales',
        data: [9, 20, 30, 20, 10, 20, 30, 20, 10, 20, 30, 20]
    }],
    colors: '#435ebe',
    xaxis: {
        categories: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    }
};

// === Donut Chart Visitors ===
let optionsVisitorsProfile = {
    series: [70, 30],
    labels: ['Male', 'Female'],
    colors: ['#435ebe', '#55c6e8'],
    chart: {
        type: 'donut',
        width: '100%',
        height: '350px'
    },
    legend: {
        position: 'bottom'
    },
    plotOptions: {
        pie: {
            donut: {
                size: '30%'
            }
        }
    }
};

// === Área base de configuración (reutilizable)
const baseAreaOptions = {
    chart: { height: 80, type: 'area', toolbar: { show: false } },
    stroke: { width: 2 },
    grid: { show: false },
    dataLabels: { enabled: false },
    xaxis: {
        type: 'datetime',
        categories: [
            "2018-09-19T00:00:00.000Z", "2018-09-19T01:30:00.000Z", "2018-09-19T02:30:00.000Z",
            "2018-09-19T03:30:00.000Z", "2018-09-19T04:30:00.000Z", "2018-09-19T05:30:00.000Z",
            "2018-09-19T06:30:00.000Z", "2018-09-19T07:30:00.000Z", "2018-09-19T08:30:00.000Z",
            "2018-09-19T09:30:00.000Z", "2018-09-19T10:30:00.000Z", "2018-09-19T11:30:00.000Z"
        ],
        axisBorder: { show: false },
        axisTicks: { show: false },
        labels: { show: false }
    },
    yaxis: { labels: { show: false } },
    tooltip: {
        x: { format: 'dd/MM/yy HH:mm' }
    }
};

// === Gráficos individuales ===

var optionsEurope = {
    ...baseAreaOptions,
    colors: ['#5350e9'],
    series: [{
        name: 'Estudiantes',
        data: [310, 800, 600, 430, 540, 340, 605, 805, 430, 540, 340, 605]
    }]
};

var optionsAmerica = {
    ...baseAreaOptions,
    colors: ['#10b981'],
    series: [{
        name: 'Docente',
        data: [300, 500, 450, 470, 490, 510, 530, 550, 540, 520, 500, 480]
    }]
};

var optionsIndonesia = {
    ...baseAreaOptions,
    colors: ['#ef4444'],
    series: [{
        name: 'Administrativo',
        data: [400, 420, 390, 410, 450, 430, 440, 460, 470, 450, 440, 430]
    }]
};

var optionsAfrica = {
    ...baseAreaOptions,
    colors: ['#f59e0b'],
    series: [{
        name: 'Visitantes',
        data: [250, 300, 280, 400, 600, 700, 900, 1000, 950, 700, 400, 300]
    }]
};

var optionsPeru = {
    ...baseAreaOptions,
    colors: ['#f43f5e'],
    series: [{
        name: 'Operativo',
        data: [200, 210, 230, 220, 250, 240, 230, 260, 280, 270, 250, 240]
    }]
};

// === Render de los charts ===

new ApexCharts(document.querySelector("#chart-profile-visit"), optionsProfileVisit).render();
new ApexCharts(document.getElementById('chart-visitors-profile'), optionsVisitorsProfile).render();
new ApexCharts(document.querySelector("#chart-europe"), optionsEurope).render();
new ApexCharts(document.querySelector("#chart-america"), optionsAmerica).render();
new ApexCharts(document.querySelector("#chart-indonesia"), optionsIndonesia).render();
new ApexCharts(document.querySelector("#chart-africa"), optionsAfrica).render();
new ApexCharts(document.querySelector("#chart-peru"), optionsPeru).render();
