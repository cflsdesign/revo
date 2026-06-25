import React, { useState } from "react";
import { Link } from "react-router-dom";
import api, { BACKEND_URL, formatApiError } from "../lib/api";

const Logo = () => (
  <svg viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M8 22C8 14.268 14.268 8 22 8" stroke="#34D4E7" strokeWidth="2.5" strokeLinecap="round" />
    <path d="M8 22C8 29.732 14.268 36 22 36" stroke="#34D4E7" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="2 3" />
    <text x="18" y="27" fontFamily="Reddit Sans, sans-serif" fontSize="13" fontWeight="700" fill="white">Revo</text>
  </svg>
);

const DownArrow = () => (
  <svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M8 2v9M4 8l4 4 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const Check = () => (
  <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12" /></svg>
);

function getUTM() {
  const p = new URLSearchParams(window.location.search);
  return {
    utm_source: p.get("utm_source"),
    utm_medium: p.get("utm_medium"),
    utm_campaign: p.get("utm_campaign"),
    utm_term: p.get("utm_term"),
    utm_content: p.get("utm_content"),
  };
}

const reasons = [
  { icon: <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />, title: "La Paradoja de la Pre-Venta", body: <>Por qué el <strong>69.35% de los condominios</strong> se venden antes de terminarse, mientras que las casas de alta gama pasan un promedio de <strong>670 días</strong> estancadas en el mercado.</> },
  { icon: <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />, title: "El Declive de los Lotes", body: <>Entiende por qué las ventas de terrenos han caído del <strong>23% al 8%</strong> y por qué los compradores hoy huyen del riesgo de construcción independiente en este nuevo mercado.</> },
  { icon: <><circle cx="12" cy="12" r="10" /><path d="M12 8v4l3 3" /></>, title: "Puntos Dulces de Inversión", body: <>Identificamos el "Epicentro de la Liquidez" donde se concreta el <strong>75.1% de las ventas exitosas</strong> de casas — y el umbral de precio exacto donde la demanda colapsa.</> },
  { icon: <path d="M3 3h7l1 3-3 2a11 11 0 006 6l2-3 3 1v7a1 1 0 01-1 1C8 20 4 8 4 4a1 1 0 011-1z" />, title: "Catalizadores 2026", body: <>El impacto real de la <strong>expansión del Aeropuerto de Puerto Vallarta</strong> y la nueva autopista GDL-PV en la plusvalía de tu activo — con datos desde enero 2026.</> },
  { icon: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />, title: "El Antídoto a la Incertidumbre", body: <>La <strong>Metodología Revo</strong>: control absoluto de capital y ciencia bioclimática perfeccionados durante <strong>30 años</strong> para garantizar la viabilidad financiera de cada proyecto.</> },
  { icon: <><rect x="2" y="3" width="20" height="14" rx="2" ry="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" /></>, title: "Inteligencia del Mercado 4:1", body: <>Con una proporción comprador-vendedor de <strong>4.1:1</strong>, entender las reglas del nuevo mercado ya no es ventaja competitiva — es requisito de supervivencia para el inversor.</> },
];

export default function Landing() {
  const [form, setForm] = useState({ name: "", email: "", phone: "" });
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const scrollToForm = (e) => {
    e.preventDefault();
    document.getElementById("form").scrollIntoView({ behavior: "smooth" });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!form.name.trim()) return setError("Por favor ingresa tu nombre completo.");
    if (!form.email.includes("@")) return setError("Por favor ingresa un correo electrónico válido.");
    setLoading(true);
    try {
      await api.post("/leads", {
        name: form.name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim() || null,
        utm: getUTM(),
        referrer: document.referrer || null,
        page_url: window.location.href,
      });
      setDone(true);
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || "No se pudo completar el registro.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page" data-testid="landing-page">
      {/* HERO */}
      <section className="hero">
        <div className="logo">
          <Logo />
          <span className="logo-text">Revo México</span>
        </div>
        <Link to="/admin/login" className="admin-link" data-testid="admin-access-link">Acceso Admin</Link>

        <div className="hero-inner">
          <div className="eyebrow">Análisis Exclusivo · Riviera Nayarit 2026</div>
          <h1 className="hero-title">
            Sayulita 2026:<br />
            La Nueva Era de la<br />
            <em>Certeza Inmobiliaria</em>
          </h1>
          <p className="hero-subtitle">
            No navegues a ciegas en un mercado con 419% de crecimiento de inventario. Descarga nuestro análisis exclusivo y descubre cómo capitalizar la "Fuga hacia la Certidumbre" en la Riviera Nayarit.
          </p>
          <div className="stat-strip">
            <div className="stat-item"><div className="stat-number">+419%</div><div className="stat-label">Crecimiento de inventario 2022–2025</div></div>
            <div className="stat-item"><div className="stat-number">69.35%</div><div className="stat-label">Condominios vendidos en pre-venta</div></div>
            <div className="stat-item"><div className="stat-number">75.1%</div><div className="stat-label">Ventas en el epicentro de liquidez</div></div>
          </div>
          <a href="#form" className="cta-primary" onClick={scrollToForm} data-testid="hero-cta">
            Obtener mi Análisis de Oportunidades 2026
            <DownArrow />
          </a>
        </div>
      </section>

      <div className="divider"></div>

      {/* REASONS */}
      <section className="section">
        <div className="section-label">Contenido del Reporte</div>
        <h2 className="section-title">¿Por qué necesitas este reporte ahora?</h2>
        <div className="reasons-grid">
          {reasons.map((r, i) => (
            <div className="reason-card" key={i}>
              <div className="reason-icon"><svg viewBox="0 0 24 24">{r.icon}</svg></div>
              <div className="reason-title">{r.title}</div>
              <p className="reason-text">{r.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* QUOTE */}
      <div className="quote-band">
        <p className="quote-text">
          "El mercado exige <em>certidumbre financiera.</em><br />
          La costa exige <em>belleza arquitectónica.</em><br />
          Es el momento de la evolución."
        </p>
        <p className="quote-attr">— Revo México · Sayulita 2026 Strategic Vision</p>
      </div>

      {/* FORM */}
      <section className="section" id="form">
        <div className="form-section">
          <div className="form-left">
            <div className="section-label">Acceso Inmediato</div>
            <h2 className="section-title">Descarga el análisis completo</h2>
            <p className="form-lead">
              Este informe es el resultado de analizar <strong>44 ventas comparables</strong>, cuatro años de datos de mercado y la inteligencia de campo del equipo Revo México. Es gratuito. Es exclusivo. Y puede cambiar tu decisión de inversión.
            </p>
            <div className="form-trust">
              <div className="trust-item"><Check />Descarga inmediata tras registro</div>
              <div className="trust-item"><Check />Sin spam. Tu información está segura</div>
              <div className="trust-item"><Check />Análisis exclusivo basado en datos reales 2022–2026</div>
              <div className="trust-item"><Check />30 años de experiencia en el mercado mexicano</div>
            </div>
          </div>

          <div className="form-right">
            <div className="form-box">
              <h3 className="form-box-title">Accede al Reporte Gratuito</h3>
              <p className="form-box-sub">Ingresa tus datos y descarga al instante.</p>

              {!done ? (
                <form onSubmit={handleSubmit} data-testid="lead-form">
                  <div className="field">
                    <label htmlFor="name">Nombre completo</label>
                    <input type="text" id="name" name="name" placeholder="Tu nombre" autoComplete="name" value={form.name} onChange={onChange} data-testid="lead-name" required />
                  </div>
                  <div className="field">
                    <label htmlFor="email">Correo electrónico</label>
                    <input type="email" id="email" name="email" placeholder="tu@correo.com" autoComplete="email" value={form.email} onChange={onChange} data-testid="lead-email" required />
                  </div>
                  <div className="field">
                    <label htmlFor="phone">Teléfono (WhatsApp)</label>
                    <input type="tel" id="phone" name="phone" placeholder="+52 322 000 0000" autoComplete="tel" value={form.phone} onChange={onChange} data-testid="lead-phone" />
                  </div>

                  <button className="submit-btn" type="submit" disabled={loading} data-testid="lead-submit">
                    {loading ? "Procesando..." : "Obtener mi Análisis de Oportunidades 2026"}
                    {!loading && <DownArrow />}
                  </button>

                  {error && <p className="error-note" data-testid="lead-error">{error}</p>}

                  <p className="privacy-note">
                    Al registrarte aceptas recibir información de Revo México.<br />
                    Respetamos tu privacidad. Sin spam, nunca.
                  </p>
                </form>
              ) : (
                <div className="success-state" data-testid="lead-success">
                  <div className="success-icon"><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12" /></svg></div>
                  <h4 className="success-title">¡Tu reporte está listo!</h4>
                  <p className="success-text">Gracias por tu interés en el mercado de Sayulita. Haz clic abajo para descargar tu análisis exclusivo.</p>
                  <a href={`${BACKEND_URL}/api/download/report`} className="download-btn" target="_blank" rel="noreferrer" data-testid="download-report-btn">
                    Descargar Análisis 2026
                    <DownArrow />
                  </a>
                  <p className="privacy-note" style={{ marginTop: 20 }}>Un asesor de Revo México se pondrá en contacto contigo pronto.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="footer">
        <div className="footer-logo"><Logo /><span>Revo México</span></div>
        <p className="footer-text">© 2026 Revo México. Todos los derechos reservados.</p>
        <div className="footer-contact">
          <a href="mailto:axel.olaf@revo.com.mx">axel.olaf@revo.com.mx</a><br />
          +52 1 322 728 4435
        </div>
      </footer>
    </div>
  );
}
