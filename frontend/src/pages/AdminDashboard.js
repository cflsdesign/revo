import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import api, { API } from "../lib/api";

function fmtDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("es-MX", {
      day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({ total: 0, today: 0, week: 0, with_phone: 0 });
  const [leads, setLeads] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const user = JSON.parse(localStorage.getItem("revo_user") || "{}");

  const logout = () => {
    localStorage.removeItem("revo_token");
    localStorage.removeItem("revo_user");
    navigate("/admin/login");
  };

  const load = useCallback(async (q) => {
    setLoading(true);
    try {
      const [s, l] = await Promise.all([
        api.get("/leads/stats"),
        api.get("/leads", { params: { search: q || undefined, limit: 200 } }),
      ]);
      setStats(s.data);
      setLeads(l.data.items);
      setTotal(l.data.total);
    } catch (err) {
      if (err.response?.status === 401) logout();
    } finally {
      setLoading(false);
    }
  }, []); // eslint-disable-line

  useEffect(() => { load(""); }, [load]);

  const handleSearch = (e) => {
    e.preventDefault();
    load(search);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("¿Eliminar este lead?")) return;
    await api.delete(`/leads/${id}`);
    load(search);
  };

  const exportCsv = () => {
    const token = localStorage.getItem("revo_token");
    window.open(`${API}/leads/export?token=${encodeURIComponent(token)}`, "_blank");
  };

  return (
    <div className="page">
      <div className="admin-wrap" data-testid="admin-dashboard">
        <div className="admin-topbar">
          <div>
            <div className="admin-title">Repositorio de <em>Leads</em> · Revo México</div>
            <p className="muted" style={{ fontSize: 13, marginTop: 6 }}>Sesión: {user.email || "Admin"}</p>
          </div>
          <div className="admin-actions">
            <button className="btn btn-accent" onClick={exportCsv} data-testid="export-csv-btn">Exportar CSV</button>
            <button className="btn" onClick={() => load(search)} data-testid="refresh-btn">Actualizar</button>
            <button className="btn btn-danger" onClick={logout} data-testid="logout-btn">Salir</button>
          </div>
        </div>

        <div className="stats-grid">
          <div className="stat-box"><div className="num" data-testid="stat-total">{stats.total}</div><div className="lbl">Total de leads</div></div>
          <div className="stat-box"><div className="num" data-testid="stat-today">{stats.today}</div><div className="lbl">Hoy</div></div>
          <div className="stat-box"><div className="num" data-testid="stat-week">{stats.week}</div><div className="lbl">Últimos 7 días</div></div>
          <div className="stat-box"><div className="num" data-testid="stat-phone">{stats.with_phone}</div><div className="lbl">Con teléfono</div></div>
        </div>

        <form className="search-bar" onSubmit={handleSearch}>
          <input type="search" placeholder="Buscar por nombre, correo o teléfono..." value={search} onChange={(e) => setSearch(e.target.value)} data-testid="search-input" />
        </form>

        <div className="table-wrap">
          <table className="leads">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Correo</th>
                <th>Teléfono</th>
                <th>Campaña / Origen</th>
                <th>Fecha</th>
                <th></th>
              </tr>
            </thead>
            <tbody data-testid="leads-tbody">
              {loading ? (
                <tr><td colSpan={6} className="empty-state">Cargando...</td></tr>
              ) : leads.length === 0 ? (
                <tr><td colSpan={6} className="empty-state">Aún no hay registros{search ? " para esta búsqueda" : ""}.</td></tr>
              ) : (
                leads.map((l) => {
                  const utm = l.utm || {};
                  const origin = utm.utm_campaign || utm.utm_source;
                  return (
                    <tr key={l.id} data-testid="lead-row">
                      <td className="cell-name">{l.name}</td>
                      <td>{l.email}</td>
                      <td>{l.phone || <span className="muted">—</span>}</td>
                      <td>
                        {origin ? <span className="tag">{origin}</span> : <span className="muted">Directo</span>}
                        {utm.utm_medium && <div className="muted" style={{ fontSize: 11, marginTop: 4 }}>{utm.utm_medium}</div>}
                      </td>
                      <td className="muted">{fmtDate(l.created_at)}</td>
                      <td><button className="del-btn" onClick={() => handleDelete(l.id)} data-testid="delete-lead-btn">Eliminar</button></td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
        <p className="muted" style={{ fontSize: 12, marginTop: 16 }}>Mostrando {leads.length} de {total} registros.</p>
      </div>
    </div>
  );
}
