import { useState, useEffect, useRef } from 'react'
import { Container, Grid, Typography, Paper, Alert, Box } from '@mui/material';
import DynamicWidget from './components/DynamicWidget';
import ControlPanel from './components/ControlPanel';
import ChatWidget from './components/ChatWidget';
import HistoryChart from './components/HistoryChart';
import AuditLog from './components/AuditLog';
import Login from './Login';
import { Button } from '@mui/material';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [data, setData] = useState({})
  const [history, setHistory] = useState([])
  const [alerts, setAlerts] = useState([])
  const [schema, setSchema] = useState({})
  const [oee, setOee] = useState({})
  const [connected, setConnected] = useState(false)
  const ws = useRef(null)

  const handleLogin = (t) => {
    console.log("App: Setting token", t);
    localStorage.setItem('token', t);
    setToken(t);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken('');
    if (ws.current) ws.current.close();
  };

  useEffect(() => {
    console.log("App: Effect triggered. Token:", token);
    if (!token) return;

    // In production, use window.location.hostname
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use hostname to allow access from other devices
    const hostname = window.location.hostname || 'localhost';
    const wsUrl = `${protocol}//${hostname}:8000/ws`;

    ws.current = new WebSocket(wsUrl)

    ws.current.onopen = () => {
      console.log("Connected to WS")
      setConnected(true)
    }

    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)

        if (message.type === 'init') {
            if (message.schema) setSchema(message.schema)
            if (message.data) setData(message.data)
            if (message.oee) setOee(message.oee)
            if (message.history) setHistory(message.history)
            if (message.alerts) setAlerts(message.alerts)
            if (message.trust !== undefined) setTrust(message.trust)
            if (message.virtual_keys) setVirtualKeys(message.virtual_keys)
        } else if (message.type === 'update') {
            if (message.schema) setSchema(message.schema)
            if (message.data) {
                setData(message.data)
                setHistory(prev => {
                    const newHistory = [...prev, message.data];
                    if (newHistory.length > 60) return newHistory.slice(newHistory.length - 60);
                    return newHistory;
                })
            }
            if (message.oee) setOee(message.oee)
            if (message.alerts) setAlerts(message.alerts)
            if (message.trust !== undefined) setTrust(message.trust)
            if (message.virtual_keys) setVirtualKeys(message.virtual_keys)
        }
      } catch (e) {
        console.error("Error parsing WS message", e)
      }
    }

    ws.current.onclose = () => {
      console.log("WS Closed")
      setConnected(false)
    }

    return () => {
      if (ws.current) ws.current.close()
    }
  }, [token])

  if (!token) {
    return <Login setToken={handleLogin} />;
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4, pb: 10 }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <Typography variant="h4" component="h1">Universal OEE Interface</Typography>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ textAlign: 'right', marginRight: '10px' }}>
                <Typography variant="caption" display="block">Trust Score</Typography>
                <Typography variant="body1" sx={{ color: trust < 0.8 ? 'red' : 'green', fontWeight: 'bold' }}>
                    {Math.round(trust * 100)}%
                </Typography>
            </div>
            <Button variant="outlined" color="inherit" onClick={handleLogout}>Logout</Button>
            <div style={{
            padding: '5px 10px',
            borderRadius: '4px',
            backgroundColor: connected ? '#4caf50' : '#f44336',
            color: 'white'
            }}>
            {connected ? 'Online' : 'Offline'}
            </div>
        </div>
      </header>

      {alerts.map((alert) => (
        <Alert key={alert.id} severity={alert.severity || "info"} sx={{ mb: 2 }}>
          {new Date(alert.timestamp * 1000).toLocaleTimeString()}: {alert.message}
        </Alert>
      ))}

      <Grid container spacing={3}>
        {/* OEE Section */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>OEE Metrics</Typography>
            <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', flexWrap: 'wrap' }}>
                <div style={{ textAlign: 'center', margin: '10px' }}>
                    <Typography variant="h2">{oee.oee || 0}%</Typography>
                    <Typography variant="subtitle1">Overall</Typography>
                </div>
                <div style={{ textAlign: 'center', margin: '10px' }}>
                    <Typography variant="h4">{oee.availability || 0}%</Typography>
                    <Typography variant="subtitle2">Availability</Typography>
                </div>
                <div style={{ textAlign: 'center', margin: '10px' }}>
                    <Typography variant="h4">{oee.performance || 0}%</Typography>
                    <Typography variant="subtitle2">Performance</Typography>
                </div>
                <div style={{ textAlign: 'center', margin: '10px' }}>
                    <Typography variant="h4">{oee.quality || 0}%</Typography>
                    <Typography variant="subtitle2">Quality</Typography>
                </div>
            </div>
          </Paper>
        </Grid>

        {/* Control Section */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'center' }}>
            <Typography variant="h6" gutterBottom align="center">Mission Control</Typography>
            <ControlPanel token={token} />
          </Paper>
        </Grid>

        {/* Dynamic Widgets */}
        <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>Live Telemetry (Auto-Discovered)</Typography>
            <Grid container spacing={2}>
                {Object.entries(schema).map(([key, type]) => {
                    const isVirtual = virtualKeys ? virtualKeys.some(k => k.includes(key)) : false;
                    return (
                        <Grid item xs={12} sm={6} md={3} key={key}>
                            <DynamicWidget name={key} value={data[key]} type={type} isVirtual={isVirtual} />
                        </Grid>
                    )
                })}
            </Grid>
        </Grid>

        {/* Historical Charts for Gauges */}
        <Grid item xs={12}>
             <Typography variant="h6" gutterBottom>Trends</Typography>
             <Grid container spacing={2}>
                {Object.entries(schema)
                    .filter(([key, type]) => type === 'Gauge')
                    .map(([key, type]) => (
                        <Grid item xs={12} md={6} key={key + "_chart"}>
                            <HistoryChart title={key} data={history} dataKey={key} />
                        </Grid>
                    ))
                }
             </Grid>
        </Grid>

        {/* Raw Data (Optional) */}
        <Grid item xs={12}>
             <Alert severity="info" sx={{ mt: 2 }}>
                Schema: {JSON.stringify(schema)}
             </Alert>
        </Grid>

        <Grid item xs={12}>
            <AuditLog />
        </Grid>
      </Grid>
      <ChatWidget />
    </Container>
  )
}

export default App
