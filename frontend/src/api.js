// api.js - This handles all direct communication with the Python FastAPI Backend
const API_ORIGIN = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
export const BASE_URL = `${API_ORIGIN.replace(/\/$/, '')}/api/v2`;

// Standard login function using OAuth2 specs
export const loginAPI = async (email, password) => {
    // FastAPI requires the data as form-urlencoded, NOT as JSON for login!
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
    });

    if (!response.ok) {
        throw new Error('שם המשתמש או הסיסמה אינם נכונים'); // "Incorrect username or password"
    }

    // Returns: { access_token, token_type, role, name, organization_id }
    return response.json(); 
};

// A helper function to automatically inject the JWT token into all future requests
export const secureFetch = async (endpoint, options = {}) => {
    const token = localStorage.getItem('jwt_token'); // Get the token from secure local storage
    
    const headers = {
        ...options.headers,
    };

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }

    if (token) {
        headers['Authorization'] = `Bearer ${token}`; // Inject the lock key!
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        // Token expired or invalid!
        localStorage.removeItem('jwt_token');
        localStorage.removeItem('user_role');
        localStorage.removeItem('user_permissions');
        window.location.reload(); // Force them back to the login screen
        throw new Error('Session expired');
    }

    return response.json();
};
