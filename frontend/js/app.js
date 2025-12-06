const API_BASE_URL = 'http://localhost:8002/api/v1';

// Helper to get headers with auth token
function getHeaders() {
    const headers = {
        'Content-Type': 'application/json'
    };
    const token = localStorage.getItem('accessToken');
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

// Helper to handle API errors
async function handleResponse(response) {
    if (response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        window.location.href = 'login.html';
        throw new Error('Unauthorized');
    }
    
    const data = await response.json();
    
    if (!response.ok) {
        const errorMsg = data.message || (data.errors ? JSON.stringify(data.errors) : 'An error occurred');
        throw new Error(errorMsg);
    }
    
    return data;
}

// Auth Functions
async function signup(username, email, password, organizationName) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/signup/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password, organization_name: organizationName })
        });
        return await handleResponse(response);
    } catch (error) {
        throw error;
    }
}

async function verifyEmail(token) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/verify-email/?token=${token}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        return await handleResponse(response);
    } catch (error) {
        throw error;
    }
}

async function login(email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await handleResponse(response);
        if (data.data && data.data.access) {
            localStorage.setItem('accessToken', data.data.access);
            localStorage.setItem('refreshToken', data.data.refresh);
            localStorage.setItem('user', JSON.stringify(data.data.user));
        }
        return data;
    } catch (error) {
        throw error;
    }
}

function logout() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}

// Dashboard Functions
async function getProviders() {
    try {
        const response = await fetch(`${API_BASE_URL}/campaigns/own-providers/`, {
            method: 'GET',
            headers: getHeaders()
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('Error fetching providers:', error);
        throw error;
    }
}

async function createProvider(data) {
    try {
        const response = await fetch(`${API_BASE_URL}/campaigns/own-providers/`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(data)
        });
        return await handleResponse(response);
    } catch (error) {
        throw error;
    }
}

async function getTemplates() {
    try {
        const response = await fetch(`${API_BASE_URL}/campaigns/templates/`, {
            method: 'GET',
            headers: getHeaders()
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('Error fetching templates:', error);
        throw error;
    }
}

async function createTemplate(data) {
    try {
        const response = await fetch(`${API_BASE_URL}/campaigns/templates/`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(data)
        });
        return await handleResponse(response);
    } catch (error) {
        throw error;
    }
}

// UI Helpers
function showAlert(elementId, message, type = 'success') {
    const alert = document.getElementById(elementId);
    alert.textContent = message;
    alert.className = `alert alert-${type}`;
    alert.style.display = 'block';
    setTimeout(() => {
        alert.style.display = 'none';
    }, 5000);
}

function checkAuth() {
    const token = localStorage.getItem('accessToken');
    if (!token) {
        window.location.href = 'login.html';
    }
}
