import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, Typography } from '@mui/material';

const HistoryChart = ({ title, data, dataKey }) => {
  return (
    <Card sx={{ m: 1, minHeight: 250 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>{title} Trend</Typography>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data}>
            <XAxis dataKey="timestamp" tickFormatter={(t) => new Date(t * 1000).toLocaleTimeString()} />
            <YAxis />
            <Tooltip labelFormatter={(t) => new Date(t * 1000).toLocaleString()} />
            <Line type="monotone" dataKey={dataKey} stroke="#8884d8" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export default HistoryChart;
