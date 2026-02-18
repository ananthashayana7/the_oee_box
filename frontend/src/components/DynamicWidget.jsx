import React from 'react';
import { Card, CardContent, Typography, LinearProgress, Box, Chip } from '@mui/material';

const DynamicWidget = ({ name, value, type, isVirtual }) => {
  let content = <Typography variant="h5">{value}</Typography>;

  if (type === 'Counter') {
    content = (
      <Typography variant="h3" component="div">
        {value}
      </Typography>
    );
  } else if (type === 'Gauge') {
    // Determine min/max? Just assume 0-100 for temperature for now
    content = (
      <Box sx={{ width: '100%' }}>
        <Typography variant="h4">{value}</Typography>
        <LinearProgress variant="determinate" value={Math.min(Math.max(value, 0), 100)} />
      </Box>
    );
  } else if (type === 'State') {
    const stateMap = { 0: 'STOPPED', 1: 'RUNNING', 2: 'FAULT' };
    const stateColor = { 0: 'grey', 1: 'green', 2: 'red' };
    const status = stateMap[value] || value;
    const color = stateColor[value] || 'black';
    content = (
      <Typography variant="h4" sx={{ color: color, fontWeight: 'bold' }}>
        {status}
      </Typography>
    );
  } else if (type === 'Timestamp') {
      content = <Typography variant="h6">{new Date(value * 1000).toLocaleTimeString()}</Typography>;
  }

  return (
    <Card sx={{ minWidth: 200, m: 1, position: 'relative', borderLeft: isVirtual ? '4px solid #9c27b0' : '4px solid #4caf50' }}>
      <CardContent>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography sx={{ fontSize: 14 }} color="text.secondary" gutterBottom>
            {name}
            </Typography>
            {isVirtual && <Chip label="Virtual" size="small" color="secondary" sx={{ height: 20, fontSize: 10 }} />}
        </div>
        <Typography sx={{ fontSize: 12 }} color="text.disabled" gutterBottom>
          {type}
        </Typography>
        {content}
      </CardContent>
    </Card>
  );
};

export default DynamicWidget;
