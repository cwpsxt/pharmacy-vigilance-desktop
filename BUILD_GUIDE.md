# 打包发布指南

## 环境要求

### Windows 打包环境
- Windows 10/11 64位
- Node.js 18+ (https://nodejs.org/)
- Python 3.9+ (https://python.org/)
- Git (可选)

### 检查环境
```bash
node -v      # 应显示 v18.x.x 或更高
npm -v       # 应显示 9.x.x 或更高
python -V    # 应显示 Python 3.9.x 或更高
```

---

## 打包步骤

### 方式零：GitHub Actions 云端打包（Mac 用户推荐）

没有 Windows 电脑时，可在 GitHub 云端自动编译 Windows 安装包。

**前提**：PyInstaller 不能跨平台，Mac 本地无法生成 `server.exe`，必须借助 Windows runner。

#### 1. 推送代码到 GitHub

```bash
cd desktop-client
git init
git add .
git commit -m "prepare windows build"
git remote add origin <你的仓库URL>
git branch -M main
git push -u origin main
```

注意：根目录 [`.gitignore`](.gitignore) 已排除 `venv/`、`node_modules/`、`tools/private_key.pem` 等，不要提交私钥和 Mac 本地依赖。

#### 2. 触发打包

- 打开 GitHub 仓库 → **Actions** → **Build Release** → **Run workflow**
- 或推送版本 tag：`git tag v1.0.0 && git push origin v1.0.0`

#### 3. 下载安装包

- 进入本次 workflow run → **Artifacts** → 下载 `windows-installer`
- 内含 `PharmacyVigilanceSystem Setup 1.0.0.exe`（版本号以 `electron/package.json` 为准）

工作流定义见 [`.github/workflows/build.yml`](.github/workflows/build.yml)，会自动：

1. 在 Windows 上 PyInstaller 打包 `python-server/dist/server.exe`（含授权模块 `cryptography`）
2. electron-builder 生成 NSIS 安装程序
3. 校验产物并上传 Artifact

### 方式一：使用打包脚本（Windows 本地推荐）

双击运行 `build_windows.bat`，脚本会自动完成所有步骤。

### 方式二：手动打包

#### 第一步：打包 Python 后端

```bash
# 1. 进入 python-server 目录
cd python-server

# 2. 创建虚拟环境（如果没有）
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 5. 执行打包
pyinstaller --clean server.spec

# 打包完成后，可执行文件在 dist/ 目录
# Windows: dist/server.exe
# macOS/Linux: dist/server
```

#### 第二步：打包 Electron 前端

```bash
# 1. 进入 electron 目录
cd electron

# 2. 安装依赖（首次）
npm install

# 3. 打包
# Windows:
npm run build:win

# macOS:
npm run build:mac

# Linux:
npm run build:linux
```

---

## 输出文件

打包完成后，安装包在 `dist/` 目录：

| 平台 | 文件名 | 说明 |
|------|--------|------|
| Windows | `PharmacyVigilanceSystem Setup 1.0.0.exe` | NSIS安装程序 |
| macOS | `PharmacyVigilanceSystem-1.0.0.dmg` | DMG镜像 |
| Linux | `PharmacyVigilanceSystem-1.0.0.AppImage` | AppImage |

---

## 常见问题

### 1. PyInstaller 打包失败

**问题**: 缺少模块或打包后运行报错

**解决**: 编辑 `server.spec`，在 `hiddenimports` 中添加缺少的模块：
```python
hiddenimports=[
    'flask',
    'flask_cors',
    # 添加缺少的模块名...
],
```

### 2. Electron 打包失败

**问题**: 找不到 python-server/dist

**解决**: 确保先完成 Python 后端打包，`python-server/dist/` 目录存在且包含 `server.exe`

### 3. 安装后无法启动

**问题**: 程序启动后白屏或报错

**解决**: 
1. 检查杀毒软件是否误杀
2. 以管理员身份运行
3. 查看日志文件排查问题

### 4. 打包文件过大

**解决**: 在 `server.spec` 中添加排除项：
```python
excludes=['tkinter', 'test', 'unittest'],
```

---

## 打包配置说明

### Python 打包配置 (server.spec)

```python
datas=[
    ('static', 'static'),      # 静态资源
    ('data', 'data'),          # 数据目录
    ('uploads', 'uploads'),    # 上传目录
],
hiddenimports=[
    'flask',                   # Web框架
    'flask_cors',              # 跨域支持
    'flask_sqlalchemy',        # ORM
    'pandas',                  # 数据处理
    'openpyxl',                # Excel支持
    'matplotlib',              # 图表生成
    'cryptography',            # 授权验签
    'app.license',             # 授权管理
    'app.license_crypto',      # 激活码加解密
    # ...
],
```

### Electron 打包配置 (package.json)

```json
{
  "build": {
    "extraResources": [
      {
        "from": "../python-server/dist",  // Python打包输出
        "to": "python-server"             // 复制到资源目录
      }
    ],
    "win": {
      "target": ["nsis"],                 // NSIS安装程序
      "icon": "assets/icon.ico"           // Windows图标
    },
    "nsis": {
      "oneClick": false,                  // 非一键安装
      "allowToChangeInstallationDirectory": true  // 可选安装路径
    }
  }
}
```

---

## 发布检查清单

- [ ] Python 后端打包成功 (`python-server/dist/server.exe` 存在)
- [ ] Electron 打包成功 (`dist/*Setup*.exe` 存在)
- [ ] 安装程序可正常安装
- [ ] 程序可正常启动
- [ ] 首次启动进入激活页，激活码验证正常
- [ ] 登录功能正常
- [ ] 数据导入功能正常
- [ ] AI 功能正常（需联网）
- [ ] 数据导出功能正常

---

## 版本更新

更新版本号：
1. 修改 `electron/package.json` 中的 `version`
2. 重新打包

```json
{
  "version": "1.0.1"  // 修改版本号
}
```
