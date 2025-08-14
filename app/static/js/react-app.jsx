/* global React, ReactDOM, API */
const { useState, useEffect, useCallback } = React;

function usePathRouter() {
  const [path, setPath] = React.useState(window.location.pathname);
  React.useEffect(()=>{
    const handler = () => setPath(window.location.pathname);
    window.addEventListener('popstate', handler);
    return () => window.removeEventListener('popstate', handler);
  },[]);
  const push = (to) => { if (to!==path){ window.history.pushState({}, '', to); setPath(to);} };
  return { path, push };
}

function Sidebar({ open, toggle, path, go, user, logout }) {
  const [vpnOpen, setVpnOpen] = React.useState(true);
  return (
    <aside className={"sidebar" + (open?" open":"")}> 
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:'.5rem'}}>
        <button className="brand" type="button" onClick={()=>go('/')}>Firewallo</button>
        <button className="burger" type="button" onClick={toggle} aria-label="Close menu">✕</button>
      </div>
      <div className="menu-section">
        <div className="menu-heading">Navigation</div>
        <button className={"menu-item" + (path.startsWith('/plugins/')? ' active':'')} onClick={()=>setVpnOpen(o=>!o)}>VPN <span>{vpnOpen?'▾':'▸'}</span></button>
        {vpnOpen && (
          <div className="submenu">
            <button className={"menu-item" + (path.startsWith('/plugins/wireguard')? ' active':'')} onClick={()=>go('/plugins/wireguard')}>WireGuard</button>
            {/* Future VPN plugins can be added here */}
          </div>
        )}
      </div>
      <div className="menu-section" style={{marginTop:'auto'}}>
        {user && (
          <div className="user-block">
            <strong>{user.email}</strong><br/>
            {user.is_superuser && <span>Superuser<br/></span>}
            <span>{user.is_verified? 'Verified':'Unverified'}</span>
          </div>
        )}
        <button className="logout-btn" type="button" onClick={logout}>Logout</button>
      </div>
    </aside>
  );
}

function Layout({ children, path, go, user, logout }) {
  // Do not render layout shell on login (standalone template handles it); safeguard in case of SPA navigation
  if (path === '/login') return <>{children}</>;
  const [open, setOpen] = React.useState(false);
  const toggle = ()=> setOpen(o=>!o);
  React.useEffect(()=>{ setOpen(false); }, [path]);
  return (
    <div className="app-shell">
      <Sidebar open={open} toggle={toggle} path={path} go={go} user={user} logout={logout} />
      <div className="layout" style={{flex:1, marginLeft:'230px'}}>
        <header className="app-header floating-header" style={{display:'flex',gap:'.75rem'}}>
          <button className="burger floating-burger" type="button" aria-label="Menu" onClick={toggle}>☰</button>
          <h1 style={{fontSize:'1rem',margin:0,fontWeight:500}}>Firewallo</h1>
        </header>
        <main className="content">{children}</main>
        <footer className="footer">© {new Date().getFullYear()} Firewallo</footer>
      </div>
    </div>
  );
}

function AuthStatus({ go }) {
  const token = API.getToken();
  return token ? <button onClick={()=>{ localStorage.removeItem('jwt'); go('/login'); }}>Logout</button> : null;
}

function Login({ onSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const submit = async (e) => {
    e.preventDefault(); setError(''); setLoading(true);
    try { await API.login(username, password); onSuccess(); } catch (err) { setError(err.message); } finally { setLoading(false); }
  };
  return (
    <div className="panel">
      <h2>Login</h2>
      {error && <div className="error">{error}</div>}
      <form onSubmit={submit}>
        <label>Username<input value={username} onChange={e=>setUsername(e.target.value)} required /></label>
        <label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} required /></label>
        <button type="submit" disabled={loading}>{loading? 'Logging in...' : 'Login'}</button>
      </form>
    </div>
  );
}

function WelcomePage() {
  return (
    <div className="panel">
      <h2>Welcome to Firewallo</h2>
      <p>This is your central dashboard. Use the sidebar to access VPN plugins and manage your infrastructure.</p>
      <p>Select <strong>VPN &gt; WireGuard</strong> to manage WireGuard servers and peers.</p>
    </div>
  );
}

// WireGuard main route now directly shows ServersPage (server list) with extra shortcuts.

function PeersTable({ peers, onEdit, onDelete, onAllowed }) {
  if (!peers.length) return <div className="empty">No peers yet.</div>;
  return (
    <table className="data-table">
      <thead><tr><th>User</th><th>Server</th><th>Private IP</th><th>Allowed IPs</th><th>Endpoint</th><th>Actions</th></tr></thead>
      <tbody>
        {peers.map(p => (
          <tr key={`${p.server_interface}:${p.username}`}>
            <td>{p.username}</td>
            <td>{p.server_interface}</td>
            <td>{p.private_ip}</td>
            <td>{p.allowed_ips}</td>
            <td>{p.endpoint || '-'}</td>
            <td className="actions">
              <button onClick={() => onAllowed(p)}>Allowed IPs</button>
              <button onClick={() => onEdit(p)}>Edit</button>
              <button className="danger" onClick={() => onDelete(p)}>Delete</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function PeersPage({ onNavigate }) {
  const [peers, setPeers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { setPeers(await API.listPeers()); } catch (e) { setError(e.message); } finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);
  const del = async (p) => {
    if (!confirm(`Delete peer ${p.username}?`)) return;
    try { await API.deletePeer(p.server_interface, p.username); await load(); } catch (e){ alert(e.message); }
  };
  return (
    <div>
      <h2>Peers</h2>
      {loading && <div className="loading"/>}
      {error && <div className="error">{error}</div>}
      {!loading && !error && <PeersTable peers={peers} onDelete={del} onEdit={(p)=>onNavigate('edit', p)} onAllowed={(p)=>onNavigate('allowed', p)} />}
    </div>
  );
}

function AddPeerPage({ onNavigate }) {
  const [state, setState] = useState({ server_interface:'', username:'', private_ip:'', allowed_ips:'', endpoint:'', group:'', persistent_keepalive:'' });
  const [servers, setServers] = useState([]);
  const [saving, setSaving] = useState(false); const [error, setError] = useState(''); const [success, setSuccess] = useState(null);
  // Load servers and pre-populate server + next IP
  React.useEffect(()=>{ (async()=>{ try {
      const list = await API.listServers();
      setServers(list);
      if(list.length){
        const firstIface = list[0].interface;
        // set server then fetch next ip
        let next = '';
        try { next = await API.nextIp(firstIface); } catch { /* ignore */ }
        setState(s=>({ ...s, server_interface: firstIface, private_ip: next? `${next}/${list[0].address.split('/')[1]}` : '' }));
      }
    } catch(e){ console.warn('Failed to load servers list', e); }
  })(); },[]);
  // Whenever server changes and private_ip empty, fetch next ip
  React.useEffect(()=>{ (async()=>{
    if(!state.server_interface) return;
    if(state.private_ip) return; // already filled
    try {
      const srv = servers.find(s=>s.interface===state.server_interface);
      const baseMask = srv? srv.address.split('/')[1] : '32';
      const next = await API.nextIp(state.server_interface);
      if(next) setState(s=>({ ...s, private_ip: `${next}/${baseMask}` }));
    } catch { /* ignore */ }
  })(); },[state.server_interface]);
  const change = (e)=> setState(s=>({...s,[e.target.name]:e.target.value}));
  const changeServer = async (e)=>{
    const iface = e.target.value;
    setState(s=>({...s, server_interface: iface, private_ip:'' }));
  };
  const submit = async (e)=>{
    e.preventDefault(); setSaving(true); setError(''); setSuccess(null);
    try {
      const payload = { ...state, persistent_keepalive: state.persistent_keepalive? Number(state.persistent_keepalive): null };
      await API.createPeer(state.server_interface, payload);
      setSuccess('Peer created');
      setTimeout(()=> onNavigate('peers'), 800);
    } catch(e){ setError(e.message);} finally { setSaving(false); }
  };
  return (
    <div className="panel">
      <h2>Add Peer</h2>
      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}
      <form onSubmit={submit} className="two-col">
        <label>Server Interface{servers.length ? (
          <select name="server_interface" value={state.server_interface} onChange={changeServer}>{servers.map(s=><option key={s.interface} value={s.interface}>{s.interface}</option>)}</select>
        ) : (<input name="server_interface" value={state.server_interface} onChange={changeServer} required />)}</label>
        <label>Username<input name="username" value={state.username} onChange={change} required /></label>
        <label>Private IP<input name="private_ip" value={state.private_ip} onChange={change} placeholder="auto" required />
          {!state.private_ip && <small style={{color:'var(--muted)'}}> Resolving next IP...</small>}
        </label>
        <label>Allowed IPs<input name="allowed_ips" value={state.allowed_ips} onChange={change} required /></label>
        <label>Endpoint<input name="endpoint" value={state.endpoint} onChange={change} /></label>
        <label>Group<input name="group" value={state.group} onChange={change} /></label>
        <label>Persistent Keepalive<input name="persistent_keepalive" value={state.persistent_keepalive} onChange={change} type="number" min="0" /></label>
        <div className="full-row">
          <button disabled={saving}>{saving? 'Saving...' : 'Create Peer'}</button>
        </div>
      </form>
    </div>
  );
}

function EditAllowedIPs({ peer, onNavigate }) {
  const [allowed, setAllowed] = useState(peer.allowed_ips);
  const [saving, setSaving] = useState(false);
  const submit = async (e)=>{ e.preventDefault(); setSaving(true); try { await API.updateAllowedIps(peer.username, allowed); onNavigate('peers'); } catch(err){ alert(err.message);} finally { setSaving(false);} };
  return (
    <div className="panel">
      <h2>Allowed IPs: {peer.username}</h2>
      <form onSubmit={submit}>
        <label>Allowed IPs<input value={allowed} onChange={e=>setAllowed(e.target.value)} required /></label>
        <button disabled={saving}>{saving? 'Saving...' : 'Update'}</button>
      </form>
    </div>
  );
}

function EditPeer({ peer, onNavigate }) {
  const [state, setState] = useState({ ...peer });
  const [saving, setSaving] = useState(false);
  const change = (e)=> setState(s=>({...s,[e.target.name]:e.target.value}));
  const submit = async (e)=>{ e.preventDefault(); setSaving(true); try { await API.updatePeer(peer.server_interface, peer.username, { ...state }); onNavigate('peers'); } catch(err){ alert(err.message);} finally { setSaving(false);} };
  return (
    <div className="panel">
      <h2>Edit Peer: {peer.username}</h2>
      <form onSubmit={submit} className="two-col">
        <label>Endpoint<input name="endpoint" value={state.endpoint||''} onChange={change} /></label>
        <label>Group<input name="group" value={state.group||''} onChange={change} /></label>
        <label>Allowed IPs<input name="allowed_ips" value={state.allowed_ips} onChange={change} required /></label>
        <label>Persistent Keepalive<input name="persistent_keepalive" type="number" value={state.persistent_keepalive||''} onChange={change} /></label>
        <div className="full-row"><button disabled={saving}>{saving? 'Saving...' : 'Save'}</button></div>
      </form>
    </div>
  );
}

function ServersPage({ go }) {
  const [servers, setServers] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');
  const [showForm, setShowForm] = React.useState(false);
  const [editing, setEditing] = React.useState(null);
  const [form, setForm] = React.useState({ interface:'', listen_port:'51820', address:'10.0.0.1/24', mtu:'1420' });
  // Peers modal state
  const [peersServer, setPeersServer] = React.useState(null); // server object
  const [peers, setPeers] = React.useState([]);
  const [peersLoading, setPeersLoading] = React.useState(false);
  const [peersError, setPeersError] = React.useState('');
  const [addingPeer, setAddingPeer] = React.useState(false);
  const [editingPeer, setEditingPeer] = React.useState(null); // username
  const emptyPeer = { username:'', private_ip:'', allowed_ips:'', endpoint:'', group:'', persistent_keepalive:'' };
  const [peerForm, setPeerForm] = React.useState(emptyPeer);
  const load = React.useCallback(async ()=>{ setLoading(true); setError(''); try { setServers(await API.listServers()); } catch(e){ setError(e.message);} finally { setLoading(false);} },[]);
  React.useEffect(()=>{ load(); },[load]);
  const change = e=> setForm(f=>({...f,[e.target.name]:e.target.value}));
  const startCreate = ()=>{ setEditing(null); setForm({ interface:'', listen_port:'51820', address:'10.0.0.1/24', mtu:'1420' }); setShowForm(true); };
  const startEdit = (s)=>{ setEditing(s.interface); setForm({ interface:s.interface, listen_port:String(s.listen_port), address:s.address, mtu:String(s.mtu) }); setShowForm(true); };
  const submit = async (e)=>{ e.preventDefault(); try { const payload={ interface:form.interface, listen_port:Number(form.listen_port), address:form.address, mtu:Number(form.mtu) }; if (editing) { await API.updateServer(editing, payload); } else { await API.createServer(payload); } setShowForm(false); await load(); } catch(err){ alert(err.message);} };
  const del = async (s)=>{
    if(!confirm(`Delete server ${s.interface}?`)) return;
    try {
      await API.deleteServer(s.interface);
      await load();
    } catch(err){
      alert(err.message);
    }
  };
  const persist = async (s)=>{ try { const blob= await API.persistServerConfig(s.interface); const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download=`${s.interface}.conf`; a.click(); URL.revokeObjectURL(url);} catch(err){ alert(err.message);} };
  // Peers modal helpers
  const openPeers = async (server)=>{
    setPeersServer(server);
    setPeers([]); setPeersError(''); setPeersLoading(true);
    try {
      const all = await API.listPeers();
      setPeers(all.filter(p=>p.server_interface === server.interface));
    } catch(e){ setPeersError(e.message);} finally { setPeersLoading(false);} }
  const closePeers = ()=>{ setPeersServer(null); setAddingPeer(false); setEditingPeer(null); setPeerForm(emptyPeer); };
  const peerChange = e=> setPeerForm(f=>({...f,[e.target.name]:e.target.value}));
  const submitPeer = async (e)=>{ 
    e.preventDefault(); 
    if(!peersServer) return; 
    try { 
      const payload={ ...peerForm, persistent_keepalive: peerForm.persistent_keepalive? Number(peerForm.persistent_keepalive): null }; 
      await API.createPeer(peersServer.interface, payload); 
      setPeerForm(emptyPeer); 
      setAddingPeer(false); 
      await openPeers(peersServer); 
    } catch(err){ 
      alert(err.message);
    } 
  };
  const startEditPeer = (p)=>{ setEditingPeer(p.username); setPeerForm({ ...p }); };
  const savePeerEdit = async (e)=>{ 
    e.preventDefault(); 
    if(!peersServer) return; 
    try { 
      await API.updatePeer(peersServer.interface, editingPeer, { ...peerForm }); 
      setEditingPeer(null); 
      setPeerForm(emptyPeer); 
      await openPeers(peersServer); 
    } catch(err){ 
      alert(err.message);
    } 
  };
  const cancelPeerEdit = ()=>{ setEditingPeer(null); setPeerForm(emptyPeer); };
  const deletePeer = async (p)=>{ 
    if(!confirm(`Delete peer ${p.username}?`)) return; 
    try { 
      await API.deletePeer(peersServer.interface, p.username); 
      await openPeers(peersServer); 
    } catch(err){ 
      alert(err.message);
    } 
  };
  const updateAllowed = async (p)=>{ 
    const val = prompt('Allowed IPs', p.allowed_ips); 
    if(val==null) return; 
    try { 
      await API.updatePeer(peersServer.interface, p.username, { ...p, allowed_ips:val }); 
      await openPeers(peersServer); 
    } catch(err){ 
      alert(err.message);
    } 
  };
  // When opening Add Peer form, auto-populate next IP
  React.useEffect(()=>{ (async()=>{
    if(!addingPeer || !peersServer) return;
    if(peerForm.private_ip) return; // already set
    try {
      const next = await API.nextIp(peersServer.interface);
      if(next){
        // derive mask from server address
        const mask = peersServer.address.split('/')[1] || '32';
        setPeerForm(f=>({...f, private_ip: `${next}/${mask}`}));
      }
    } catch{ /* ignore */ }
  })(); }, [addingPeer, peersServer]);
  return (
    <div>
      <h2>WireGuard Servers</h2>
      <div style={{display:'flex', flexWrap:'wrap', gap:'.5rem', marginBottom:'1rem'}}>
        <button type="button" onClick={startCreate}>New Server</button>
        <button type="button" onClick={load}>Refresh</button>
      </div>
      {loading && <div className="loading"/>}
      {error && <div className="error">{error}</div>}
      {!loading && !servers.length && <div className="empty">No servers defined.</div>}
      {!loading && servers.length>0 && (
        <table className="data-table">
          <thead><tr><th>Interface</th><th>Address</th><th>Port</th><th>MTU</th><th>Public Key</th><th>Actions</th></tr></thead>
          <tbody>
            {servers.map(s=> (
              <tr key={s.interface}>
                <td>{s.interface}</td><td>{s.address}</td><td>{s.listen_port}</td><td>{s.mtu}</td><td style={{fontSize:'.6rem',maxWidth:'160px',overflow:'hidden',textOverflow:'ellipsis'}}>{s.public_key}</td>
                <td className="actions">
                  <button onClick={()=>openPeers(s)}>Peers</button>
                  <button onClick={()=>startEdit(s)}>Edit</button>
                  <button onClick={()=>persist(s)}>Config</button>
                  <button className="danger" onClick={()=>del(s)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {showForm && (
        <div className="modal-overlay">
          <dialog open className="modal">
            <button className="modal-close" aria-label="Close" onClick={()=>setShowForm(false)}>✕</button>
            <h3 style={{marginTop:0}}>{editing? 'Edit Server' : 'Create Server'}</h3>
            <form onSubmit={submit} className="two-col" style={{marginTop:'1rem'}}>
              <label>Interface<input name="interface" value={form.interface} onChange={change} required disabled={!!editing} /></label>
              <label>Listen Port<input name="listen_port" value={form.listen_port} onChange={change} required type="number" min="1" /></label>
              <label>Address<input name="address" value={form.address} onChange={change} required /></label>
              <label>MTU<input name="mtu" value={form.mtu} onChange={change} required type="number" min="576" /></label>
              <div className="full-row" style={{display:'flex', gap:'.5rem'}}>
                <button type="submit">{editing? 'Save' : 'Create'}</button>
                <button type="button" onClick={()=>setShowForm(false)}>Cancel</button>
              </div>
            </form>
          </dialog>
        </div>
      )}
      {peersServer && (
        <div className="modal-overlay">
          <dialog open className="modal">
            <button className="modal-close" aria-label="Close" onClick={closePeers}>✕</button>
            <h3>Peers for {peersServer.interface}</h3>
            {peersLoading && <div className="loading"/>}
            {peersError && <div className="error" style={{marginTop:'1rem'}}>{peersError}</div>}
            {!peersLoading && !peersError && (
              <>
                <div style={{display:'flex', gap:'.5rem', flexWrap:'wrap', marginTop:'.75rem'}}>
                  <button type="button" onClick={()=>{ setAddingPeer(a=>!a); setEditingPeer(null); setPeerForm(emptyPeer); }}>{addingPeer? 'Close New Peer Form' : 'Add Peer'}</button>
                  <button type="button" onClick={()=>openPeers(peersServer)}>Refresh</button>
                </div>
                {addingPeer && (
                  <form onSubmit={submitPeer} className="two-col inline-form" style={{marginTop:'1rem'}}>
                    <label>Username<input name="username" value={peerForm.username} onChange={peerChange} required /></label>
                    <label>Private IP<input name="private_ip" value={peerForm.private_ip} onChange={peerChange} placeholder="10.0.0.x/24" required /></label>
                    <label>Allowed IPs<input name="allowed_ips" value={peerForm.allowed_ips} onChange={peerChange} required /></label>
                    <label>Endpoint<input name="endpoint" value={peerForm.endpoint} onChange={peerChange} /></label>
                    <label>Group<input name="group" value={peerForm.group} onChange={peerChange} /></label>
                    <label>Persistent Keepalive<input name="persistent_keepalive" value={peerForm.persistent_keepalive} onChange={peerChange} type="number" min="0" /></label>
                    <div className="full-row" style={{display:'flex', gap:'.5rem'}}>
                      <button type="submit">Create Peer</button>
                      <button type="button" onClick={()=>{ setAddingPeer(false); setPeerForm(emptyPeer); }}>Cancel</button>
                    </div>
                  </form>
                )}
                <div style={{overflowX:'auto', marginTop:'1rem'}}>
                  <table className="data-table">
                    <thead><tr><th>User</th><th>Private IP</th><th>Allowed IPs</th><th>Endpoint</th><th>Group</th><th>Keepalive</th><th>Actions</th></tr></thead>
                    <tbody>
                      {peers.map(p=> (
                        <tr key={p.username}>
                          <td>{editingPeer===p.username ? (
                            <input name="username" value={peerForm.username} disabled />
                          ) : p.username}</td>
                          <td>{editingPeer===p.username ? (
                            <input name="private_ip" value={peerForm.private_ip} onChange={peerChange} />
                          ) : p.private_ip}</td>
                          <td>{editingPeer===p.username ? (
                            <input name="allowed_ips" value={peerForm.allowed_ips} onChange={peerChange} />
                          ) : p.allowed_ips}</td>
                          <td>{editingPeer===p.username ? (
                            <input name="endpoint" value={peerForm.endpoint} onChange={peerChange} />
                          ) : (p.endpoint||'-')}</td>
                          <td>{editingPeer===p.username ? (
                            <input name="group" value={peerForm.group} onChange={peerChange} />
                          ) : (p.group||'-')}</td>
                          <td>{editingPeer===p.username ? (
                            <input name="persistent_keepalive" type="number" value={peerForm.persistent_keepalive} onChange={peerChange} />
                          ) : (p.persistent_keepalive||'-')}</td>
                          <td className="actions">
                            {editingPeer===p.username ? (
                              <>
                                <button onClick={savePeerEdit}>Save</button>
                                <button type="button" onClick={cancelPeerEdit}>Cancel</button>
                              </>
                            ) : (
                              <>
                                <button onClick={()=>startEditPeer(p)}>Edit</button>
                                <button onClick={()=>updateAllowed(p)}>Allowed IPs</button>
                                <button className="danger" onClick={()=>deletePeer(p)}>Delete</button>
                              </>
                            )}
                          </td>
                        </tr>
                      ))}
                      {!peers.length && (
                        <tr><td colSpan="7" style={{textAlign:'center',padding:'1rem',color:'var(--muted)'}}>No peers yet.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </dialog>
        </div>
      )}
    </div>
  );
}

function ErrorBoundary({ children }) {
  const [err, setErr] = React.useState(null);
  if (err) return <div className="panel"><h2>UI Error</h2><pre style={{whiteSpace:'pre-wrap'}}>{String(err)}</pre></div>;
  return <React.Suspense fallback={<div className="loading"/>}>{React.cloneElement(children, { onError:setErr })}</React.Suspense>;
}

// Mount application if root exists
const rootEl = document.getElementById('app-root');
if (rootEl) {
  ReactDOM.createRoot(rootEl).render(
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  );
}

function App() {
  const { path, push } = usePathRouter();
  const go = (p)=>{ push(p); };
  const token = API.getToken();
  const [user,setUser] = React.useState(null);
  React.useEffect(()=>{ (async()=>{ if(token){ try { setUser(await API.currentUser()); } catch{ setUser(null);} } else setUser(null); })(); },[token]);
  const logout = ()=>{ localStorage.removeItem('jwt'); push('/login'); };
  React.useEffect(()=>{
    if (!token && path !== '/login') {
      window.location.href = '/login';
    }
  }, [token, path]);
  let page;
  if (!token) {
    page = null; // handled by redirect/login template
  } else {
    // authenticated route resolution using switch for style compliance
    switch (path) {
      case '/':
        page = <WelcomePage />; break;
      case '/plugins/wireguard':
        page = <ServersPage go={go} />; break; // main wireguard page shows servers list
      case '/plugins/wireguard/peers':
        page = <PeersPage onNavigate={()=>{}} />; break;
      case '/plugins/wireguard/servers':
        page = <ServersPage go={go} />; break;
      case '/plugins/wireguard/peers/add':
        page = <AddPeerPage onNavigate={()=>go('/plugins/wireguard/peers')} />; break;
      default:
        page = <PeersPage onNavigate={()=>{}} />;
    }
  }
  return <Layout path={path} go={go} user={user} logout={logout}>{page}</Layout>;
}
