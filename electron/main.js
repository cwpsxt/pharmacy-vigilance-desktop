const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

// 保持窗口对象的全局引用
let mainWindow = null;
let pythonProcess = null;
const PYTHON_PORT = 5001;

// 判断是否为开发环境
const isDev = !app.isPackaged;

/**
 * 获取 Python 服务器路径
 */
function getPythonServerPath() {
    if (isDev) {
        // 开发环境：使用本地 python-server 目录
        return path.join(__dirname, '..', 'python-server');
    } else {
        // 生产环境：使用打包后的资源目录
        return path.join(process.resourcesPath, 'python-server');
    }
}

/**
 * 获取 Python 可执行文件路径
 */
function getPythonExecutable() {
    const serverPath = getPythonServerPath();
    
    if (isDev) {
        // 开发环境使用系统 Python 或虚拟环境
        if (process.platform === 'win32') {
            return path.join(serverPath, 'venv', 'Scripts', 'python.exe');
        } else {
            return path.join(serverPath, 'venv', 'bin', 'python');
        }
    } else {
        // 生产环境使用打包的可执行文件
        if (process.platform === 'win32') {
            return path.join(serverPath, 'server.exe');
        } else {
            return path.join(serverPath, 'server');
        }
    }
}

/**
 * 启动 Python 后端服务
 */
function startPythonServer() {
    return new Promise((resolve, reject) => {
        const serverPath = getPythonServerPath();
        
        if (isDev) {
            // 开发环境：运行 python run.py
            const pythonExe = getPythonExecutable();
            const runScript = path.join(serverPath, 'run.py');
            
            console.log(`启动 Python 服务: ${pythonExe} ${runScript}`);
            
            pythonProcess = spawn(pythonExe, [runScript], {
                cwd: serverPath,
                env: { ...process.env, FLASK_ENV: 'production' }
            });
        } else {
            // 生产环境：运行打包后的可执行文件
            const serverExe = getPythonExecutable();
            
            console.log(`启动 Python 服务: ${serverExe}`);
            
            pythonProcess = spawn(serverExe, [], {
                cwd: serverPath
            });
        }

        pythonProcess.stdout.on('data', (data) => {
            console.log(`Python: ${data}`);
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error(`Python Error: ${data}`);
        });

        pythonProcess.on('error', (err) => {
            console.error('启动 Python 服务失败:', err);
            reject(err);
        });

        pythonProcess.on('exit', (code) => {
            console.log(`Python 服务退出，退出码: ${code}`);
            pythonProcess = null;
        });

        // 等待服务启动
        waitForServer(resolve, reject);
    });
}

/**
 * 等待服务器启动
 */
function waitForServer(resolve, reject, attempts = 0) {
    const maxAttempts = 30; // 最多等待 30 秒
    
    const checkServer = () => {
        http.get(`http://localhost:${PYTHON_PORT}/api/health`, (res) => {
            if (res.statusCode === 200) {
                console.log('Python 服务已启动');
                resolve();
            } else {
                retry();
            }
        }).on('error', retry);
    };

    const retry = () => {
        if (attempts < maxAttempts) {
            setTimeout(() => waitForServer(resolve, reject, attempts + 1), 1000);
        } else {
            reject(new Error('Python 服务启动超时'));
        }
    };

    checkServer();
}

/**
 * 停止 Python 后端服务
 */
function stopPythonServer() {
    if (pythonProcess) {
        console.log('停止 Python 服务...');
        
        if (process.platform === 'win32') {
            spawn('taskkill', ['/pid', pythonProcess.pid, '/f', '/t']);
        } else {
            pythonProcess.kill('SIGTERM');
        }
        
        pythonProcess = null;
    }
}

/**
 * 查询授权状态
 */
function fetchLicenseStatus() {
    return new Promise((resolve) => {
        const req = http.get(`http://localhost:${PYTHON_PORT}/api/license/status`, (res) => {
            let body = '';
            res.on('data', (chunk) => { body += chunk; });
            res.on('end', () => {
                try {
                    resolve(JSON.parse(body));
                } catch (e) {
                    resolve({ valid: false, reason: 'parse_error' });
                }
            });
        });
        req.on('error', () => resolve({ valid: false, reason: 'network_error' }));
        req.setTimeout(3000, () => {
            req.destroy();
            resolve({ valid: false, reason: 'timeout' });
        });
    });
}

/**
 * 创建主窗口
 */
function createWindow(initialPage = 'login.html') {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1024,
        minHeight: 768,
        title: '医院药学药物警戒与运营绩效可视化分析系统',
        icon: path.join(__dirname, 'assets', 'icon.png'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        show: false
    });

    mainWindow.loadFile(path.join(__dirname, 'pages', initialPage));

    // 页面加载完成后显示窗口
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // 开发环境打开开发者工具
    if (isDev) {
        mainWindow.webContents.openDevTools();
    }

    // 窗口关闭事件
    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // 允许导航到本地后端服务
    mainWindow.webContents.on('will-navigate', (event, url) => {
        // 允许导航到 localhost:5001
        if (url.startsWith('http://localhost:5001') || url.startsWith('http://127.0.0.1:5001')) {
            // 允许导航
            return;
        }
        // 其他外部链接在浏览器中打开
        if (!url.startsWith('file://')) {
            event.preventDefault();
            shell.openExternal(url);
        }
    });

    // 拦截新窗口，在默认浏览器中打开
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        if (url.startsWith('http://localhost:5001') || url.startsWith('http://127.0.0.1:5001')) {
            return { action: 'allow' };
        }
        shell.openExternal(url);
        return { action: 'deny' };
    });
}

/**
 * 显示加载窗口
 */
function createLoadingWindow() {
    const loadingWindow = new BrowserWindow({
        width: 400,
        height: 300,
        frame: false,
        transparent: true,
        alwaysOnTop: true,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    loadingWindow.loadFile(path.join(__dirname, 'loading.html'));
    
    return loadingWindow;
}

// 应用准备就绪
app.whenReady().then(async () => {
    try {
        await startPythonServer();
        console.log('Python 服务启动完成');
    } catch (error) {
        console.error('Python 服务启动失败:', error.message);
    }

    let initialPage = 'activate.html';
    try {
        const status = await fetchLicenseStatus();
        if (status && status.valid) {
            initialPage = 'login.html';
        }
    } catch (error) {
        console.error('授权状态检查失败，默认进入激活页:', error.message);
    }

    createWindow(initialPage);

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow(initialPage);
        }
    });
});

// 所有窗口关闭时退出应用
app.on('window-all-closed', () => {
    stopPythonServer();
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// 应用退出前清理
app.on('before-quit', () => {
    stopPythonServer();
});

// IPC 通信处理
ipcMain.handle('get-app-version', () => {
    return app.getVersion();
});

ipcMain.handle('open-external-link', (event, url) => {
    shell.openExternal(url);
});

ipcMain.handle('show-open-dialog', async (event, options) => {
    const result = await dialog.showOpenDialog(mainWindow, options);
    return result;
});

ipcMain.handle('show-save-dialog', async (event, options) => {
    const result = await dialog.showSaveDialog(mainWindow, options);
    return result;
});
