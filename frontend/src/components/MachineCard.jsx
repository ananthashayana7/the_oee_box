import React from 'react';
import { Card, CardContent, Typography, Box, Chip, IconButton } from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

const MachineCard = ({ machineId, oee, trust, status, onClick, onSettings }) => {
  const oeeVal = oee?.oee || 0;
  const isRunning = status === 1;
  const isFault = status === 2;

  return (
    <Card
      sx={{
        minWidth: 200,
        cursor: 'pointer',
        border: '1px solid #eee',
        '&:hover': { boxShadow: 6 }
      }}
      onClick={onClick}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">{machineId.toUpperCase()}</Typography>
            <Box>
                {isFault ? <WarningIcon color="error" sx={{mr: 1}} /> :
                 isRunning ? <CheckCircleIcon color="success" sx={{mr: 1}} /> :
                 null}
                <IconButton size="small" onClick={(e) => { e.stopPropagation(); onSettings(machineId); }}>
                    <SettingsIcon fontSize="small" />
                </IconButton>
            </Box>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography color="text.secondary">OEE</Typography>
            <Typography variant="h5" fontWeight="bold">{oeeVal}%</Typography>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="caption">Trust Score</Typography>
            <Chip
                label={`${Math.round(trust * 100)}%`}
                size="small"
                color={trust < 0.8 ? "error" : "success"}
                variant="outlined"
            />
        </Box>
      </CardContent>
    </Card>
  );
};

export default MachineCard;
