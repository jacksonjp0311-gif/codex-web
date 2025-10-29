const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    backgroundColor: '#121212',
    webPreferences: { nodeIntegration: true, contextIsolation: false }
  });
  win.loadFile('lumen.html');
  // Auto-Daemon Wake
  const daemon = spawn('node', ['index.js'], { stdio: 'pipe' });
  daemon.stdout.on('data', (data) => { console.log(Daemon: \); });
}

app.whenReady().then(createWindow);
