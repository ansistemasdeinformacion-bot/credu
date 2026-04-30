// CREDU - VERSIÓN FINAL CON ENVÍO DE CORREO PREPARADO
let docenteActual = null;
let esperandoCedula = true;
let esperandoOpcion = false;
let docentesGlobal = [];

// ============ CONFIGURACIÓN ============
// Cambia esta variable a false cuando subas a la nube
const MODO_SIMULACION = true;  // true: simula correo, false: envía correo real

// Credenciales para EmailJS (cambiar cuando subas a la nube)
const EMAILJS_CONFIG = {
    SERVICE_ID: 'service_tu_id',      // Cambiar por el ID real
    TEMPLATE_ID: 'template_tu_id',    // Cambiar por el ID real
    PUBLIC_KEY: 'tu_public_key'       // Cambiar por tu clave pública
};
// =====================================

// Cargar docentes desde docentes.txt (formato TSV)
async function cargarDocentes() {
    try {
        console.log("📂 Leyendo docentes.txt...");
        
        const response = await fetch('docentes.txt');
        const texto = await response.text();
        
        const lineas = texto.split(/\r?\n/);
        const encabezados = lineas[0].split(/\t/);
        
        const idxCedula = encabezados.findIndex(h => h.includes('CEDULA'));
        const idxContrasena = encabezados.findIndex(h => h.includes('CONTRASEÑA'));
        const idxNombreCompleto = encabezados.findIndex(h => h.includes('NOMBRE COMPLETO'));
        const idxCorreo = encabezados.findIndex(h => h.includes('CORREO INSTITUCIONAL'));
        const idxNombre1 = encabezados.findIndex(h => h.includes('NOMBRE 1'));
        
        docentesGlobal = [];
        
        for (let i = 1; i < lineas.length; i++) {
            const linea = lineas[i].trim();
            if (linea === '') continue;
            
            const columnas = linea.split(/\t/);
            
            const cedula = columnas[idxCedula]?.trim() || '';
            let contrasena = columnas[idxContrasena]?.trim() || 'credu2026';
            let nombreCompleto = columnas[idxNombreCompleto]?.trim() || '';
            let correo = columnas[idxCorreo]?.trim().toLowerCase() || '';
            const nombre1 = idxNombre1 !== -1 ? columnas[idxNombre1]?.trim() || '' : '';
            
            if (contrasena && (
                contrasena.toLowerCase() === 'contraseña personalizada' ||
                contrasena.toLowerCase() === 'personalizada'
            )) {
                contrasena = 'contraseña personalizada';
            }
            
            correo = correo.replace(/\s/g, '');
            
            if (cedula && correo && correo.includes('@')) {
                docentesGlobal.push({
                    cedula: cedula,
                    correo: correo,
                    nombreCompleto: nombreCompleto,
                    nombre1: nombre1,
                    contrasena: contrasena
                });
            }
        }
        
        localStorage.setItem('docentesDB', JSON.stringify(docentesGlobal));
        console.log(`✅ ${docentesGlobal.length} docentes cargados`);
        
        const personalizados = docentesGlobal.filter(d => d.contrasena === 'contraseña personalizada').length;
        console.log(`🔐 ${personalizados} docentes con contraseña personalizada`);
        
        return docentesGlobal.length > 0;
        
    } catch (error) {
        console.error("❌ Error cargando docentes.txt:", error);
        return false;
    }
}

// ============ DETECCIÓN DE GÉNERO INTELIGENTE ============
function obtenerTratamiento(nombreCompleto, nombre1) {
    let primerNombre = '';
    
    if (nombre1 && nombre1.trim()) {
        primerNombre = nombre1.trim().toUpperCase();
    } else if (nombreCompleto) {
        primerNombre = nombreCompleto.split(' ')[0].toUpperCase();
    }
    
    if (!primerNombre) return 'profesor';
    
    if (primerNombre.endsWith('A')) {
        const masculinosTerminanA = ['JOSE', 'JOSUE', 'JESUS', 'JUAN', 'MANUEL', 'RAFAEL', 'ANGEL', 'SAUL', 'ELIAS', 'NOE'];
        if (masculinosTerminanA.includes(primerNombre)) {
            return 'profesor';
        }
        return 'profesora';
    }
    
    const femeninosEspeciales = [
        'MARIA', 'MARI', 'LUZ', 'MERCEDES', 'DOLORES', 'CARMEN', 'ROSARIO',
        'ANGELES', 'NIEVES', 'SOLEDAD', 'GINNA', 'GINA', 'YOLIMA', 'NANCY', 'KAREN'
    ];
    
    if (femeninosEspeciales.includes(primerNombre)) {
        return 'profesora';
    }
    
    return 'profesor';
}

function obtenerSaludo(nombreCompleto, nombre1) {
    const tratamiento = obtenerTratamiento(nombreCompleto, nombre1);
    if (tratamiento === 'profesora') {
        return `✅ <strong>¡Bienvenida, profesora ${nombreCompleto}!</strong>`;
    } else {
        return `✅ <strong>¡Bienvenido, profesor ${nombreCompleto}!</strong>`;
    }
}

function buscarDocente(correo) {
    const busqueda = correo.toLowerCase().trim();
    
    let encontrado = docentesGlobal.find(d => d.correo === busqueda);
    if (encontrado) return encontrado;
    
    const sinPuntos = busqueda.replace(/[.-]/g, '');
    encontrado = docentesGlobal.find(d => d.correo.replace(/[.-]/g, '') === sinPuntos);
    if (encontrado) return encontrado;
    
    const parteLocal = busqueda.split('@')[0];
    encontrado = docentesGlobal.find(d => d.correo.includes(parteLocal));
    
    return encontrado;
}

function registrarIngreso(d) {
    const ahora = new Date();
    const fecha = ahora.toISOString().split('T')[0];
    const hora = ahora.toLocaleTimeString('es-CO');
    const registros = JSON.parse(localStorage.getItem('registrosIngreso') || '[]');
    registros.push({ fecha, hora, cedula: d.cedula, docente: d.nombreCompleto, correo: d.correo });
    localStorage.setItem('registrosIngreso', JSON.stringify(registros));
    console.log(`✅ Ingreso registrado: ${d.nombreCompleto}`);
}

// ============ FUNCIÓN PARA ENVIAR CORREO REAL ============
async function enviarCorreoReal(docente) {
    const tratamiento = obtenerTratamiento(docente.nombreCompleto, docente.nombre1);
    const saludoInicial = tratamiento === 'profesora' ? 'Estimada profesora' : 'Estimado profesor';
    
    // Cargar EmailJS (solo si no está cargado)
    if (typeof emailjs === 'undefined') {
        await new Promise((resolve) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/@emailjs/browser@4/dist/email.min.js';
            script.onload = () => {
                emailjs.init(EMAILJS_CONFIG.PUBLIC_KEY);
                resolve();
            };
            document.head.appendChild(script);
        });
    }
    
    const templateParams = {
        to_email: docente.correo,
        to_name: docente.nombreCompleto,
        tratamiento: tratamiento,
        saludo_inicial: saludoInicial,
        usuario: docente.cedula,
        contrasena: docente.contrasena,
        year: new Date().getFullYear()
    };
    
    try {
        const response = await emailjs.send(
            EMAILJS_CONFIG.SERVICE_ID,
            EMAILJS_CONFIG.TEMPLATE_ID,
            templateParams
        );
        console.log("✅ Correo real enviado:", response);
        return true;
    } catch (error) {
        console.error("❌ Error enviando correo:", error);
        return false;
    }
}

// ============ FUNCIÓN PARA SIMULAR ENVÍO DE CORREO (modo local) ============
function enviarCorreoSimulado(docente) {
    const tratamiento = obtenerTratamiento(docente.nombreCompleto, docente.nombre1);
    console.log("📧 SIMULACIÓN DE CORREO:");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.log(`📧 Para: ${docente.correo}`);
    console.log(`📋 Asunto: CREDU - Tus credenciales institucionales`);
    console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    console.log(`${tratamiento === 'profesora' ? 'Estimada profesora' : 'Estimado profesor'} ${docente.nombreCompleto},`);
    console.log(``);
    console.log(`Te damos la bienvenida a CREDU, el sistema de credenciales de la Uniagustiniana.`);
    console.log(``);
    console.log(`📌 Tus credenciales de acceso son:`);
    console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    console.log(`🔑 Usuario: ${docente.cedula}`);
    console.log(`🔒 Contraseña: ${docente.contrasena}`);
    console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    console.log(``);
    console.log(`🔗 Plataformas disponibles:`);
    console.log(`• SIGA: https://siga.uniagustiniana.edu.co`);
    console.log(`• KAWAK: https://kawak.uniagustiniana.edu.co`);
    console.log(`• SIPA HCM: https://sipahcm.uniagustiniana.edu.co`);
    console.log(``);
    console.log(`📌 Si tienes alguna duda, acércate a la oficina de Tecnologías en la sede Tagaste.`);
    console.log(``);
    console.log(`Atentamente,`);
    console.log(`CREDU - Uniagustiniana`);
    console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
}

// ============ FUNCIÓN PRINCIPAL DE ENVÍO DE CREDENCIALES ============
async function enviarCredenciales() {
    const tratamiento = obtenerTratamiento(docenteActual?.nombreCompleto, docenteActual?.nombre1);
    
    // Mostrar mensaje en el chat
    agregarMensaje(`
        <div style="background: rgba(0, 229, 160, 0.1); border-left: 4px solid #00E5A0; padding: 12px; border-radius: 12px; margin: 5px 0;">
            📧 <strong>Tus credenciales de SIGA, KAWAK y SIPA HCM</strong> están siendo enviadas a tu correo institucional:<br>
            <strong style="color: #00E5A0;">${docenteActual?.correo}</strong>
        </div>
    `, 'sistema');
    
    // Enviar correo (real o simulado)
    if (MODO_SIMULACION) {
        // Modo simulación (local)
        enviarCorreoSimulado(docenteActual);
        agregarMensaje(`📧 <strong>SIMULACIÓN:</strong> Revisa la consola (F12) para ver el correo que se enviará en producción.`, 'sistema');
    } else {
        // Modo real (nube)
        const enviado = await enviarCorreoReal(docenteActual);
        if (!enviado) {
            agregarMensaje(`⚠️ <strong>Error al enviar el correo.</strong> Por favor, intenta nuevamente o contacta a Tecnologías.`, 'sistema');
        }
    }
    
    agregarMensaje(`📌 ¿Algo más en lo que pueda ayudarte, ${tratamiento}?`, 'sistema');
    mostrarOpciones();
}
// ==================================================================

function verificarCedula(ced) {
    if (docenteActual?.cedula !== ced) {
        agregarMensaje(`❌ Lo siento, la cédula "<strong>${ced}</strong>" no coincide.`, 'sistema');
        agregarMensaje(`📝 Por favor, ingresa tu número de cédula nuevamente:`, 'sistema');
        return false;
    }
    
    registrarIngreso(docenteActual);
    const saludo = obtenerSaludo(docenteActual.nombreCompleto, docenteActual.nombre1);
    agregarMensaje(saludo, 'sistema');
    
    // Verificar si es contraseña personalizada para mostrar alerta
    const esPersonalizada = docenteActual?.contrasena === 'contraseña personalizada';
    if (esPersonalizada) {
        const mensajeAdvertencia = `
            <div style="background: rgba(255, 71, 87, 0.2); border: 2px solid #FF4757; border-radius: 16px; padding: 16px; margin: 8px 0;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                    <span style="font-size: 28px;">⚠️</span>
                    <strong style="color: #FF4757; font-size: 1.1rem;">¡CONTRASEÑA PERSONALIZADA!</strong>
                </div>
                <p style="margin: 8px 0; color: #FFD166;">
                    <strong>Estimado/a ${obtenerTratamiento(docenteActual.nombreCompleto, docenteActual.nombre1)},</strong>
                </p>
                <p style="margin: 8px 0;">
                    Tu contraseña <strong style="color: #FF4757;">fue modificada por ti mismo/a</strong> en algún momento.
                </p>
                <div style="background: rgba(0, 0, 0, 0.3); border-radius: 12px; padding: 12px; margin: 12px 0;">
                    <p style="margin: 5px 0;">🔐 Si <strong style="color: #FF4757;">NO RECUERDAS tu contraseña</strong>:</p>
                    <p style="margin: 5px 0;">📌 Debes acercarte a la <strong style="color: #F5A623;">oficina de Tecnologías de la Información</strong></p>
                    <p style="margin: 5px 0;">📍 <strong>Ubicación:</strong> Sede Tagaste</p>
                </div>
                <p style="margin: 8px 0; font-size: 0.85rem; color: #94A3B8;">
                    ⏰ Horario de atención: Lunes a Viernes de 8:00 AM a 5:00 PM
                </p>
            </div>
        `;
        agregarMensaje(mensajeAdvertencia, 'sistema');
    }
    
    enviarCredenciales();
    return true;
}

function agregarMensaje(texto, tipo) {
    const chat = document.getElementById('chatMessages');
    if (!chat) return;
    const m = document.createElement('div');
    m.className = `mensaje ${tipo}`;
    m.innerHTML = texto;
    chat.appendChild(m);
    chat.scrollTop = chat.scrollHeight;
}

let esperaCedula = true, esperaOpcion = false;

function mostrarOpciones() {
    const opc = document.getElementById('opcionesArea');
    const inpArea = document.getElementById('inputArea');
    if (opc) opc.style.display = 'flex';
    if (inpArea) inpArea.style.display = 'none';
    esperaOpcion = true;
    esperaCedula = false;
}

function ocultarOpciones() {
    const opc = document.getElementById('opcionesArea');
    const inpArea = document.getElementById('inputArea');
    if (opc) opc.style.display = 'none';
    if (inpArea) inpArea.style.display = 'flex';
    esperaOpcion = false;
    esperaCedula = true;
    const inp = document.getElementById('chatInput');
    if (inp) inp.value = '';
}

function procesarOpcion(r) {
    const tratamiento = obtenerTratamiento(docenteActual?.nombreCompleto, docenteActual?.nombre1);
    if (r === 'si') {
        agregarMensaje('✅ Sí', 'usuario');
        agregarMensaje('🔄 Serás redirigido a la página principal...', 'sistema');
        setTimeout(() => { localStorage.removeItem('docenteCREDU'); window.location.href = 'index.html'; }, 2000);
    } else {
        agregarMensaje('❌ No', 'usuario');
        agregarMensaje(`👋 Fue un gusto ayudarte, ${tratamiento} ${docenteActual?.nombreCompleto || ''}. ¡Hasta la próxima!`, 'sistema');
        setTimeout(() => { localStorage.removeItem('docenteCREDU'); window.location.href = 'index.html'; }, 3000);
    }
    ocultarOpciones();
}

async function iniciarAsistente() {
    await cargarDocentes();
    
    const g = localStorage.getItem('docenteCREDU');
    if (!g) { window.location.href = 'index.html'; return; }
    docenteActual = JSON.parse(g);
    
    const chatContainer = document.getElementById('chatMessages');
    if (chatContainer) {
        chatContainer.innerHTML = '';
    }
    
    agregarMensaje('🤖 ¡Hola! Soy <strong>CREDU</strong>, tu asistente virtual.', 'sistema');
    agregarMensaje('📝 Para ayudarte con tus credenciales, regálame tu número de cédula:', 'sistema');
    
    const inp = document.getElementById('chatInput');
    const btn = document.getElementById('btnEnviar');
    
    function enviar() {
        const txt = inp.value.trim();
        if (!txt) return;
        if (esperaOpcion) {
            const r = txt.toLowerCase();
            if (r === 'si' || r === 'sí') procesarOpcion('si');
            else if (r === 'no') procesarOpcion('no');
            else agregarMensaje('❓ Por favor, responde con "Sí" o "No".', 'sistema');
            inp.value = '';
            return;
        }
        if (esperaCedula) {
            agregarMensaje(`🔑 ${txt}`, 'usuario');
            verificarCedula(txt);
            inp.value = '';
        }
    }
    
    btn.onclick = enviar;
    inp.onkeypress = (e) => { if (e.key === 'Enter') enviar(); };
    
    const btnSi = document.getElementById('btnSi');
    const btnNo = document.getElementById('btnNo');
    if (btnSi) btnSi.onclick = () => procesarOpcion('si');
    if (btnNo) btnNo.onclick = () => procesarOpcion('no');
}

async function iniciarLogin() {
    const btn = document.getElementById('btnIngresar');
    const inp = document.getElementById('email');
    const err = document.getElementById('errorMsg');
    if (!btn) return;
    
    btn.onclick = async () => {
        const email = inp.value.trim().toLowerCase();
        if (err) err.style.display = 'none';
        
        if (!email.endsWith('@uniagustiniana.edu.co')) {
            if (err) { err.textContent = '❌ Use su correo institucional (@uniagustiniana.edu.co)'; err.style.display = 'block'; }
            return;
        }
        
        if (err) { err.textContent = '⏳ Verificando credenciales...'; err.style.display = 'block'; }
        
        await cargarDocentes();
        const docente = buscarDocente(email);
        
        if (!docente) {
            if (err) { err.textContent = `❌ Correo "${email}" no registrado en la base de datos de docentes.`; err.style.display = 'block'; }
            return;
        }
        
        localStorage.setItem('docenteCREDU', JSON.stringify(docente));
        window.location.href = 'asistente.html';
    };
}

if (window.location.pathname.includes('asistente.html')) {
    iniciarAsistente();
} else if (!window.location.pathname.includes('admin')) {
    iniciarLogin();
}