import React from 'react';
import { Button, Stack, ButtonGroup } from '@mui/material';
import axios from 'axios';

const ControlPanel = ({ token }) => {
  const sendCommand = async (cmd) => {
    try {
      const hostname = window.location.hostname || 'localhost';
      const protocol = window.location.protocol;
      await axios.post(
        `${protocol}//${hostname}:8000/command`,
        { cmd: { command: cmd, target: "factory/line1/machine_1/command" } },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      console.log(`Sent ${cmd}`);
    } catch (error) {
      console.error("Command failed", error);
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
