# 打包成 EXE 说明

## 方法 1: 使用 Python 脚本 (推荐)

### 步骤 1: 运行打包脚本

```bash
python build_exe.py
```

**这个脚本会自动:**
1. 检查并安装 PyInstaller
2. 打包主程序 (pcb_analyzer.exe)
3. 打包验证工具 (validate_accuracy.exe)
4. 打包对比工具 (visual_compare.exe)
5. 创建发布包 (release/)
6. 创建使用示例 (run.bat)

### 步骤 2: 查看结果

打包完成后，在 `release/` 目录中会有:

```
release/
├── pcb_analyzer.exe          # 主程序
├── validate_accuracy.exe     # 验证工具
├── visual_compare.exe        # 对比工具
├── run.bat                   # 使用示例
├── README.md                 # 快速开始
├── USER_GUIDE.md            # 详细使用
├── HANDOFF.md               # 技术文档
├── input/                    # 放入 Gerber 文件
└── output/                   # 输出目录
```

---

## 方法 2: 使用批处理文件 (简单)

### 步骤 1: 双击运行

```
build_simple.bat
```

### 步骤 2: 等待完成

脚本会自动完成所有打包步骤。

---

## 方法 3: 手动打包 (高级)

### 步骤 1: 安装 PyInstaller

```bash
pip install pyinstaller
```

### 步骤 2: 打包主程序

```bash
pyinstaller --name=pcb_analyzer --onefile --console main.py
```

### 步骤 3: 打包验证工具

```bash
pyinstaller --name=validate_accuracy --onefile --console validate_accuracy.py
```

### 步骤 4: 打包对比工具

```bash
pyinstaller --name=visual_compare --onefile --console visual_compare.py
```

### 步骤 5: 收集文件

从 `dist/` 目录复制 EXE 文件到发布目录。

---

## 使用打包后的程序

### 方法 1: 使用 run.bat (推荐)

1. 将 Gerber 文件放入 `release/input/`
2. 双击 `release/run.bat`
3. 选择操作 (1-6)

### 方法 2: 命令行

```bash
# 进入 release 目录
cd release

# 运行分析
pcb_analyzer.exe -i input -o output

# 验证准确性
validate_accuracy.exe input output\pads.csv

# 生成对比图
visual_compare.exe input\mask1.gbr output\pads.csv output
```

### 方法 3: 拖放 (Windows)

创建快捷方式，设置参数后可以拖放文件夹。

---

## 打包选项说明

### --onefile
打包成单个 EXE 文件（推荐）

**优点:**
- 只有一个文件
- 方便分发

**缺点:**
- 首次运行较慢（解压依赖）
- 文件较大

### --onedir
打包成目录（包含依赖）

**优点:**
- 运行速度快
- 文件较小

**缺点:**
- 多个文件
- 不方便分发

### 推荐配置

```bash
pyinstaller \
  --name=pcb_analyzer \
  --onefile \
  --console \
  --icon=icon.ico \
  --add-data="README.md;." \
  main.py
```

---

## 常见问题

### Q1: 打包失败

**错误:** `ModuleNotFoundError`

**解决:**
```bash
# 确保所有依赖已安装
pip install -r requirements.txt

# 重新打包
python build_exe.py
```

### Q2: EXE 运行失败

**错误:** `Failed to execute script`

**解决:**
```bash
# 使用 --console 模式查看错误
pyinstaller --onefile --console main.py

# 或查看日志
dist\pcb_analyzer.exe > log.txt 2>&1
```

### Q3: 文件太大

**原因:** 包含了所有依赖

**解决:**
- 使用 --onedir 模式
- 或使用 UPX 压缩

```bash
pip install pyinstaller[encryption]
pyinstaller --onefile --upx-dir=upx main.py
```

### Q4: 运行速度慢

**原因:** --onefile 模式需要解压

**解决:**
- 使用 --onedir 模式
- 或在 SSD 上运行

### Q5: 缺少依赖

**错误:** `No module named 'xxx'`

**解决:**
```bash
# 添加隐藏导入
pyinstaller --hidden-import=xxx main.py

# 或收集所有依赖
pyinstaller --collect-all=xxx main.py
```

---

## 高级配置

### 添加图标

```bash
pyinstaller --icon=icon.ico main.py
```

### 隐藏控制台窗口

```bash
pyinstaller --noconsole main.py
```

**注意:** 不推荐，因为看不到进度和错误

### 添加版本信息

创建 `version.txt`:

```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', 'Your Company'),
        StringStruct('FileDescription', 'PCB Gerber Analyzer'),
        StringStruct('FileVersion', '1.0.0.0'),
        StringStruct('ProductName', 'PCB Analyzer'),
        StringStruct('ProductVersion', '1.0.0.0'),
      ])
    ]),
  ]
)
```

然后:

```bash
pyinstaller --version-file=version.txt main.py
```

---

## 分发建议

### 1. 创建安装包

使用 Inno Setup 或 NSIS 创建安装程序。

### 2. 压缩发布

```bash
# 压缩 release 目录
tar -czf pcb_analyzer_v1.0.zip release/
```

### 3. 添加 README

在 release 目录添加:
- README.txt (快速开始)
- LICENSE.txt (许可证)
- CHANGELOG.txt (更新日志)

### 4. 测试

在干净的 Windows 系统上测试:
- Windows 7
- Windows 10
- Windows 11

---

## 文件大小优化

### 方法 1: 排除不必要的模块

```bash
pyinstaller --exclude-module=tkinter main.py
```

### 方法 2: 使用 UPX 压缩

```bash
# 下载 UPX: https://upx.github.io/
pyinstaller --upx-dir=upx main.py
```

### 方法 3: 使用虚拟环境

```bash
# 创建干净的虚拟环境
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pyinstaller main.py
```

---

## 性能优化

### 1. 使用 --onedir 模式

```bash
pyinstaller --onedir main.py
```

### 2. 预编译 Python 文件

```bash
python -m compileall .
```

### 3. 使用 Nuitka (替代方案)

```bash
pip install nuitka
python -m nuitka --standalone --onefile main.py
```

**优点:**
- 更快的运行速度
- 更小的文件大小

**缺点:**
- 编译时间长
- 配置复杂

---

## 总结

**推荐方法:**
1. 使用 `python build_exe.py` 自动打包
2. 或使用 `build_simple.bat` 快速打包
3. 测试 `release/` 目录中的 EXE
4. 分发 `release/` 目录

**注意事项:**
- 首次运行可能较慢
- 需要 Windows 7 或更高版本
- 建议在 SSD 上运行
- 文件大小约 50-100MB

**支持:**
- 查看 README.md
- 查看 USER_GUIDE.md
- 运行 `pcb_analyzer.exe --help`
