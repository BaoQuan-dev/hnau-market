# 河南农业大学闲置物品交易平台 - Render 部署指南

本指南将帮助你把河南农业大学闲置物品交易平台部署到 Render 平台，让你的项目可以在互联网上访问。

---

## 📋 部署前准备

### 1. 创建 GitHub 仓库

部署到 Render 最简单的方式是通过 GitHub 仓库自动部署。

**步骤：**

1. 访问 [GitHub](https://github.com) 并登录账号

2. 点击右上角 **"+"** 按钮，选择 **"New repository"**

3. 填写仓库信息：
   - **Repository name**: `hnau-market`（或你喜欢的名称）
   - **Description**: `河南农业大学闲置物品交易平台`
   - **选择 Public**（公开仓库免费额度更多）
   - **勾选 "Add a README file"**

4. 点击 **"Create repository"** 创建仓库

5. **上传项目文件**：
   - 在仓库页面点击 **"uploading an existing file"**
   - 将 `hnau-market-deploy` 文件夹内的所有文件拖入上传区域
   - 确保包含以下文件：
     ```
     hnau-market/
     ├── app.py
     ├── requirements.txt
     ├── render.yaml
     ├── build.sh
     └── templates/
         ├── base.html
         ├── index.html
         ├── login.html
         └── ...（其他模板文件）
     ```
   - 点击 **"Commit changes"** 提交

---

## 🚀 创建 Render Web Service

### 2. 注册/登录 Render

1. 访问 [Render 官网](https://render.com)

2. 点击 **"Get Started"** 或 **"Sign Up"**

3. 使用 **GitHub 账号登录**（推荐）或邮箱注册

4. 授权 Render 访问你的 GitHub 仓库

### 3. 创建 Web Service

**方法一：通过 GitHub 仓库自动部署（推荐）**

1. 登录后进入 Dashboard

2. 点击 **"New +"** 按钮，选择 **"Web Service"**

3. 在 "Connect a repository" 页面：
   - 选择你的 **GitHub 账号**
   - 搜索并选择你刚才创建的仓库
   - 点击 **"Connect"**

4. 配置 Web Service：

   | 配置项 | 值 | 说明 |
   |--------|-----|------|
   | **Name** | `hnau-market` | 服务名称，将成为 URL 的一部分 |
   | **Region** | Singapore（或其他） | 选择离用户最近的区域 |
   | **Branch** | `main` | 部署的分支 |
   | **Root Directory** | （留空） | 使用仓库根目录 |
   | **Runtime** | `Python` | 运行环境 |
   | **Build Command** | `./build.sh` | 构建脚本 |
   | **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2` | 启动命令 |

5. **实例类型**：选择 **Free**（免费版）

6. **环境变量**（点击 "Advanced" → "Add Environment Variable"）：

   | Key | Value | 说明 |
   |-----|-------|------|
   | `SECRET_KEY` | （点击 Generate 自动生成） | Flask 会话密钥 |
   | `DATABASE_PATH` | `/tmp/hnau_market.db` | 数据库路径 |
   | `FLASK_ENV` | `production` | 生产环境 |

7. 点击 **"Create Web Service"**

8. **等待部署完成**（通常需要 1-3 分钟）

### 4. 访问你的应用

部署成功后，你将看到类似的信息：

```
Your service is live at: https://hnau-market.onrender.com
```

访问这个链接即可使用你的闲置交易平台！

---

## 🔧 配置环境变量（可选）

如果你需要修改配置，可以在服务页面点击 **"Environment"** 标签进行修改：

| 变量名 | 说明 | 建议 |
|--------|------|------|
| `SECRET_KEY` | Flask 会话加密密钥 | 使用随机字符串，定期更换 |
| `DATABASE_PATH` | 数据库文件路径 | 默认为 `/tmp/hnau_market.db` |

---

## 📊 常用操作

### 查看日志

1. 进入你的 Web Service 页面
2. 点击 **"Logs"** 标签
3. 可以看到构建日志和运行日志

### 重新部署

- **自动部署**：Push 到 GitHub 仓库后自动触发
- **手动部署**：点击 **"Manual Deploy"** → **"Deploy latest commit"**

### 修改代码后重新部署

1. 修改本地代码
2. Push 到 GitHub：
   ```bash
   git add .
   git commit -m "更新说明"
   git push origin main
   ```
3. Render 会自动检测到更新并重新部署

---

## 🔐 管理员账号

部署完成后，使用以下管理员账号登录：

- **用户名**：`admin`
- **密码**：`admin123`

⚠️ **重要**：首次登录后请立即修改管理员密码！

修改方法：
1. 登录管理员账号
2. 进入个人中心或管理后台
3. 修改密码

---

## ⚠️ 注意事项

### 1. 免费版限制

Render 免费版（Free）有以下限制：

| 限制项 | 说明 |
|--------|------|
| **休眠** | 15 分钟无活动后自动休眠 |
| **唤醒时间** | 首次访问可能需要 30 秒等待 |
| **数据库** | SQLite 保存在 `/tmp`，重启会丢失数据 |
| **带宽** | 每月 100GB 带宽 |
| **实例** | 只能运行 1 个实例 |

### 2. 数据持久化

**问题**：Render 免费版的 `/tmp` 目录在服务重启后会清空。

**解决方案**：

1. **使用 Render PostgreSQL**（免费版有 1GB）：
   - 创建 PostgreSQL 数据库
   - 修改代码使用 PostgreSQL 替代 SQLite

2. **使用 Render Disk**（付费功能）：
   - 开启持久化磁盘存储
   - 修改 `DATABASE_PATH` 指向持久化目录

3. **接受数据丢失**：
   - 免费版适合开发测试
   - 生产环境建议升级付费版

### 3. 安全性建议

- [ ] 首次登录后修改管理员密码
- [ ] 在环境变量中设置强密码的 `SECRET_KEY`
- [ ] 定期检查管理员后台的用户认证申请
- [ ] 如有安全顾虑，升级到付费版获得更好的隔离

---

## 🆘 常见问题

### Q1: 部署失败怎么办？

**检查步骤**：

1. 查看 Render 日志中的错误信息
2. 确认 `build.sh` 有执行权限（已设置）
3. 确认 `requirements.txt` 中的依赖都正确
4. 确认 GitHub 仓库中的文件结构正确

### Q2: 访问显示 "Service Unavailable"？

**可能原因**：
- 服务正在启动中（等待 1-2 分钟）
- 免费版实例已休眠（首次访问需要唤醒）
- 应用启动失败（查看日志排查）

### Q3: 数据库数据丢失？

这是免费版的已知限制。如需持久化存储：
1. 升级到付费版使用 Render Disk
2. 或切换到云数据库（如 Render PostgreSQL）

### Q4: 如何升级到付费版？

1. 进入 Web Service 设置
2. 点击 **"Plan"** 标签
3. 选择 **"Starter"** 或其他付费计划
4. 按月计费，无需长期合约

---

## 📞 获取帮助

- [Render 官方文档](https://render.com/docs)
- [Flask 官方文档](https://flask.palletsprojects.com/)
- 项目问题可在 GitHub 仓库提交 Issue

---

## 🎉 部署成功！

恭喜！你的河南农业大学闲置物品交易平台已经成功部署到互联网上了。

访问地址格式：`https://你的服务名.onrender.com`

例如：`https://hnau-market.onrender.com`

快去体验吧！ 🚀
