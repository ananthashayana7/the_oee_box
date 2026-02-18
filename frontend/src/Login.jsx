import React, { useState } from 'react';
import { Paper, TextField, Button, Typography, Box, Alert } from '@mui/material';
import axios from 'axios';

const Login = ({ setToken }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    try {
      const hostname = window.location.hostname || 'localhost';
      const protocol = window.location.protocol;
      console.log("Login: Sending request to", `${protocol}//${hostname}:8000/token`);
      const res = await axios.post(`${protocol}//${hostname}:8000/token`, formData);
      console.log("Login: Success, token received", res.data.access_token);
      setToken(res.data.access_token);
    } catch (err) {
      console.error("Login: Failed", err);
      setError('Login failed. Check credentials.');
    }
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', bgcolor: '#f5f5f5' }}>
      <Paper elevation={3} sx={{ p: 4, width: 300 }}>
        <Typography variant="h5" gutterBottom>Login</Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Username"
            margin="normal"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <TextField
            fullWidth
            label="Password"
            type="password"
            margin="normal"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button type="submit" variant="contained" fullWidth sx={{ mt: 2 }}>
            Sign In
          </Button>
        </form>
        <Typography variant="caption" display="block" sx={{ mt: 2, textAlign: 'center' }}>
          Default: admin / admin123
        </Typography>
      </Paper>
    </Box>
  );
};

export default Login;
