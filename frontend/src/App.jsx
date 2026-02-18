import { useState, useEffect, useRef } from 'react'
import { Container, Grid, Typography, Paper, Alert, Box } from '@mui/material';
import DynamicWidget from './components/DynamicWidget';
import ControlPanel from './components/ControlPanel';

function App() {
  const [data, setData] = useState({})
  const [schema, setSchema] = useState({})
  const [oee, setOee] = useState({})
  const [connected, setConnected] = useState(false)
  const ws = useRef(null)

  useEffect(() => {
    const wsUrl = "ws://localhost:8000/ws";

    ws.current = new WebSocket(wsUrl)

    ws.current.onopen = () => {
      console.log("Connected to WS")
      setConnected(true)
    }

    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        if (message.schema) setSchema(message.schema)
        if (message.data) setData(message.data)
        if (message.oee) setOee(message.oee)
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
  }, [])

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <Typography variant="h4" component="h1">Universal OEE Interface</Typography>
        <div style={{
          padding: '5px 10px',
          borderRadius: '4px',
          backgroundColor: connected ? '#4caf50' : '#f44336',
          color: 'white'
        }}>
          {connected ? 'Online' : 'Offline'}
        </div>
      </header>

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
            <ControlPanel />
          </Paper>
        </Grid>

        {/* Dynamic Widgets */}
        <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>Live Telemetry (Auto-Discovered)</Typography>
            <Grid container spacing={2}>
                {Object.entries(schema).map(([key, type]) => (
                    <Grid item xs={12} sm={6} md={3} key={key}>
                        <DynamicWidget name={key} value={data[key]} type={type} />
                    </Grid>
                ))}
            </Grid>
        </Grid>

        {/* Raw Data (Optional) */}
        <Grid item xs={12}>
             <Alert severity="info" sx={{ mt: 2 }}>
                Schema: {JSON.stringify(schema)}
             </Alert>
        </Grid>
      </Grid>
    </Container>
  )
}

export default App
