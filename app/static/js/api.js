// Lightweight API helper for authenticated requests.
const API = (() => {
  const base = '/api';

  function getToken() {
    return localStorage.getItem('jwt');
  }

  function authHeaders(extra = {}) {
    const token = getToken();
    return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
  }

  async function request(path, { method = 'GET', headers = {}, body } = {}) {
    const res = await fetch(`${base}${path}`, {
      method,
      headers: authHeaders({ 'Content-Type': 'application/json', ...headers }),
      body: body ? JSON.stringify(body) : undefined,
    });
    if (res.status === 204) return null;
    const text = await res.text();
    let data;
    try { data = text ? JSON.parse(text) : null; } catch { data = text; }
    if (!res.ok) throw new Error(data?.detail || res.statusText);
    return data;
  }

  async function login(username, password) {
    // Custom JWT auth expects form-encoded credentials at /api/auth/login
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);
    const res = await fetch('/api/auth/jwt/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
    if (!res.ok) {
      let detail; try { detail = (await res.json())?.detail; } catch { /* ignore */ }
      throw new Error(detail || 'Login failed');
    }
    const auth = await res.json();
    if (auth?.access_token) localStorage.setItem('jwt', auth.access_token);
    return auth;
  }

  // Peers
  const listPeers = () => request('/peers');
  const createPeer = (serverInterface, payload) => request(`/servers/${serverInterface}/peers/`, { method: 'POST', body: payload });
  const updatePeer = (serverInterface, username, payload) => request(`/servers/${serverInterface}/peers/${username}`, { method: 'PUT', body: payload });
  const deletePeer = (serverInterface, username) => request(`/servers/${serverInterface}/peers/${username}`, { method: 'DELETE' });
  const updateAllowedIps = (username, allowed_ips) => request(`/peers/${username}/allowed_ips?allowed_ips=${encodeURIComponent(allowed_ips)}`, { method: 'PUT' });

  // Servers
  const listServers = async () => {
    try { return await request('/servers/'); } catch { return []; }
  };
  const createServer = (payload) => request('/servers/', { method: 'POST', body: payload });
  const updateServer = (iface, payload) => request(`/servers/${encodeURIComponent(iface)}`, { method: 'PUT', body: payload });
  const deleteServer = (iface) => request(`/servers/${encodeURIComponent(iface)}`, { method: 'DELETE' });
  const persistServerConfig = async (iface) => {
    const res = await fetch(`/api/servers/${encodeURIComponent(iface)}/persist`, { method: 'POST', headers: authHeaders() });
    if (!res.ok) throw new Error('Persist failed');
    return await res.blob();
  };

  // Peer config persistence
  const persistPeerConfig = async (username, customAllowedIps) => {
    let url = `/api/peers/${encodeURIComponent(username)}/persist`;
    if (customAllowedIps) url += `?custom_allowed_ips=${encodeURIComponent(customAllowedIps)}`;
    const res = await fetch(url, { method: 'POST', headers: authHeaders() });
    if (!res.ok) throw new Error('Persist failed');
    return await res.blob();
  };

  const nextIp = async (server_interface) => {
    const res = await fetch(`/api/next_ip?server_interface=${encodeURIComponent(server_interface)}`, { headers: authHeaders() });
    if (!res.ok) return '';
    return (await res.text()) || '';
  };

  const currentUser = async () => {
    const res = await fetch('/api/auth/me', { headers: authHeaders() });
    if (!res.ok) throw new Error('Not authenticated');
    return await res.json();
  };

  return { login, listPeers, createPeer, updatePeer, deletePeer, updateAllowedIps, listServers, createServer, updateServer, deleteServer, persistServerConfig, persistPeerConfig, nextIp, currentUser, getToken };
})();

window.API = API;
