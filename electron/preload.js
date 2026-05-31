const { contextBridge, ipcRenderer } = require('electron');

// 暴露安全的 API 给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
    // 获取应用版本
    getAppVersion: () => ipcRenderer.invoke('get-app-version'),
    
    // 打开外部链接
    openExternalLink: (url) => ipcRenderer.invoke('open-external-link', url),
    
    // 打开文件选择对话框
    showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
    
    // 打开文件保存对话框
    showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
    
    // 平台信息
    platform: process.platform,
    
    // 判断是否在 Electron 中运行
    isElectron: true
});

// 页面加载完成后的处理
window.addEventListener('DOMContentLoaded', () => {
    console.log('药品不良反应数据分析系统 - Electron 客户端已加载');
});
