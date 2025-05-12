// Initialize Socket.IO connection
const socket = io();

// DOM Elements
const temperatureEl = document.getElementById('temperature');
const humidityEl = document.getElementById('humidity');
const pressureEl = document.getElementById('pressure');
const activeDevicesEl = document.getElementById('active-devices');
const totalBlocksEl = document.getElementById('total-blocks');
const lastUpdateEl = document.getElementById('last-update');
const connectionStatusEl = document.getElementById('connection-status');
const blockchainBlocksEl = document.getElementById('blockchain-blocks');
const devicesListEl = document.getElementById('devices-list');
const activityLogEl = document.getElementById('activity-log');

// Menu navigation
const menuItems = document.querySelectorAll('.menu-item');
const sections = document.querySelectorAll('.section');
const sectionTitle = document.getElementById('section-title');

menuItems.forEach(item => {
    item.addEventListener('click', () => {
        const targetSection = item.dataset.section;
        
        // Update active states
        menuItems.forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        
        // Show target section
        sections.forEach(section => {
            section.classList.remove('active');
            if (section.id === targetSection) {
                section.classList.add('active');
                sectionTitle.textContent = item.textContent;
            }
        });
    });
});

// Store connected devices
const connectedDevices = new Map();

// Simulate sensor data
function generateRandomSensorData() {
    return {
        temperature: 20 + Math.random() * 10, // Random temperature between 20-30°C
        humidity: 40 + Math.random() * 20,    // Random humidity between 40-60%
        pressure: 980 + Math.random() * 40,   // Random pressure between 980-1020 hPa
        timestamp: Date.now() / 1000
    };
}

// Update device status
function updateDeviceStatus(deviceId, data) {
    connectedDevices.set(deviceId, {
        lastSeen: new Date(),
        ...data
    });
    
    renderDevices();
    updateActiveDevicesCount();
}

function renderDevices() {
    devicesListEl.innerHTML = Array.from(connectedDevices.entries())
        .map(([deviceId, data]) => `
            <div class="device-item">
                <div>
                    <strong>Device ${deviceId}</strong>
                    <div style="color: var(--text-secondary)">
                        Last seen: ${data.lastSeen.toLocaleTimeString()}
                    </div>
                </div>
                <div class="dot"></div>
            </div>
        `)
        .join('');
}

function updateActiveDevicesCount() {
    activeDevicesEl.textContent = connectedDevices.size;
}

function addActivityLog(message) {
    const logItem = document.createElement('div');
    logItem.className = 'activity-item';
    logItem.innerHTML = `
        <div style="color: var(--text-secondary)">${new Date().toLocaleTimeString()}</div>
        <div>${message}</div>
    `;
    activityLogEl.insertBefore(logItem, activityLogEl.firstChild);
    
    // Keep only last 50 logs
    if (activityLogEl.children.length > 50) {
        activityLogEl.removeChild(activityLogEl.lastChild);
    }
}

function updateSensorData(data) {
    if (data.temperature !== undefined) {
        temperatureEl.textContent = `${Number(data.temperature).toFixed(1)}°C`;
    }
    
    if (data.humidity !== undefined) {
        humidityEl.textContent = `${Number(data.humidity).toFixed(1)}%`;
    }
    
    if (data.pressure !== undefined) {
        pressureEl.textContent = `${Number(data.pressure).toFixed(1)} hPa`;
    }
    
    lastUpdateEl.textContent = new Date().toLocaleTimeString();
}

function renderBlockchain(chain) {
    totalBlocksEl.textContent = chain.length;
    
    blockchainBlocksEl.innerHTML = chain.map(block => `
        <div class="block-item">
            <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                <strong>Block #${block.index}</strong>
                <span style="color: var(--text-secondary)">${new Date(block.timestamp * 1000).toLocaleString()}</span>
            </div>
            <div style="color: var(--text-secondary); margin-bottom: 0.5rem;">
                Hash: <span style="color: var(--accent-red)">${block.hash.substring(0, 16)}...</span>
            </div>
            <div style="color: var(--text-secondary);">
                Transactions: ${block.transactions.length}
            </div>
        </div>
    `).join('');
}

// Socket event handlers
socket.on('connect', () => {
    connectionStatusEl.textContent = 'Connected';
    addActivityLog('Connected to server');
    
    // Get initial blockchain data
    fetch('/api/chain')
        .then(response => response.json())
        .then(data => renderBlockchain(data.chain))
        .catch(error => console.error('Error fetching blockchain:', error));
});

socket.on('disconnect', () => {
    connectionStatusEl.textContent = 'Disconnected';
    addActivityLog('Disconnected from server');
});

socket.on('new_data', (data) => {
    updateDeviceStatus(data.device_id, data);
    updateSensorData(data.data);
    addActivityLog(`Received new data from Device ${data.device_id}`);
});

socket.on('new_block', (data) => {
    renderBlockchain(data.chain);
    addActivityLog('New block added to the chain');
});

// Simulate device data every 3 seconds
setInterval(() => {
    const mockData = {
        device_id: 'raspberry_pi_01',
        data: generateRandomSensorData()
    };
    updateDeviceStatus(mockData.device_id, mockData);
    updateSensorData(mockData.data);
    addActivityLog(`Received new data from Device ${mockData.device_id}`);
}, 3000);

// Check device status every minute
setInterval(() => {
    const now = new Date();
    connectedDevices.forEach((data, deviceId) => {
        if ((now - data.lastSeen) > 60000) { // 1 minute
            connectedDevices.delete(deviceId);
            renderDevices();
            updateActiveDevicesCount();
            addActivityLog(`Device ${deviceId} disconnected due to inactivity`);
        }
    });
}, 60000); 