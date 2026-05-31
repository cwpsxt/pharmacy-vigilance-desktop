# 药品不良反应数据分析系统 - 桌面客户端

基于 Electron + Python 后端的桌面应用程序。

## 项目结构

```
desktop-client/
├── electron/           # Electron 客户端
│   ├── main.js         # 主进程
│   ├── preload.js      # 预加载脚本
│   ├── loading.html    # 加载页面
│   ├── package.json    # 依赖配置
│   └── assets/         # 图标资源
├── python-server/      # Python 后端服务
│   ├── app/            # Flask 应用
│   ├── run.py          # 启动脚本
│   └── requirements.txt
└── dist/               # 打包输出目录
```

## 开发环境搭建

### 1. 安装 Electron 依赖

```bash
cd electron
npm install
```

### 2. 安装 Python 依赖

```bash
cd python-server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 开发模式运行

先启动 Python 服务：
```bash
cd python-server
python run.py
```

再启动 Electron：
```bash
cd electron
npm start
```

## 打包发布

### Windows
```bash
cd electron
npm run build:win
```

### macOS
```bash
cd electron
npm run build:mac
```

### Linux
```bash
cd electron
npm run build:linux
```

打包后的安装程序将生成在 `dist/` 目录。

## 注意事项

1. 打包前需先使用 PyInstaller 打包 Python 后端
2. 确保 `python-server/dist/` 目录包含打包后的可执行文件
3. 图标文件需放置在 `electron/assets/` 目录
   - Windows: `icon.ico`
   - macOS: `icon.icns`
   - Linux: `icon.png`
