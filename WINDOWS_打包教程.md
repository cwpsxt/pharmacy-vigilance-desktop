# Windows 打包成 EXE 安装包 - 零基础教程

> 把这个项目打包成 Windows 用户双击就能安装的 `.exe` 安装程序。
>
> **重要**：必须在 **Windows 电脑** 上打包，Mac 上做不了。
> 因为 PyInstaller 不支持跨平台打包。

> **重要**：必须在 **Windows 电脑** 上本地打包，Mac 上无法直接生成 `server.exe`（PyInstaller 不支持跨平台）。
>
> **Mac 用户替代方案**：使用 GitHub Actions 云端打包（见下方「方式 C」）。

---

## 方式 C：GitHub Actions 云端打包（Mac / 无 Windows 电脑）

### 1. 推送代码

```bash
cd desktop-client
git init
git add .
git commit -m "prepare windows build"
git remote add origin <你的GitHub仓库URL>
git branch -M main
git push -u origin main
```

### 2. 触发构建

GitHub 仓库 → **Actions** → **Build Release** → **Run workflow**

### 3. 下载安装包

构建完成后 → 进入 run 详情 → **Artifacts** → 下载 `windows-installer`

产物文件名类似：`PharmacyVigilanceSystem Setup 1.0.0.exe`

### 4. 注意事项

- 不要把 `tools/private_key.pem` 提交到 GitHub（已在 `.gitignore` 排除）
- 安装包内只含公钥，激活码仍需在厂商侧用 `tools/license_generator.py` 或 Web 工具生成
- 首次安装启动应进入**激活页**，激活后才能登录

---

## 一、把项目拷到 Windows 电脑

把整个 `desktop-client` 文件夹拷贝到 Windows，建议放在路径不带中文、不带空格的位置：

```
推荐：D:\projects\desktop-client
不推荐：C:\Users\张三\桌面\desktop-client    （含中文，可能出错）
```

---

## 二、安装两个开发工具

### 1. Node.js（带 npm）

- 下载：https://nodejs.org/
- 选 **LTS（长期支持版）**，版本 18 或更高
- 安装时全部默认下一步即可

### 2. Python

- 下载：https://www.python.org/downloads/
- 版本要求 3.9 或更高（建议 3.10 / 3.11，**不要用 3.13**，部分库还没适配）
- **⚠️ 安装第一步勾上 "Add Python to PATH"**（很重要！否则后面找不到 python 命令）

### 3. 验证环境

打开 **命令提示符（cmd）** 或 **PowerShell**，依次输入：

```cmd
node -v
npm -v
python --version
pip --version
```

如果四条命令都返回版本号，环境就准备好了。如果某条报"不是内部或外部命令"，需要重新安装并勾选添加到 PATH。

---

## 三、打包（两种方式任选）

### 方式 A：一键脚本（小白推荐）

1. 用资源管理器进入项目根目录 `desktop-client`
2. **双击** `build_windows.bat`
3. 等待自动完成（首次大约 10–20 分钟，主要时间在下载 npm 和 pip 依赖）
4. 完成后会自动打开 `dist` 目录，里面就是安装包

如果脚本中途报错，看错误信息，常见问题见本文末"常见问题"。

### 方式 B：手动分步（推荐用于排查问题）

打开 cmd，**先 cd 到项目根目录**：

```cmd
cd /d D:\projects\desktop-client
```

#### 第 1 步：打包 Python 后端

```cmd
cd python-server

:: 创建虚拟环境（首次执行需要）
python -m venv venv

:: 激活虚拟环境（注意是反斜杠）
venv\Scripts\activate

:: 装依赖
pip install -r requirements.txt
pip install pyinstaller

:: 打包
pyinstaller --clean server.spec
```

完成后会生成 `python-server\dist\server.exe`，大约 80–150 MB。

**验证**：双击 `python-server\dist\server.exe`，如果弹出 "服务运行在 http://localhost:5001" 类似提示，说明后端打包成功。可以关掉它。

#### 第 2 步：打包 Electron 前端

```cmd
cd ..\electron

:: 装依赖（首次执行需要）
npm install

:: 打包
npm run build:win
```

完成后会在项目根目录的 `dist\` 下生成：

```
dist\PharmacyVigilanceSystem Setup 1.0.0.exe
```

这就是最终给用户的安装包，大概 250–350 MB。

---

## 四、测试安装包

1. 双击 `PharmacyVigilanceSystem Setup 1.0.0.exe`
2. 选择安装目录（建议安装到非系统盘，如 `D:\Programs\`）
3. 安装完后桌面会有 **"PharmacyVigilance"** 快捷方式
4. 双击启动，等待几秒（首次启动需要释放 Python 后端）
5. **首次启动应进入激活页**，输入激活码后进入登录页

**默认管理员账号**（激活成功后）：
- 用户名：`admin`
- 密码：`admin`

激活码生成见 [`release/授权说明.txt`](release/授权说明.txt)。

---

## 五、发布给别人

把生成的 `Setup 1.0.0.exe` 上传到网盘 / 用 U 盘拷给用户，对方双击安装即可。

无需任何其他依赖——Python、Node、所有库都已经打包进去了。

---

## 六、常见问题

### 1. 脚本提示"python 不是内部或外部命令"

**原因**：Python 没装、或没勾选 Add to PATH。
**解决**：重新跑 Python 安装程序，选 "Modify" → 勾选 "Add Python to environment variables"。

### 2. pip install 卡住或超时

**原因**：访问 PyPI 慢。
**解决**：用国内镜像（清华源）：

```cmd
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. npm install 卡住

**解决**：换成国内镜像：

```cmd
npm config set registry https://registry.npmmirror.com
npm install
```

### 4. PyInstaller 打包失败，提示缺少模块

**原因**：代码用了某个库，但 `server.spec` 的 `hiddenimports` 没列出。
**解决**：编辑 [python-server/server.spec](python-server/server.spec)，把缺的模块名加到 `hiddenimports` 列表里，重新打包。

### 5. Electron 打包报错：找不到 python-server/dist

**原因**：第一步 Python 打包没成功 / 没做。
**解决**：确认 `python-server\dist\server.exe` 存在再做第二步。

### 6. 安装后启动白屏 / 转圈不进入

**原因**：Python 后端没启动起来。
**排查**：
- 打开任务管理器看是否有 `server.exe` 进程
- 试试以管理员身份运行
- 检查防火墙 / 杀毒软件是否拦截了 5001 端口
- 临时把 [server.spec:55](python-server/server.spec#L55) 的 `console=False` 改回 `console=True`，重新打包，启动时会有黑窗口显示后端日志，能看到具体报错

### 7. 安装包太大（300MB+）

**原因**：pandas + matplotlib 体积本身就大。
**优化方案**（按需）：
- 如果不用 matplotlib，从代码和 hiddenimports 移除可省 ~50MB
- 如果不用 pandas，移除可省 ~80MB
- 在 [server.spec](python-server/server.spec) 加 `excludes=['tkinter','test','unittest']` 排除标准库无用模块

### 8. 杀毒软件报毒

**原因**：PyInstaller 打包的程序经常被误报（无数字签名）。
**解决**：
- 临时方案：让用户加白名单
- 长期方案：买代码签名证书（约 ¥500–2000/年）给 exe 签名

---

## 七、修改版本号

下次升级时改 [electron/package.json:3](electron/package.json#L3)：

```json
{
  "version": "1.0.1"   // 改这里
}
```

然后重新跑 `build_windows.bat` 即可。

---

## 八、文件清单

打包前检查这几个关键文件都在：

- [x] `electron/assets/icon.ico` — 应用图标（已生成）
- [x] `electron/package.json` — Electron 配置
- [x] `electron/main.js` — Electron 主进程
- [x] `python-server/server.spec` — PyInstaller 配置（console 已改为 False）
- [x] `python-server/run.py` — Python 入口
- [x] `python-server/requirements.txt` — Python 依赖清单
- [x] `build_windows.bat` — 一键打包脚本
