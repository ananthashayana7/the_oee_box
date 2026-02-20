import { useState, useEffect, useRef } from 'react'
import { Container, Grid, Typography, Paper, Alert, Box } from '@mui/material';
import DynamicWidget from './components/DynamicWidget';
import ControlPanel from './components/ControlPanel';
import ChatWidget from './components/ChatWidget';
import HistoryChart from './components/HistoryChart';
import AuditLog from './components/AuditLog';
import PlantOverview from './components/PlantOverview';
import Login from './Login';
import { Button } from '@mui/material';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [machines, setMachines] = useState({});
  const [selectedMachineId, setSelectedMachineId] = useState(null);
  const [history, setHistory] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [connected, setConnected] = useState(false);
  const ws = useRef(null);

  const handleLogin = (t) => {
    localStorage.setItem('token', t);
    setToken(t);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken('');
    if (ws.current) ws.current.close();
  };

  const handleExport = async () => {
      try {
        const hostname = window.location.hostname || 'localhost';
        const protocol = window.location.protocol;
        // Trigger download
        window.open(`${protocol}//${hostname}:8000/report/pdf`, '_blank');
      } catch (e) {
          console.error("Export failed", e);
      }
  }

  useEffect(() => {
    if (!token) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
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

        if (message.type === 'plant_init') {
            setMachines(message.machines);
            if (message.history) setHistory(message.history);
        } else if (message.type === 'update') {
            const { machine_id, data, schema, oee, alerts: newAlerts, trust, virtual_keys } = message;

            setMachines(prev => ({
                ...prev,
                [machine_id]: {
                    data,
                    schema,
                    oee: { ...oee, trust },
                    virtual_keys
                }
            }));

            if (newAlerts) setAlerts(newAlerts);

            // Update history only if looking at this machine (simplification)
            if (selectedMachineId === machine_id && data) {
                 setHistory(prev => {
                    const newHistory = [...prev, data];
                    if (newHistory.length > 60) return newHistory.slice(newHistory.length - 60);
                    return newHistory;
                })
            }
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
  }, [token, selectedMachineId])

  if (!token) {
    return <Login setToken={handleLogin} />;
  }

  const activeMachine = selectedMachineId ? machines[selectedMachineId] : null;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4, pb: 10 }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <Typography variant="h4" component="h1">Universal OEE Interface</Typography>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
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

      {!selectedMachineId ? (
          <PlantOverview machines={machines} onSelectMachine={setSelectedMachineId} onExport={handleExport} />
      ) : (
        <Box>
            <Button onClick={() => setSelectedMachineId(null)} sx={{ mb: 2 }}>&larr; Back to Plant View</Button>
            <Typography variant="h5" gutterBottom>Machine: {selectedMachineId.toUpperCase()}</Typography>

            {activeMachine && (
                <Grid container spacing={3}>
                    {/* OEE Section */}
                    <Grid item xs={12} md={8}>
                    <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
                        <Typography variant="h6" gutterBottom>OEE Metrics</Typography>
                        <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', flexWrap: 'wrap' }}>
                            <div style={{ textAlign: 'center', margin: '10px' }}>
                                <Typography variant="h2">{activeMachine.oee?.oee || 0}%</Typography>
                                <Typography variant="subtitle1">Overall</Typography>
                            </div>
                            <div style={{ textAlign: 'center', margin: '10px' }}>
                                <Typography variant="h4">{activeMachine.oee?.availability || 0}%</Typography>
                                <Typography variant="subtitle2">Availability</Typography>
                            </div>
                            <div style={{ textAlign: 'center', margin: '10px' }}>
                                <Typography variant="h4">{activeMachine.oee?.performance || 0}%</Typography>
                                <Typography variant="subtitle2">Performance</Typography>
                            </div>
                            <div style={{ textAlign: 'center', margin: '10px' }}>
                                <Typography variant="h4">{activeMachine.oee?.quality || 0}%</Typography>
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
                            {Object.entries(activeMachine.schema || {}).map(([key, type]) => {
                                const isVirtual = activeMachine.virtual_keys ? activeMachine.virtual_keys.some(k => k.includes(key)) : false;
                                return (
                                    <Grid item xs={12} sm={6} md={3} key={key}>
                                        <DynamicWidget name={key} value={activeMachine.data[key]} type={type} isVirtual={isVirtual} />
                                    </Grid>
                                )
                            })}
                        </Grid>
                    </Grid>

                    {/* Historical Charts for Gauges */}
                    <Grid item xs={12}>
                        <Typography variant="h6" gutterBottom>Trends</Typography>
                        <Grid container spacing={2}>
                            {Object.entries(activeMachine.schema || {})
                                .filter(([key, type]) => type === 'Gauge')
                                .map(([key, type]) => (
                                    <Grid item xs={12} md={6} key={key + "_chart"}>
                                        <HistoryChart title={key} data={history} dataKey={key} />
                                    </Grid>
                                ))
                            }
                        </Grid>
                    </Grid>

                    <Grid item xs={12}>
                        <AuditLog />
                    </Grid>
                </Grid>
            )}
        </Box>
      )}

      <ChatWidget />
    </Container>
  )
}

export default App
