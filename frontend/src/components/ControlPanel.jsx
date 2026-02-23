import React from 'react';
import { Button, Stack, ButtonGroup } from '@mui/material';
import axios from 'axios';

const ControlPanel = ({ token, machineId }) => {
  const sendCommand = async (cmd) => {
    try {
      const hostname = window.location.hostname || 'localhost';
      const protocol = window.location.protocol;
      const machine = machineId || "machine_1";
      const target = `factory/line1/${machine}/command`;

      console.log(`Attempting to send command: ${cmd} to ${target}`);

      const response = await axios.post(
        `${protocol}//${hostname}:8000/command`,
        { cmd: { command: cmd, target: target } },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      console.log(`Response:`, response.data);
    } catch (error) {
      console.error("Command failed details:", {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      });
      if (error.response?.status === 401) {
        alert("Session expired or invalid. Please Logout and Login again.");
      }
    }
  };

  return (
    <Stack direction="row" spacing={2} justifyContent="center" sx={{ mt: 2 }}>
      <ButtonGroup variant="contained" aria-label="outlined primary button group">
        <Button color="success" onClick={() => sendCommand('START')}>START</Button>
        <Button color="error" onClick={() => sendCommand('STOP')}>STOP</Button>
        <Button color="warning" onClick={() => sendCommand('RESET')}>RESET</Button>
      </ButtonGroup>
    </Stack>
  );
};

export default ControlPanel;
