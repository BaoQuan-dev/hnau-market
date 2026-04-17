# 🌾 河南农业大学闲置交易平台

校园专属闲置物品交易系统，支持学生认证、物品发布、收藏、留言等功能。

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-2.0+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ 功能特性

### 核心功能
- 🔐 **用户系统**：注册、登录、个人信息管理
- 🎓 **学生认证**：河南农业大学学生身份认证
- 📦 **闲置发布**：发布闲置物品，支持图片、成色、分类
- 🔍 **搜索筛选**：关键词搜索、分类筛选

### 新增功能
- ❤️ **收藏功能**：收藏感兴趣的物品
- 👁️ **浏览历史**：自动记录浏览过的物品
- 💬 **留言询问**：物品详情页留言互动
- 🏷️ **成色标签**：全新/99新/95新/9成新/8成新

### 管理功能
- 👮 管理员后台
- 📋 用户管理、认证审核
- 📊 物品管理

## 🎨 UI特色

- 🌾 农大绿 + 丰收金主题配色
- 📱 响应式设计，适配手机/电脑
- ✨ 卡片悬停动效
- 🎯 图标分类导航

## 🛠️ 技术栈

- **后端**: Python + Flask
- **数据库**: SQLite
- **前端**: 原生 HTML + CSS + JavaScript
- **部署**: Render (免费托管)

## 📦 本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/hnau-market.git
cd hnau-market

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
python app.py

# 5. 浏览器访问
http://localhost:5000
```

## 🚀 部署到 Render

### 方式一：一键部署

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### 方式二：手动部署

1. **Fork 本仓库** 到你的 GitHub

2. **登录 Render** (https://render.com)

3. **创建 Web Service**
   - 选择 "New" → "Web Service"
   - 连接 GitHub，选择 `hnau-market` 仓库

4. **配置部署参数**
   | 参数 | 值 |
   |------|-----|
   | Name | hnau-market |
   | Runtime | Python 3 |
   | Build Command | `./build.sh` |
   | Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2` |

5. **添加环境变量**（可选）
   - `SECRET_KEY`: 应用密钥（推荐设置）

6. **点击 Deploy** 等待部署完成

### 免费版限制

- ⏰ 15分钟无活动自动休眠
- 💾 数据存储在 `/tmp`，重启后丢失
- 🔒 建议升级付费版实现数据持久化

## 🔑 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |

⚠️ 部署后请立即修改密码！

## 📁 项目结构

```
hnau-market/
├── app.py              # Flask 主程序
├── requirements.txt    # Python 依赖
├── build.sh            # Render 构建脚本
├── render.yaml         # Render 配置文件
├── README.md           # 项目说明
├── .gitignore          # Git 忽略配置
└── templates/          # HTML 模板
    ├── base.html       # 基础模板（全局样式）
    ├── index.html      # 首页
    ├── login.html      # 登录页
    ├── register.html   # 注册页
    ├── publish.html    # 发布页
    ├── item_detail.html # 物品详情
    ├── profile.html    # 个人中心
    ├── favorites.html  # 我的收藏
    ├── history.html    # 浏览历史
    ├── auth.html       # 学生认证
    ├── admin.html      # 管理后台
    └── error.html      # 错误页
```

## 📋 数据库结构

### 用户表 (user)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| username | TEXT | 用户名 |
| password | TEXT | 密码哈希 |
| auth_status | TEXT | 认证状态 |
| college | TEXT | 学院 |
| is_admin | INTEGER | 是否管理员 |

### 物品表 (item)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| title | TEXT | 标题 |
| price | REAL | 价格 |
| condition | TEXT | 成色 |
| category | TEXT | 分类 |
| status | TEXT | 状态 |

### 收藏表 (favorite)
| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | INTEGER | 用户ID |
| item_id | INTEGER | 物品ID |

### 留言表 (comment)
| 字段 | 类型 | 说明 |
|------|------|------|
| item_id | INTEGER | 物品ID |
| user_id | INTEGER | 用户ID |
| content | TEXT | 留言内容 |

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 开源协议

[MIT License](LICENSE)

---

🌾 河南农业大学闲置交易平台 © 2024