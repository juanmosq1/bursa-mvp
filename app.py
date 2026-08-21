import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import requests

st.set_page_config(page_title="Bursa", page_icon="📈", layout="centered")

# ---------------------------------------------------------------------------
# Credenciales de Alpaca (se leen de Streamlit Secrets, nunca escritas aqui)
# ---------------------------------------------------------------------------
try:
    ALPACA_API_KEY = st.secrets["ALPACA_API_KEY"]
    ALPACA_SECRET_KEY = st.secrets["ALPACA_SECRET_KEY"]
    ALPACA_CONFIGURADO = True
except (KeyError, FileNotFoundError):
    ALPACA_CONFIGURADO = False

# ---------------------------------------------------------------------------
# Marca Bursa
# ---------------------------------------------------------------------------
NAVY = "#101B2E"
TEAL_DARK = "#0E8F73"
TEAL_MID = "#12B08C"
TEAL_LIGHT = "#15CC9F"
TEAL_BRIGHT = "#18E8B5"
GOLD = "#F5B914"
GOLD_DARK = "#7A5200"

LOGO_SVG = f"""
<svg width="34" height="34" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="512" height="512" rx="112" fill="{NAVY}"/>
<rect x="106" y="300" width="60" height="90" rx="12" fill="{TEAL_DARK}"/>
<rect x="186" y="250" width="60" height="140" rx="12" fill="{TEAL_MID}"/>
<rect x="266" y="200" width="60" height="190" rx="12" fill="{TEAL_LIGHT}"/>
<rect x="346" y="160" width="60" height="230" rx="12" fill="{TEAL_BRIGHT}"/>
<circle cx="376" cy="122" r="30" fill="{GOLD}"/>
</svg>
"""

st.markdown(f"""
<style>
.stApp {{ max-width: 480px; margin: 0 auto; }}
.bursa-header {{ display:flex; align-items:center; gap:10px; margin-bottom: 0.5rem; }}
.bursa-header span {{ font-size: 22px; font-weight: 700; color: {NAVY}; }}
div.stButton > button {{
    background-color: {NAVY}; color: white; border: none; border-radius: 8px;
    font-weight: 500; width: 100%; padding: 10px 0; min-height: 48px;
}}
div.stButton > button:hover {{ background-color: #1c2c47; color: white; }}
.bursa-card {{
    background: white; border: 1px solid #E5E5E0; border-radius: 12px;
    padding: 14px 16px; margin-bottom: 12px;
}}
.bursa-coin {{ background:#E1F5EE; border-radius:8px; padding:10px 12px; text-align:center; }}
.bursa-token {{ background:#FDF0CE; border-radius:8px; padding:10px 12px; text-align:center; }}
.bursa-badge {{
    display:inline-block; background:{NAVY}; color:{GOLD}; font-size:11px;
    padding:3px 10px; border-radius:6px; font-weight:600;
}}
.risk-alto {{ color:#A32D2D; font-weight:600; }}
.risk-moderado {{ color:{TEAL_DARK}; font-weight:600; }}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="bursa-header">{LOGO_SVG}<span>bursa</span></div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Estado de la app (simula la base de datos mientras dura la sesion)
# ---------------------------------------------------------------------------
if "coins" not in st.session_state:
    st.session_state.coins = 1500
if "tokens" not in st.session_state:
    st.session_state.tokens = 18
if "history" not in st.session_state:
    st.session_state.history = [
        {"label": "Quiz completado: riesgo vs volatilidad", "amount": "+40 monedas"},
        {"label": "Bono de racha: 7 días seguidos", "amount": "+25 monedas"},
    ]
if "copied" not in st.session_state:
    st.session_state.copied = {}
if "caps" not in st.session_state:
    st.session_state.caps = {}
if "wtp_responses" not in st.session_state:
    st.session_state.wtp_responses = []
if "usuario_educado" not in st.session_state:
    st.session_state.usuario_educado = False

PAQUETES = [
    {"nombre": "Paquete básico", "monedas": 500, "precio": "$9.900 COP"},
    {"nombre": "Paquete popular", "monedas": 1200, "precio": "$19.900 COP"},
    {"nombre": "Paquete pro", "monedas": 3000, "precio": "$39.900 COP"},
]

EXPERTS = [
    {
        "id": "Juan",
        "nombre": "Juan Mosquera",
        "rentabilidad": "+18.4%",
        "riesgo": "moderado",
        "seguidores": 3204,
        "cap_default": 25,
        "cap_max": 45,
        "pregunta": "Si diversificas en 10 activos poco correlacionados en vez de 1 solo, tu riesgo total generalmente...",
        "opciones": ["Sube", "Baja", "No cambia"],
        "correcta": 1,
    },
    {
        "id": "laura",
        "nombre": "Laura Salas",
        "rentabilidad": "+41.2%",
        "riesgo": "alto",
        "seguidores": 890,
        "cap_default": 10,
        "cap_max": 30,
        "pregunta": "Si el precio de un activo cae 30% de golpe, una posición apalancada 5 veces puede...",
        "opciones": ["Perder proporcionalmente 30%", "Liquidarse por completo", "No cambiar"],
        "correcta": 1,
    },
]


def coins_add(amount, label):
    st.session_state.coins += amount
    st.session_state.history.insert(0, {"label": label, "amount": f"+{amount} monedas"})


def coins_spend(amount, label):
    if st.session_state.coins >= amount:
        st.session_state.coins -= amount
        st.session_state.history.insert(0, {"label": label, "amount": f"-{amount} monedas"})
        return True
    return False


# ---------------------------------------------------------------------------
# Balance visible siempre arriba
# ---------------------------------------------------------------------------
c1, c2 = st.columns(2)
with c1:
    st.markdown(f"""<div class="bursa-coin"><div style="font-size:18px;font-weight:700;color:#04342C">{st.session_state.coins:,}</div><div style="font-size:12px;color:{TEAL_DARK}">monedas</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="bursa-token"><div style="font-size:18px;font-weight:700;color:#412402">{st.session_state.tokens}</div><div style="font-size:12px;color:{GOLD_DARK}">tokens</div></div>""", unsafe_allow_html=True)

st.write("")

tab_inicio, tab_academia, tab_expertos, tab_rendimiento, tab_mercado, tab_wallet = st.tabs(
    ["Inicio", "Academia", "Descubrir expertos", "Rendimiento", "Mercado en vivo", "Wallet"]
)

# ---------------------------------------------------------------------------
# TAB 1: Inicio
# ---------------------------------------------------------------------------
with tab_inicio:
    st.markdown("""<div class="bursa-card">
        <b>Cómo leer una vela japonesa</b><br>
        <span style="color:#666;font-size:13px;">Video · 4 min</span>
    </div>""", unsafe_allow_html=True)

    with st.expander("Quiz: riesgo vs volatilidad · +40 monedas", expanded=False):
        st.write("¿Qué mide realmente la volatilidad de un activo?")
        resp = st.radio(
            "Selecciona una respuesta",
            ["Su rentabilidad promedio histórica", "Qué tanto varía su precio en el tiempo", "El número de operaciones diarias"],
            index=None, key="quiz_inicio", label_visibility="collapsed",
        )
        if st.button("Responder", key="btn_quiz_inicio"):
            if resp is None:
                st.error("Selecciona una respuesta antes de continuar.")
            elif resp == "Qué tanto varía su precio en el tiempo":
                if "quiz_inicio_done" not in st.session_state:
                    coins_add(40, "Quiz completado: riesgo vs volatilidad")
                    st.session_state.quiz_inicio_done = True
                st.success("Correcto. +40 monedas")
            else:
                st.warning("No es correcto, intenta de nuevo.")

    st.markdown(f"""<div class="bursa-card">
        <span class="bursa-badge">VIP</span><br><br>
        <b>Sesión en vivo con Camila Ríos</b><br>
        <span style="color:#666;font-size:13px;">Análisis de apertura Wall Street · Hoy 8:00am</span>
    </div>""", unsafe_allow_html=True)

    if st.button("Desbloquear con 800 monedas", key="btn_vip"):
        if coins_spend(800, "Sesión VIP desbloqueada: Camila Ríos"):
            st.success("Sesión desbloqueada. Te llegará el enlace antes de las 4:00pm.")
        else:
            st.error("No tienes monedas suficientes todavía. Completa más retos para ganar.")

# ---------------------------------------------------------------------------
# TAB 2: academia (certificacion con quiz opcional)
# ---------------------------------------------------------------------------
with tab_academia:
    st.caption("Ruta alterna en prueba: aprobar el quiz te permite desbloquear copiar traders ilimitadamente. Compárala con 'Descubrir expertos', donde se puede copiar de inmediato con un límite por defecto.")

    st.header("Clase 1: ¿Qué es un ETF y cómo reduce tu riesgo?")

    tab1, tab2 = st.tabs(["📖 Lectura Rápida", "🎥 Video Explicativo"])
    with tab1:
        st.markdown("""
        Un *ETF (Exchange-Traded Fund)* o Fondo Cotizado en Bolsa, es como una canasta de acciones.
        En lugar de comprar una sola empresa (como Apple o Tesla), compras una fracción de cientos de empresas al mismo tiempo.

        *   *Diversificación:* Si a una empresa le va mal, las otras equilibran el portafolio.
        *   *VOO:* Es el ETF que replica las 500 empresas más grandes de EE.UU. (S&P 500).
        *   *QQQ:* Es el ETF que agrupa a las 100 empresas tecnológicas más importantes (Nasdaq).
        """)
    with tab2:
        # Embeber un video educativo (puedes cambiarlo por tu propio enlace de YouTube o Vimeo)
        st.video("https://youtube.com")

    st.divider()
    st.header("🧠 Quiz ")
    st.write("Responde correctamente para copiar ilimitadamente.")

    with st.form("quiz_educativo"):
        pregunta_1 = st.radio(
            "1. Si quieres invertir en las 500 empresas más grandes de EE.UU. de forma diversificada, ¿qué activo elegirías?",
            ["Una acción individual de Tesla", "El ETF VOO (S&P 500)", "Dejar el dinero en efectivo"],
            index=None,
        )
        pregunta_2 = st.radio(
            "2. ¿Cuál es el principal beneficio de invertir a través de un ETF?",
            ["Garantizar ganancias del 100% diario", "Eliminar por completo las fluctuaciones del mercado", "Diversificar tu capital en múltiples empresas con una sola operación"],
            index=None,
        )
        boton_enviar = st.form_submit_button("Validar Respuestas")

    if boton_enviar:
        if pregunta_1 == "El ETF VOO (S&P 500)" and pregunta_2 == "Diversificar tu capital en múltiples empresas con una sola operación":
            if not st.session_state.usuario_educado:
                coins_add(100, "Certificación completada: Academia Bursa")
            st.session_state.usuario_educado = True
            st.success("🎉 ¡Felicitaciones! Has aprobado el módulo. La función de Copytrading ya está disponible. +100 monedas")
        else:
            st.session_state.usuario_educado = False
            st.error("❌ Algunas respuestas son incorrectas. Repasa el contenido y vuelve a intentarlo.")

    st.divider()
    st.header("🚀 Panel de Copytrading")

    if st.session_state.usuario_educado:
        st.write("🟢 *Acceso Concedido.* Elige al trader experto que deseas copiar:")

        # Tarjetas apiladas verticalmente (mejor en Android que columnas lado a lado)
        traders_academia = [
            {"nombre": "Laura V.", "iniciales": "LV", "color": TEAL_MID, "enfoque": "ETFs Tecnológicos (QQQ)", "rendimiento": "+14.2%"},
            {"nombre": "Carlos M.", "iniciales": "CM", "color": GOLD, "enfoque": "Valor y Dividendos (VOO)", "rendimiento": "+9.5%"},
        ]
        for t in traders_academia:
            st.markdown(f"""<div class="bursa-card">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                    <div style="width:38px;height:38px;border-radius:50%;background:{t['color']};display:flex;align-items:center;justify-content:center;font-weight:700;color:{NAVY};">{t['iniciales']}</div>
                    <div><b>Trader {t['nombre']}</b><br><span style="font-size:12px;color:#666;">Enfoque: {t['enfoque']}</span></div>
                </div>
            </div>""", unsafe_allow_html=True)
            st.metric("Rendimiento 2026", t["rendimiento"])
            if st.button(f"Copiar Portafolio de {t['nombre']}", key=f"btn_academia_{t['iniciales']}"):
                st.toast(f"¡Orden enviada al broker! Copiando a {t['nombre']}...")
            st.write("")
    else:
        st.warning("🔒 *Función Bloqueada.* Debes completar y aprobar el Quiz de Certificación de arriba para poder activar el Copytrading con dinero simulado.")

# ---------------------------------------------------------------------------
# TAB 3: Descubrir expertos
# ---------------------------------------------------------------------------
with tab_expertos:
    for exp in EXPERTS:
        cap_actual = st.session_state.caps.get(exp["id"], exp["cap_default"])
        risk_class = "risk-alto" if exp["riesgo"] == "alto" else "risk-moderado"

        st.markdown(f"""<div class="bursa-card">
            <div style="display:flex;justify-content:space-between;">
                <div><b>{exp['nombre']}</b><br>
                <span class="{risk_class}" style="font-size:12px;">Riesgo {exp['riesgo']}</span>
                <span style="font-size:12px;color:#888;"> · {exp['seguidores']:,} copiadores</span></div>
                <div style="text-align:right;color:{TEAL_DARK};font-weight:700;">{exp['rentabilidad']}<br>
                <span style="font-size:11px;color:#888;font-weight:400;">3 meses</span></div>
            </div>
        </div>""", unsafe_allow_html=True)

        colA, colB = st.columns(2)
        with colA:
            st.checkbox("Entiendo el riesgo", key=f"chk_{exp['id']}", value=True)
        with colB:
            if st.button(f"Copiar hasta {cap_actual}%", key=f"btn_copiar_{exp['id']}"):
                st.session_state.copied[exp["id"]] = True
                coins_add(5, f"Primera copia a {exp['nombre']}")
                st.success(f"Copiaste a {exp['nombre']} con hasta {cap_actual}% de tu wallet. +5 monedas de bienvenida.")

        if st.session_state.copied.get(exp["id"]) and cap_actual < exp["cap_max"]:
            with st.expander(f"Reto rápido: sube tu límite con {exp['nombre']} · +50 monedas", expanded=False):
                st.write(exp["pregunta"])
                r = st.radio("Opciones", exp["opciones"], index=None, key=f"reto_{exp['id']}", label_visibility="collapsed")
                if st.button("Responder reto", key=f"btn_reto_{exp['id']}"):
                    if r is None:
                        st.error("Elige una opción antes de responder.")
                    elif exp["opciones"].index(r) == exp["correcta"]:
                        nuevo_cap = min(exp["cap_max"], cap_actual + 20)
                        st.session_state.caps[exp["id"]] = nuevo_cap
                        coins_add(50, f"Reto superado: {exp['nombre']}")
                        st.success(f"Correcto. Tu límite con {exp['nombre']} subió a {nuevo_cap}%. +50 monedas")
                    else:
                        st.warning("No es correcto. Puedes intentarlo de nuevo cuando quieras, o saltarlo.")
        st.write("")

# ---------------------------------------------------------------------------
# TAB 3: Rendimiento
# ---------------------------------------------------------------------------
with tab_rendimiento:
    st.markdown("**Valor total del portafolio**")
    st.markdown("### $7,000,000 COP")
    st.markdown(f"<span style='color:{TEAL_DARK};font-weight:600;'>+15.7% en 3 meses</span>", unsafe_allow_html=True)

    # Datos simulados de la evolucion del portafolio (12 semanas)
    valores = [3620, 3680, 3705, 3810, 3790, 3860, 3950, 3990, 4040, 4090, 4140, 4183]
    semanas = list(range(1, len(valores) + 1))

    fig1, ax1 = plt.subplots(figsize=(6, 2.4))
    ax1.fill_between(semanas, valores, min(valores) - 50, color=TEAL_DARK, alpha=0.12)
    ax1.plot(semanas, valores, color=TEAL_DARK, linewidth=2)
    ax1.set_ylim(min(valores) - 50, max(valores) + 50)
    ax1.set_xticks([])
    ax1.set_yticklabels([f"{int(v)}k" for v in ax1.get_yticks()])
    for spine in ["top", "right", "left", "bottom"]:
        ax1.spines[spine].set_visible(False)
    ax1.tick_params(left=False, labelsize=8, colors="#666666")
    ax1.grid(axis="y", color="#eeeeee", linewidth=0.6)
    fig1.tight_layout()
    st.pyplot(fig1, use_container_width=True)
    plt.close(fig1)

    st.markdown("---")
    st.markdown("**Rendimiento por origen**")

    filas = [{"nombre": "Mi inversión directa", "rentabilidad": 12.1, "asignado": None}]
    for exp in EXPERTS:
        if st.session_state.copied.get(exp["id"]):
            cap_actual = st.session_state.caps.get(exp["id"], exp["cap_default"])
            filas.append({"nombre": exp["nombre"], "rentabilidad": float(exp["rentabilidad"].strip("+%")), "asignado": cap_actual})

    colores_barras = [TEAL_DARK, TEAL_MID, TEAL_LIGHT, TEAL_BRIGHT]

    fig2, ax2 = plt.subplots(figsize=(6, 0.6 * len(filas) + 0.4))
    nombres = [f"{f['nombre']}" + (f" · {f['asignado']}%" if f["asignado"] else "") for f in filas]
    valores_barras = [f["rentabilidad"] for f in filas]
    bars = ax2.barh(nombres, valores_barras, color=colores_barras[:len(filas)], height=0.55)
    ax2.bar_label(bars, labels=[f"+{v:.1f}%" for v in valores_barras], padding=4, fontsize=9, color="#333333")
    ax2.invert_yaxis()
    ax2.set_xlim(0, max(valores_barras) * 1.25)
    for spine in ["top", "right", "bottom"]:
        ax2.spines[spine].set_visible(False)
    ax2.spines["left"].set_visible(False)
    ax2.set_xticks([])
    ax2.tick_params(left=False, labelsize=9, colors="#333333")
    fig2.tight_layout()
    st.pyplot(fig2, use_container_width=True)
    plt.close(fig2)

    if len(filas) == 1:
        st.caption("Aún no has copiado a ningún experto — ve a Descubrir expertos para comparar rendimientos.")

    st.caption("Precios de mercado en tiempo real: en la app definitiva se integrarían vía TradingView.")

# ---------------------------------------------------------------------------
# TAB 5: Mercado en vivo (Alpaca API)
# ---------------------------------------------------------------------------
with tab_mercado:
    st.subheader("Datos de Mercado en Tiempo Real vía Alpaca")

    if not ALPACA_CONFIGURADO:
        st.info(
            "Esta sección todavía no está conectada. Agrega ALPACA_API_KEY y "
            "ALPACA_SECRET_KEY en Settings → Secrets de Streamlit Cloud "
            "(o en .streamlit/secrets.toml si corres localmente) para activarla."
        )
    else:
        activo = st.selectbox(
            "Selecciona el ETF o Acción que quieres analizar:",
            ["VOO (ETF S&P 500)", "QQQ (ETF Nasdaq 100)", "AAPL (Apple Inc.)", "TSLA (Tesla)"],
        )
        ticker = activo.split(" ")[0]

        if st.button(f"Consultar precio de {ticker}"):
            headers = {
                "APCA-API-KEY-ID": ALPACA_API_KEY,
                "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
            }
            try:
                url_precio = f"https://data.alpaca.markets/v2/stocks/{ticker}/trades/latest?feed=iex"
                response = requests.get(url_precio, headers=headers, timeout=10)

                if response.status_code == 200:
                    datos = response.json()
                    precio_usd = datos["trade"]["p"]
                    st.metric(label=f"Precio Actual de {ticker}", value=f"${precio_usd:,.2f} USD")
                    st.success("¡Datos conectados correctamente desde el broker internacional!")
                    st.info(f"💡 *Tip Educativo:* Al comprar {ticker} a través de nuestra app, estás adquiriendo una fracción regulada en EE.UU. protegida por la SIPC.")
                else:
                    st.error(f"Error al conectar con Alpaca: Código {response.status_code}")
                    st.json(response.json())
            except Exception as e:
                st.error(f"Ocurrió un error en la conexión: {e}")

        st.caption("Solo lectura de precios. Ninguna orden real se ejecuta desde este prototipo.")

# ---------------------------------------------------------------------------
# TAB 6: Wallet
# ---------------------------------------------------------------------------
with tab_wallet:
    st.markdown(f"""<div class="bursa-card">
        <b>Canjear tokens por descuento VIP</b><br>
        <span style="font-size:13px;color:#666;">{st.session_state.tokens} tokens equivalen a {min(30, st.session_state.tokens)}% de descuento este mes</span>
    </div>""", unsafe_allow_html=True)

    if st.button("Canjear ahora", key="btn_canjear"):
        if st.session_state.tokens >= 5:
            st.session_state.tokens -= 5
            st.session_state.history.insert(0, {"label": "Canje: descuento VIP", "amount": "-5 tokens"})
            st.success("Descuento aplicado a tu próxima suscripción VIP.")
        else:
            st.error("Necesitas al menos 5 tokens para canjear.")

    st.markdown("---")
    st.markdown("**Comprar monedas**")
    st.caption("Prototipo de validación: esto no cobra dinero real, solo mide si comprarías.")

    opciones_paquete = [f"{p['nombre']} · {p['monedas']} monedas · {p['precio']}" for p in PAQUETES]
    elegido = st.radio("Elige un paquete", opciones_paquete, index=None, key="paquete_elegido", label_visibility="collapsed")

    if st.button("Comprar ahora", key="btn_comprar_simulado"):
        if elegido is None:
            st.error("Selecciona un paquete antes de continuar.")
        else:
            idx = opciones_paquete.index(elegido)
            paquete = PAQUETES[idx]
            st.session_state.coins += paquete["monedas"]
            st.session_state.history.insert(0, {
                "label": f"Compra simulada: {paquete['nombre']}",
                "amount": f"+{paquete['monedas']} monedas",
            })
            st.session_state["ultimo_paquete"] = paquete
            st.success(f"Simulación completa: {paquete['monedas']} monedas agregadas a tu wallet.")

    if "ultimo_paquete" in st.session_state:
        p = st.session_state["ultimo_paquete"]
        st.markdown(f"**Pregunta rápida:** ¿pagarías de verdad {p['precio']} por {p['monedas']} monedas?")
        colsi, colno = st.columns(2)
        with colsi:
            if st.button("Sí, lo pagaría", key="wtp_si"):
                st.session_state.wtp_responses.append({"paquete": p["nombre"], "respuesta": "Sí"})
                del st.session_state["ultimo_paquete"]
                st.rerun()
        with colno:
            if st.button("No lo pagaría", key="wtp_no"):
                st.session_state.wtp_responses.append({"paquete": p["nombre"], "respuesta": "No"})
                del st.session_state["ultimo_paquete"]
                st.rerun()

    if st.session_state.wtp_responses:
        st.markdown("---")
        st.markdown("**Respuestas de disposición a pagar (esta sesión)**")
        for r in st.session_state.wtp_responses:
            st.markdown(f"- {r['paquete']}: {r['respuesta']}")

    st.markdown("---")
    st.markdown("**Movimientos recientes**")
    for h in st.session_state.history[:8]:
        st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #eee;font-size:13px;">
            <span>{h['label']}</span><span style="font-weight:600;">{h['amount']}</span>
        </div>""", unsafe_allow_html=True)
