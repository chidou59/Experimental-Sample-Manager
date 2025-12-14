# 试样数据管理平台
### Sample Records Management System

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green)
![Matplotlib](https://img.shields.io/badge/Plotting-Matplotlib-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## 📖 项目简介 (Introduction)

**试样数据管理平台** 是一个基于 Python 和 PySide6 开发的桌面应用程序，为需要试验制样的科研人员设计。
本软件旨在提供一个**结构化、可视化、交互式**的平台，帮助科研人员将繁杂的excel等各种文件集中管理。
<div align="center">
  <img src="fig\fig2.png" width="800" />
  <br> <p>图 1：主操作界面</p>
</div>

## ✨ 核心功能 (Key Features)

**🗂️ 项目与试样管理**
* 清晰的树状结构，管理多个实验项目及下属试样。
* 详细记录试样元数据（尺寸、形状、各阶段日期等）。
* 支持复制参数快速新建，避免重复编辑。
<div align="center">
  <img src="fig\fig1.png" width="200" />
  <br> <p>图 2：树状管理、快速新建</p>
  <img src="fig\fig3.png" width="300" />
  <br> <p>图 3：试样参数输入</p>
</div>

**📊 质量变化追踪**
* 根据质量数据自动计算质量变化率（%）。
* 自动绘制质量变化图、质量变化率图。
* 支持一键导出数据、高清图像。
* **批量操作**：支持将某一试样的质量记录批量应用/覆盖到其他同批次试样。
<div align="center">
  <img src="fig\fig5.png" width="300" />
  <br> <p>图 4：输入质量自动绘图</p>
</div>

**📈 应力应变分析**
* 支持上传 **Excel/CSV** 文件智能导入数据。
* 自动绘制应力应变曲线，自动标记峰值强度与对应应变。
* 数据点右键随时编辑/删除，图表实时更新。
* 支持一键导出数据、高清图像。
<div align="center">
  <img src="fig\fig4.png" width="300" />
  <br> <p>图 5：导入数据自动绘图</p>
</div>

**🖼️ 附件画廊**
* 为每个试样建立独立的附件库。
* 支持图片（自动生成缩略图）及文档（PDF, Excel, Txt）管理。
* 支持**拖拽上传**，双击预览或打开文件位置。
<div align="center">
  <img src="fig\fig6.png" width="600" />
  <br> <p>图 6：附件画廊清晰管理</p>
</div>

**💾 数据持久化**
* 所有数据以 JSON 格式存储在本地，无需配置数据库，方便迁移与备份。
* 完全离线运行，保障科研数据安全。

## 🛠️ 安装与运行 (Installation)


### 1. 环境要求
* Python 3.8 或更高版本

### 2. 克隆项目
```bash
git clone [https://github.com/YourUsername/YourProjectName.git](https://github.com/YourUsername/YourProjectName.git)
cd YourProjectName
```

### 3. 安装依赖
建议使用虚拟环境运行本项目。

**如果你有 requirements.txt 文件：**
```bash
pip install -r requirements.txt
```

**如果没有，请手动安装以下核心库：**
```bash
pip install PySide6 matplotlib pandas openpyxl pillow
```

### 4. 启动软件
```bash
python main.py
```

## 📂 项目结构 (Project Structure)

```text
Experimental_Manager/
├── config.py               # 全局配置及路径管理
├── main.py                 # 程序入口
├── src/
│   ├── controllers/        # 控制器层 (业务逻辑)
│   │   └── file_manager.py # 核心文件管理逻辑 (CRUD)
│   ├── views/              # 视图层 (UI 界面)
│   │   ├── main_window.py  # 主窗口框架
│   │   ├── sample_view.py  # 试样详情页 (仪表盘布局)
│   │   ├── chart_widget.py # 质量趋势图组件
│   │   ├── stress_chart.py # 应力应变图组件
│   │   └── dialogs.py      # 各类弹窗 (新建、编辑、录入)
│   └── utils/              # 工具类
│       ├── data_importer.py# 数据导入解析 (Pandas)
│       └── image_helper.py # 图像处理工具
└── README.md
```

## 🖥️ 使用指南 (Usage)

1.  **首次运行**：软件会提示选择一个文件夹作为**数据仓库**（Data Root）。所有的实验数据将保存在该文件夹下的 JSON 文件中。
2.  **创建项目**：点击工具栏的“新建项目”，输入实验名称。
3.  **录入试样**：在项目下新建试样，选择形状（圆柱/立方体等），输入初始质量。
4.  **数据记录**：
    * 在“质量监控”卡片点击“记录”添加不同天数的质量。
    * 在“应力应变”卡片点击“导入”，选择实验机导出的 CSV/Excel 文件。
5.  **导出结果**：在任意图表右下角点击导出按钮，获取高清图表用于论文撰写。

## 🤝 贡献 (Contribution)

欢迎提交 Issue 或 Pull Request 来改进这个项目！

## 📄 许可证 (License)

本项目采用 MIT 许可证。