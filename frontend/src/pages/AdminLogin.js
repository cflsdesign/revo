import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { formatApiError } from "../lib/api";

export default function AdminLogin() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await api.post("/auth/login", { email, password });
      localStorage.setItem("revo_token", data.token);
      localStorage.setItem("revo_user", JSON.stringify(data.user));
      navigate("/admin");
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || "Error al iniciar sesión.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="login-wrap">
        <div className="login-box" data-testid="login-box">
          <div className="login-logo">
            <svg viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M8 22C8 14.268 14.268 8 22 8" stroke="#34D4E7" strokeWidth="2.5" strokeLinecap="round" />
              <path d="M8 22C8 29.732 14.268 36 22 36" stroke="#34D4E7" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="2 3" />
              <text x="18" y="27" fontFamily="Reddit Sans, sans-serif" fontSize="13" fontWeight="700" fill="white">Revo</text>
            </svg>
            <span>Revo México</span>
          </div>
          <h3 className="form-box-title">Panel de Leads</h3>
          <p className="form-box-sub">Ingresa con tus credenciales de administrador.</p>
          <form onSubmit={handleLogin} data-testid="login-form">
            <div className="field">
              <label htmlFor="login-email">Correo</label>
              <input type="email" id="login-email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="admin@revo.mx" data-testid="login-email" required />
            </div>
            <div className="field">
              <label htmlFor="login-password">Contraseña</label>
              <input type="password" id="login-password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" data-testid="login-password" required />
            </div>
            <button className="submit-btn" type="submit" disabled={loading} data-testid="login-submit">
              {loading ? "Ingresando..." : "Entrar"}
            </button>
            {error && <p className="error-note" data-testid="login-error">{error}</p>}
          </form>
        </div>
      </div>
    </div>
  );
}
