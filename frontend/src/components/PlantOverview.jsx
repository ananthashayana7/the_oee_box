import React, { useState } from 'react';
import { Grid, Typography, Button, Box, TextField, InputAdornment } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import MachineCard from './MachineCard';

const PlantOverview = ({ machines, onSelectMachine, onExport }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredMachines = Object.entries(machines).filter(([id, state]) => {
      return id.toLowerCase().includes(searchTerm.toLowerCase());
  });

  return (
    <Box sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
            <Typography variant="h4">Plant Overview</Typography>
            <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                    variant="outlined"
                    size="small"
                    placeholder="Search Machine ID..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    InputProps={{
                        startAdornment: (
                            <InputAdornment position="start">
                                <SearchIcon />
                            </InputAdornment>
                        ),
                    }}
                />
                <Button variant="contained" onClick={onExport}>Export Report (PDF)</Button>
            </Box>
        </Box>

        <Grid container spacing={3}>
            {filteredMachines.map(([id, state]) => {
                const status = state.data?.state_code ?? 0;
                return (
                    <Grid item xs={12} sm={6} md={4} lg={3} key={id}>
                        <MachineCard
                            machineId={id}
                            oee={state.oee}
                            trust={state.oee?.trust || 1.0}
                            status={status}
                            onClick={() => onSelectMachine(id)}
                        />
                    </Grid>
                )
            })}
            {Object.keys(machines).length === 0 && (
                <Grid item xs={12}>
                    <Typography color="text.secondary">Waiting for machines to connect...</Typography>
                </Grid>
            )}
             {Object.keys(machines).length > 0 && filteredMachines.length === 0 && (
                <Grid item xs={12}>
                    <Typography color="text.secondary">No machines match "{searchTerm}"</Typography>
                </Grid>
            )}
        </Grid>
    </Box>
  );
};

export default PlantOverview;
