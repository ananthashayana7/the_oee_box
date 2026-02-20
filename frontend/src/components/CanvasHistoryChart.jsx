import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { Card, CardContent, Typography } from '@mui/material';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const CanvasHistoryChart = ({ title, data, dataKey }) => {

  const chartData = useMemo(() => {
    return {
      labels: data.map(d => new Date(d.timestamp * 1000).toLocaleTimeString()),
      datasets: [
        {
          label: title,
          data: data.map(d => d[dataKey]),
          borderColor: 'rgb(53, 162, 235)',
          backgroundColor: 'rgba(53, 162, 235, 0.5)',
          tension: 0.1,
          pointRadius: 0, // Performance: Hide points for high density
          borderWidth: 2,
        },
      ],
    };
  }, [data, title, dataKey]);

  const options = useMemo(() => ({
    responsive: true,
    animation: false, // Performance: Disable animation for real-time updates
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        display: false
      },
      title: {
        display: false,
        text: title,
      },
    },
    scales: {
        x: {
            display: true,
            ticks: {
                maxTicksLimit: 10
            }
        },
        y: {
            beginAtZero: false
        }
    }
  }), [title]);

  return (
    <Card sx={{ m: 1, minHeight: 250 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>{title} Trend (Canvas)</Typography>
        <div style={{ height: '200px' }}>
            <Line options={options} data={chartData} />
        </div>
      </CardContent>
    </Card>
  );
};

export default CanvasHistoryChart;
