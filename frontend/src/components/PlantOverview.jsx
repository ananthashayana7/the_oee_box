import React from 'react';
import { Grid, Typography, Button, Box } from '@mui/material';
import MachineCard from './MachineCard';

const PlantOverview = ({ machines, onSelectMachine, onExport }) => {
  return (
    <Box sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h4">Plant Overview</Typography>
            <Button variant="contained" onClick={onExport}>Export Report (PDF)</Button>
        </Box>

        <Grid container spacing={3}>
            {Object.entries(machines).map(([id, state]) => {
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
        </Grid>
    </Box>
  );
};

export default PlantOverview;
