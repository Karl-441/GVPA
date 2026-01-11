# 通用可视化编程助手 (GVPA)

## 项目简介
通用可视化编程助手（General Visual Programming Assistant）是一个旨在整合OpenCV、Matplotlib、Plotly、PyQt等主流可视化库能力的工具。它提供统一、简化的接口，支持图像可视化、数据可视化、交互式可视化及GUI快速生成。

## 核心功能
- **统一可视化接口**：封装多库API，一行代码实现绘图。
- **GUI快速生成**：拖拽配置生成PyQt界面代码。
- **模板库**：内置多种可视化场景模板。
- **代码导出**：自动生成可运行的Python代码。

## 安装与运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行项目
```bash
python main.py
```

## 目录结构
- `gvpa/`: 核心源码
  - `interface/`: 用户界面 (GUI/Web)
  - `core/`: 核心业务逻辑
  - `engine/`: 可视化引擎适配
  - `data/`: 数据存储
- `plugins/`: 插件扩展
- `docs/`: 文档
