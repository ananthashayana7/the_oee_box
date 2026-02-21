import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, TextField, Box, Typography
} from '@mui/material';
import axios from 'axios';

const MachineSettings = ({ open, onClose, machineId, token }) => {
  const [cycleTime, setCycleTime] = useState(1.0);
  const [shiftStart, setShiftStart] = useState(8);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSave = async () => {
    setLoading(true);
    setError("");
    try {
      const hostname = window.location.hostname || 'localhost';
      const protocol = window.location.protocol;

      const config = {
          machine_id: machineId,
          ideal_cycle_time: parseFloat(cycleTime),
          shift_start_hour: parseInt(shiftStart),
          target_availability: 0.9,
          target_performance: 0.95,
          target_quality: 0.99
      };

      await axios.put(`${protocol}//${hostname}:8000/machines/${machineId}/config`, { config }, {
          headers: { Authorization: `Bearer ${token}` }
      });
      onClose();
    } catch (err) {
      console.error(err);
      if (err.response && err.response.status === 403) {
          setError("Access Denied: You need Engineer or Admin role.");
      } else {
          setError("Failed to save config.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Machine Settings: {machineId}</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
            <TextField
                label="Ideal Cycle Time (seconds)"
                type="number"
                fullWidth
                margin="dense"
                value={cycleTime}
                onChange={(e) => setCycleTime(e.target.value)}
                helperText="Theoretical minimum time to produce one part"
            />
            <TextField
                label="Shift Start Hour (0-23)"
                type="number"
                fullWidth
                margin="dense"
                value={shiftStart}
                onChange={(e) => setShiftStart(e.target.value)}
            />
            {error && <Typography color="error" variant="caption">{error}</Typography>}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave} variant="contained" disabled={loading}>
            {loading ? "Saving..." : "Save Configuration"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default MachineSettings;
