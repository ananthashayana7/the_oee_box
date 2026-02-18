import React, { useState, useRef, useEffect } from 'react';
import { Paper, TextField, Button, Typography, List, ListItem, ListItemText, IconButton, Collapse } from '@mui/material';
import axios from 'axios';

const ChatWidget = () => {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [history, setHistory] = useState([
    { sender: "bot", text: "Hello! I am your AI Co-Pilot. Ask me about the machine status." }
  ]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [history]);

  const handleSend = async () => {
    if (!query.trim()) return;

    const userMsg = { sender: "user", text: query };
    setHistory(prev => [...prev, userMsg]);
    setQuery("");

    try {
      const hostname = window.location.hostname || 'localhost';
      const protocol = window.location.protocol;
      const res = await axios.post(`${protocol}//${hostname}:8000/chat`, { query: userMsg.text });
      const botMsg = { sender: "bot", text: res.data.response };
      setHistory(prev => [...prev, botMsg]);
    } catch (error) {
      console.error("Chat failed", error);
      setHistory(prev => [...prev, { sender: "bot", text: "Sorry, I couldn't reach the server." }]);
    }
  };

  return (
    <div style={{ position: 'fixed', bottom: 20, right: 20, zIndex: 1000, width: 350 }}>
      <Button
        variant="contained"
        onClick={() => setOpen(!open)}
        fullWidth
        sx={{ borderRadius: open ? "4px 4px 0 0" : "4px" }}
      >
        {open ? "Close Copilot" : "Open AI Copilot"}
      </Button>
      <Collapse in={open}>
        <Paper elevation={3} sx={{ height: 400, display: 'flex', flexDirection: 'column', p: 1 }}>
          <List sx={{ flexGrow: 1, overflow: 'auto' }}>
            {history.map((msg, idx) => (
              <ListItem key={idx} alignItems="flex-start" sx={{ justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}>
                <Paper sx={{
                    p: 1,
                    bgcolor: msg.sender === 'user' ? '#e3f2fd' : '#f5f5f5',
                    maxWidth: '80%'
                }}>
                  <ListItemText primary={msg.text} />
                </Paper>
              </ListItem>
            ))}
            <div ref={messagesEndRef} />
          </List>
          <div style={{ display: 'flex', gap: '5px', marginTop: '10px' }}>
            <TextField
              fullWidth
              size="small"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask about status..."
            />
            <Button variant="contained" onClick={handleSend} size="small">Send</Button>
          </div>
        </Paper>
      </Collapse>
    </div>
  );
};

export default ChatWidget;
