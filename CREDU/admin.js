// ADMIN CREDU - PANEL DE CONTROL
let chartInstance = null;
let registrosActuales = [];

// ============ LOGIN ADMIN ============
if (window.location.pathname.includes('admin.html')) {
    const btnLogin = document.getElementById('btnAdminLogin');
    if (btnLogin) {
        btnLogin.addEventListener('click', function() {
            const user = document.getElementById('adminUser').value;
            const pass = document.getElementById('adminPass').value;
            const errorDiv = document.getElementById('errorMsg');
            if (user === 'admin' && pass === 'credu2026') {
                localStorage.setItem('adminLogged', 'true');
                window.location.href = 'admin-panel.html';
            } else {
                errorDiv.textContent = '❌ Usuario o contraseña incorrectos';
                errorDiv.style.display = 'block';
            }
        });
    }
}

// ============ PANEL ADMIN ============
if (window.location.pathname.includes('admin-panel.html')) {
    if (localStorage.getItem('adminLogged') !== 'true') {
        window.location.href = 'admin.html';
    }
    
    // Navegación
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const section = this.dataset.section;
            document.querySelectorAll('.admin-section').forEach(sec => sec.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(nav => nav.classList.remove('active'));
            document.getElementById(`${section}Section`).classList.add('active');
            this.classList.add('active');
            document.getElementById('sectionTitle').textContent = this.textContent.trim();
            if (section === 'dashboard') actualizarDashboard();
            if (section === 'calendario') inicializarCalendario();
            if (section === 'registros') cargarRegistros();
            if (section === 'docentes') cargarTablaDocentes();
            if (section === 'graficas') cargarGrafica();
        });
    });
    
    document.getElementById('btnLogout')?.addEventListener('click', () => {
        localStorage.removeItem('adminLogged');
        window.location.href = 'admin.html';
    });
    
    // ============ DASHBOARD ============
    function actualizarDashboard() {
        const docentes = JSON.parse(localStorage.getItem('docentesDB')) || (typeof docentesDB !== 'undefined' ? docentesDB : []);
        const registros = JSON.parse(localStorage.getItem('registrosIngreso')) || [];
        const hoy = new Date().toISOString().split('T')[0];
        const mesActual = new Date().getMonth() + 1;
        const anioActual = new Date().getFullYear();
        document.getElementById('totalDocentes').textContent = docentes.length;
        document.getElementById('totalIngresos').textContent = registros.length;
        document.getElementById('ingresosHoy').textContent = registros.filter(r => r.fecha === hoy).length;
        document.getElementById('ingresosMes').textContent = registros.filter(r => {
            const [anio, mes] = r.fecha.split('-');
            return parseInt(anio) === anioActual && parseInt(mes) === mesActual;
        }).length;
    }
    
    // ============ CALENDARIO ============
    let calendar = null;
    function inicializarCalendario() {
        if (calendar) calendar.destroy();
        const calendarEl = document.getElementById('calendar');
        const registros = JSON.parse(localStorage.getItem('registrosIngreso')) || [];
        const conteoPorDia = {};
        registros.forEach(r => { conteoPorDia[r.fecha] = (conteoPorDia[r.fecha] || 0) + 1; });
        const eventos = Object.keys(conteoPorDia).map(fecha => ({
            title: `${conteoPorDia[fecha]} ingresos`,
            start: fecha,
            color: '#F5A623',
            textColor: '#003366'
        }));
        calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            locale: 'es',
            headerToolbar: { left: 'prev,next', center: 'title', right: 'dayGridMonth' },
            validRange: { start: '2026-01-01' },
            events: eventos
        });
        calendar.render();
    }
    
    // ============ REGISTROS CON FILTRO ============
    function cargarRegistros() {
        const registros = JSON.parse(localStorage.getItem('registrosIngreso')) || [];
        registrosActuales = [...registros].reverse();
        const filtroCedula = document.getElementById('filtroCedula')?.value.trim() || '';
        let datosAMostrar = registrosActuales;
        if (filtroCedula) {
            datosAMostrar = registrosActuales.filter(r => r.cedula.includes(filtroCedula));
        }
        const tbody = document.getElementById('tablaRegistrosBody');
        tbody.innerHTML = datosAMostrar.map(r => `
            <tr><td>${r.fecha}</td><td>${r.hora}</td><td>${r.cedula}</td><td>${r.docente}</td><td>${r.correo}</td></tr>
        `).join('');
        if (datosAMostrar.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center">No hay registros</td></tr>';
        }
    }
    
    document.getElementById('btnFiltrar')?.addEventListener('click', cargarRegistros);
    document.getElementById('filtroCedula')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') cargarRegistros();
    });
    
    // Exportar a Excel
    document.getElementById('btnExportarExcel')?.addEventListener('click', () => {
        const mes = document.getElementById('mesExportar').value;
        const filtroCedula = document.getElementById('filtroCedula').value.trim();
        let registros = JSON.parse(localStorage.getItem('registrosIngreso')) || [];
        if (mes) {
            registros = registros.filter(r => r.fecha.substring(0, 7) === mes);
        }
        if (filtroCedula) {
            registros = registros.filter(r => r.cedula.includes(filtroCedula));
        }
        if (registros.length === 0) {
            alert('No hay registros para exportar');
            return;
        }
        const exportData = registros.map(r => ({
            Fecha: r.fecha, Hora: r.hora, Cédula: r.cedula, Docente: r.docente, Correo: r.correo
        }));
        const ws = XLSX.utils.json_to_sheet(exportData);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Registros');
        let nombreArchivo = 'registros_ingreso';
        if (mes) nombreArchivo += `_${mes}`;
        if (filtroCedula) nombreArchivo += `_cedula_${filtroCedula}`;
        XLSX.writeFile(wb, `${nombreArchivo}.xlsx`);
    });
    
    // ============ CRUD DOCENTES ============
    function cargarTablaDocentes() {
        let docentes = JSON.parse(localStorage.getItem('docentesDB'));
        if (!docentes || docentes.length === 0) {
            docentes = typeof docentesDB !== 'undefined' ? docentesDB : [];
            localStorage.setItem('docentesDB', JSON.stringify(docentes));
        }
        const tbody = document.getElementById('tablaDocentesBody');
        tbody.innerHTML = docentes.map((d, i) => `
            <tr>
                <td>${d.cedula}</td><td>${d.nombreCompleto}</td><td>${d.correo}</td>
                <td>${d.contrasena.length > 25 ? d.contrasena.substring(0, 25) + '...' : d.contrasena}</td>
                <td class="acciones">
                    <button class="btn-editar" data-index="${i}">✏️ Editar</button>
                    <button class="btn-eliminar" data-index="${i}">🗑️ Eliminar</button>
                </td>
            </tr>
        `).join('');
        document.querySelectorAll('.btn-editar').forEach(btn => {
            btn.addEventListener('click', () => editarDocente(parseInt(btn.dataset.index)));
        });
        document.querySelectorAll('.btn-eliminar').forEach(btn => {
            btn.addEventListener('click', () => eliminarDocente(parseInt(btn.dataset.index)));
        });
    }
    
    function editarDocente(index) {
        const docentes = JSON.parse(localStorage.getItem('docentesDB'));
        const d = docentes[index];
        document.getElementById('modalTitle').textContent = 'Editar Docente';
        document.getElementById('modalCedula').value = d.cedula;
        document.getElementById('modalNombre').value = d.nombreCompleto;
        document.getElementById('modalCorreo').value = d.correo;
        document.getElementById('modalContrasena').value = d.contrasena;
        document.getElementById('docenteModal').style.display = 'flex';
        document.getElementById('btnGuardarDocente').onclick = () => guardarDocente(index);
    }
    
    function eliminarDocente(index) {
        if (confirm('¿Eliminar este docente?')) {
            let docentes = JSON.parse(localStorage.getItem('docentesDB'));
            docentes.splice(index, 1);
            localStorage.setItem('docentesDB', JSON.stringify(docentes));
            cargarTablaDocentes();
            actualizarDashboard();
        }
    }
    
    document.getElementById('btnAgregarDocente')?.addEventListener('click', () => {
        document.getElementById('modalTitle').textContent = 'Agregar Docente';
        document.getElementById('modalCedula').value = '';
        document.getElementById('modalNombre').value = '';
        document.getElementById('modalCorreo').value = '';
        document.getElementById('modalContrasena').value = '';
        document.getElementById('docenteModal').style.display = 'flex';
        document.getElementById('btnGuardarDocente').onclick = () => guardarDocente(null);
    });
    
    function guardarDocente(index) {
        const cedula = document.getElementById('modalCedula').value.trim();
        const nombre = document.getElementById('modalNombre').value.trim();
        const correo = document.getElementById('modalCorreo').value.trim();
        const contrasena = document.getElementById('modalContrasena').value.trim();
        if (!cedula || !nombre || !correo || !contrasena) {
            alert('Todos los campos son obligatorios');
            return;
        }
        let docentes = JSON.parse(localStorage.getItem('docentesDB'));
        const nuevoDocente = { cedula, correo, nombreCompleto: nombre, nombre1: nombre.split(' ')[0], apellido1: nombre.split(' ').pop() || '', contrasena, estado: 'Activo' };
        if (index !== null && index !== undefined) docentes[index] = nuevoDocente;
        else docentes.push(nuevoDocente);
        localStorage.setItem('docentesDB', JSON.stringify(docentes));
        document.getElementById('docenteModal').style.display = 'none';
        cargarTablaDocentes();
        actualizarDashboard();
    }
    
    document.querySelector('.close-modal')?.addEventListener('click', () => {
        document.getElementById('docenteModal').style.display = 'none';
    });
    
    // ============ GRÁFICAS ============
    function cargarGrafica() {
        const anio = document.getElementById('anioGrafica').value;
        const mes = document.getElementById('mesGrafica').value;
        const registros = JSON.parse(localStorage.getItem('registrosIngreso')) || [];
        const filtrados = registros.filter(r => {
            const [a, m] = r.fecha.split('-');
            return a === anio && m === mes;
        });
        const diasEnMes = new Date(parseInt(anio), parseInt(mes), 0).getDate();
        const ingresosPorDia = Array(diasEnMes).fill(0);
        filtrados.forEach(r => {
            const dia = parseInt(r.fecha.split('-')[2]) - 1;
            if (dia >= 0 && dia < diasEnMes) ingresosPorDia[dia]++;
        });
        if (chartInstance) chartInstance.destroy();
        const ctx = document.getElementById('ingresosChart').getContext('2d');
        chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array.from({ length: diasEnMes }, (_, i) => i + 1),
                datasets: [{
                    label: `Ingresos - ${mes}/${anio}`,
                    data: ingresosPorDia,
                    borderColor: '#F5A623',
                    backgroundColor: 'rgba(245, 166, 35, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { labels: { color: '#F1F5F9' } } },
                scales: { x: { ticks: { color: '#94A3B8' } }, y: { ticks: { color: '#94A3B8' } } }
            }
        });
    }
    
    document.getElementById('btnActualizarGrafica')?.addEventListener('click', cargarGrafica);
    
    // Inicializar años
    const anioSelect = document.getElementById('anioGrafica');
    if (anioSelect) {
        for (let i = 2026; i <= 2035; i++) {
            const option = document.createElement('option');
            option.value = i; option.textContent = i;
            anioSelect.appendChild(option);
        }
    }
    
    // Inicializar mes por defecto
    const mesExportar = document.getElementById('mesExportar');
    if (mesExportar) {
        const ahora = new Date();
        mesExportar.value = `${ahora.getFullYear()}-${String(ahora.getMonth() + 1).padStart(2, '0')}`;
    }
    
    // Inicializar datos
    if (!localStorage.getItem('docentesDB')) {
        if (typeof docentesDB !== 'undefined') localStorage.setItem('docentesDB', JSON.stringify(docentesDB));
        else localStorage.setItem('docentesDB', JSON.stringify([]));
    }
    if (!localStorage.getItem('registrosIngreso')) {
        localStorage.setItem('registrosIngreso', JSON.stringify([]));
    }
    
    actualizarDashboard();
    cargarTablaDocentes();
}