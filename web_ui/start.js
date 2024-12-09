const { spawn } = require('child_process');
const path = require('path');

// Start FastAPI server
const serverPath = path.join(__dirname, 'server', 'main.py');
const pythonProcess = spawn('python', [serverPath], {
    stdio: 'inherit',
    shell: true
});

pythonProcess.on('error', (err) => {
    console.error('Failed to start FastAPI server:', err);
});

// Start Nuxt.js frontend server
const nuxtProcess = spawn('npm.cmd', ['run', 'dev'], {
    stdio: 'inherit',
    cwd: __dirname,
    shell: true
});

nuxtProcess.on('error', (err) => {
    console.error('Failed to start Nuxt server:', err);
});

// Handle cleanup on exit
process.on('SIGINT', () => {
    pythonProcess.kill();
    nuxtProcess.kill();
    process.exit();
});

process.on('exit', () => {
    pythonProcess.kill();
    nuxtProcess.kill();
});
