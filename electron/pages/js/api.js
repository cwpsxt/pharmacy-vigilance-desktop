// API 配置
const API_BASE = 'http://localhost:5001';

// 获取 token（从 URL 参数、localStorage 或父窗口）
function getToken() {
    // 1. 从 URL 参数获取
    const urlParams = new URLSearchParams(window.location.search);
    let token = urlParams.get('token');
    
    // 2. 从 localStorage 获取
    if (!token) {
        token = localStorage.getItem('token');
    }
    
    // 3. 从父窗口全局变量获取
    if (!token && window.parent !== window) {
        try {
            token = window.parent.APP_TOKEN;
        } catch (e) {}
    }
    
    return token || '';
}

// 跳转到登录页面
function redirectToLogin() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    if (window.top !== window) {
        window.top.location.href = window.top.location.pathname.replace(/[^/]*$/, 'login.html');
    } else {
        window.location.href = window.location.pathname.includes('/views/') ? '../login.html' : 'login.html';
    }
}

// 跳转到激活页面
function redirectToActivate() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    if (window.top !== window) {
        window.top.location.href = window.top.location.pathname.replace(/[^/]*$/, 'activate.html');
    } else {
        window.location.href = window.location.pathname.includes('/views/') ? '../activate.html' : 'activate.html';
    }
}

// 无授权检查的 fetch（激活/状态接口）
async function licenseFetch(url, options = {}) {
    const response = await fetch(`${API_BASE}${url}`, options);
    return response;
}

// 带认证的 fetch
async function authFetch(url, options = {}) {
    const token = getToken();

    if (!token) {
        console.warn('No token found, redirecting to login');
        redirectToLogin();
        return null;
    }

    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };

    const response = await fetch(`${API_BASE}${url}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        console.warn('Unauthorized, redirecting to login');
        redirectToLogin();
        return null;
    }

    if (response.status === 403) {
        try {
            const data = await response.clone().json();
            if (data.code === 'LICENSE_REQUIRED') {
                console.warn('License required, redirecting to activate page');
                redirectToActivate();
                return null;
            }
        } catch (e) {}
    }

    return response;
}

// GET 请求
async function apiGet(url) {
    return authFetch(url);
}

// POST 请求
async function apiPost(url, data) {
    return authFetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
}

// POST FormData
async function apiPostForm(url, formData) {
    return authFetch(url, {
        method: 'POST',
        body: formData
    });
}

// PUT 请求
async function apiPut(url, data) {
    return authFetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
}

// DELETE 请求
async function apiDelete(url, data = null) {
    const options = { method: 'DELETE' };
    if (data) {
        options.headers = { 'Content-Type': 'application/json' };
        options.body = JSON.stringify(data);
    }
    return authFetch(url, options);
}
