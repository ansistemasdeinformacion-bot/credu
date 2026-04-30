// CREDU - VERSIÓN FUNCIONAL CON CSV
let docenteActual = null;
let esperandoCedula = true;
let esperandoOpcion = false;
let docentesGlobal = [];

async function cargarDocentes() {
    try {
        console.log("📂 Cargando docentes.csv...");
        const response = await fetch('docentes.csv?_=' + Date.now());
        const csvText = await response.text();
        const lineas = csvText.split(/\r?\n/);
        const docentes = [];
        
        for (let i = 1; i < lineas.length; i++) {
            const linea = lineas[i].trim();
            if (linea === '') continue;
            
            const valores = linea.split(',');
            const cedula = valores[0]?.trim();
            const correo = valores[8]?.trim().toLowerCase();
            const nombre = valores[6]?.trim();
            const contrasena = valores[1]?.trim();
            
            if (cedula && correo && correo.includes('@')) {
                docentes.push({ cedula, correo, nombreCompleto: nombre, contrasena });
            }
        }
        
        docentesGlobal = docentes;
        localStorage.setItem('docentesDB', JSON.stringify(docentes));
        console.log(`✅ ${docentes.length} docentes cargados`);
        return docentes;
    } catch (error) {
        console.error('Error:', error);
        return [];
    }
}

function registrarIngreso(docente) {
    const ahora = new Date();
    const fecha = ahora.toISOString().split('T')[0];
    const hora = ahora.toLocaleTimeString('es-CO');
    let registros = JSON.parse(localStorage.getItem('registrosIngreso')) || [];
    registros.push({ fecha, hora, cedula: docente.cedula, docente: docente.nombreCompleto, correo: docente.correo });
    localStorage.setItem('registrosIngreso', JSON.stringify(registros));
    console.log('✅ Ingreso registrado');
}

function obtenerTratamiento(nombre) {
    const femeninos = ['ANA', 'MARIA', 'MARTHA', 'LUZ', 'GLORIA', 'NANCY', 'SANDRA', 'PAOLA', 'CAROLINA', 'ANDREA', 'DIANA', 'CLAUDIA', 'LILIANA', 'LINA', 'YAMILE', 'LORENA', 'SUSAN', 'SANDRA'];
    return femeninos.includes(nombre.split(' ')[0].toUpperCase()) ? 'profesora' : 'profesor';
}

function agregarMensaje(texto, tipo) {
    const chat = document.getElementById('chatMessages');
    if (!chat) return;
    const msg = document.createElement('div');
    msg.className = `mensaje ${tipo}`;
    msg.innerHTML = texto;
    chat.appendChild(msg);
    chat.scrollTop = chat.scrollHeight;
}

function mostrarOpciones() {
    document.getElementById('opcionesArea').style.display = 'flex';
    document.getElementById('inputArea').style.display = 'none';
    esperandoOpcion = true;
    esperandoCedula = false;
}

function ocultarOpciones() {
    document.getElementById('opcionesArea').style.display = 'none';
    document.getElementById('inputArea').style.display = 'flex';
    esperandoOpcion = false;
    esperandoCedula = true;
    document.getElementById('chatInput').value = '';
    document.getElementById('chatInput').focus();
}

function procesarOpcion(respuesta) {
    const tratamiento = obtenerTratamiento(docenteActual.nombreCompleto);
    if (respuesta === 'si') {
        agregarMensaje(`✅ Sí`, 'usuario');
        agregarMensaje(`🔄 Redirigiendo...`, 'sistema');
        setTimeout(() => { localStorage.removeItem('docenteCREDU'); window.location.href = 'index.html'; }, 2000);
    } else if (respuesta === 'no') {
        agregarMensaje(`❌ No`, 'usuario');
        agregarMensaje(`👋 Hasta luego, ${tratamiento} ${docenteActual.nombreCompleto}.`, 'sistema');
        setTimeout(() => { localStorage.removeItem('docenteCREDU'); window.location.href = 'index.html'; }, 3000);
    }
    ocultarOpciones();
}

function enviarCredenciales() {
    const esPersonalizada = docenteActual.contrasena === 'contraseña personalizada';
    if (esPersonalizada) {
        agregarMensaje(`🔐 Tu contraseña fue cambiada por ti mismo/a. Acércate a Tecnologías si no la recuerdas.`, 'sistema');
    } else {
        agregarMensaje(`📧 Tus credenciales fueron enviadas a: ${docenteActual.correo}`, 'sistema');
    }
    const tratamiento = obtenerTratamiento(docenteActual.nombreCompleto);
    agregarMensaje(`📌 ¿Algo más, ${tratamiento} ${docenteActual.nombreCompleto}?`, 'sistema');
    mostrarOpciones();
}

function verificarCedula(cedula) {
    if (docenteActual.cedula !== cedula) {
        agregarMensaje(`❌ Cédula incorrecta. Intenta de nuevo:`, 'sistema');
        return false;
    }
    registrarIngreso(docenteActual);
    const tratamiento = obtenerTratamiento(docenteActual.nombreCompleto);
    agregarMensaje(`✅ ¡Bienvenido${tratamiento === 'profesora' ? 'a' : ''}, ${tratamiento} ${docenteActual.nombreCompleto}!`, 'sistema');
    enviarCredenciales();
    return true;
}

async function iniciarAsistente() {
    await cargarDocentes();
    const guardado = localStorage.getItem('docenteCREDU');
    if (!guardado) { window.location.href = 'index.html'; return; }
    docenteActual = JSON.parse(guardado);
    
    agregarMensaje(`🤖 Hola, soy CREDU. Dame tu cédula:`, 'sistema');
    
    const input = document.getElementById('chatInput');
    const btn = document.getElementById('btnEnviar');
    
    function enviar() {
        const texto = input.value.trim();
        if (texto === '') return;
        if (esperandoOpcion) {
            const r = texto.toLowerCase();
            if (r === 'si' || r === 'sí') procesarOpcion('si');
            else if (r === 'no') procesarOpcion('no');
            else agregarMensaje(`❓ Responde "Sí" o "No"`, 'sistema');
            input.value = '';
            return;
        }
        if (esperandoCedula) {
            agregarMensaje(`🔑 ${texto}`, 'usuario');
            verificarCedula(texto);
            input.value = '';
        }
    }
    
    btn.onclick = enviar;
    input.onkeypress = (e) => { if (e.key === 'Enter') enviar(); };
    document.getElementById('btnSi').onclick = () => procesarOpcion('si');
    document.getElementById('btnNo').onclick = () => procesarOpcion('no');
}

function iniciarLogin() {
    const btn = document.getElementById('btnIngresar');
    const emailInput = document.getElementById('email');
    const errorDiv = document.getElementById('errorMsg');
    
    btn.onclick = async () => {
        const correo = emailInput.value.trim().toLowerCase();
        errorDiv.style.display = 'none';
        
        if (!correo.endsWith('@uniagustiniana.edu.co')) {
            errorDiv.textContent = '❌ Use su correo institucional';
            errorDiv.style.display = 'block';
            return;
        }
        
        await cargarDocentes();
        const docente = docentesGlobal.find(d => d.correo === correo);
        
        if (!docente) {
            errorDiv.textContent = `❌ Correo no registrado`;
            errorDiv.style.display = 'block';
            return;
        }
        
        localStorage.setItem('docenteCREDU', JSON.stringify(docente));
        window.location.href = 'asistente.html';
    };
}

if (window.location.pathname.includes('asistente.html')) {
    iniciarAsistente();
} else {
    iniciarLogin();
}