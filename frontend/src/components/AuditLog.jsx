import React, { useState, useEffect } from 'react';
import { Paper, Typography, List, ListItem, ListItemText, Chip } from '@mui/material';
import axios from 'axios';

const AuditLog = ({ token }) => {
  const [logs, setLogs] = useState([]);

  const fetchLogs = async () => {
    try {
      const hostname = window.location.hostname || 'localhost';
      const protocol = window.location.protocol;
      const res = await axios.get(`${protocol}//${hostname}:8000/audit`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLogs(res.data);
    } catch (e) {
      console.error("Failed to fetch logs", e);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Paper sx={{ p: 2, mt: 2, maxHeight: 200, overflow: 'auto' }}>
      <Typography variant="h6" gutterBottom>System Audit Logs (AI Shadow Mode)</Typography>
      <List dense>
        {logs.map((log, idx) => (
          <ListItem key={idx}>
            <Chip
              label={log.action}
              color={log.action === 'AI_SHADOW' ? 'warning' : 'primary'}
              size="small"
              sx={{ mr: 2 }}
            />
            <ListItemText
              primary={`${new Date(log.timestamp * 1000).toLocaleTimeString()} - ${log.user}`}
              secondary={log.details}
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
};

export default AuditLog;
