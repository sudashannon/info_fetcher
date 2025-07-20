# 实时热点聚合与推送系统

本项目旨在开发一个自动化的信息聚合工具，用于抓取、分析并推送来自各大门户网站和社交平台的热点信息。

## 环境依赖

本项目依赖 Python 3.8+ 环境。在开始之前，请确保您已安装 `pip` 和 `venv`。

```bash
# 更新包列表
sudo apt-get update

# 安装pip
sudo apt-get install -y python3-pip

# 安装venv
sudo apt-get install -y python3.8-venv
```

## 开发计划

### 第一阶段 (MVP)

- [x] 初始化项目结构
- [x] 实现核心抓取逻辑 (微博热搜)
- [x] 设计数据库模型 (SQLite)
- [x] 实现基本的数据存储功能
- [x] 实现定时任务抓取
- [x] 实现邮件推送功能

## 如何运行

1.  **安装依赖:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **配置邮件:**

    打开 `app/core/config.py` 文件，修改以下邮件配置项。建议使用环境变量进行配置。

    ```python
    MAIL_SERVER = "smtp.example.com"
    MAIL_PORT = 587
    MAIL_USERNAME = "your-email@example.com"
    MAIL_PASSWORD = "your-password"
    MAIL_FROM = "your-email@example.com"
    MAIL_TO = ["recipient1@example.com", "recipient2@example.com"]
    ```

3.  **启动应用:**

    ```bash
    uvicorn app.main:app --reload
    ```

4.  **访问:**

    应用启动后，可以访问 `http://127.0.0.1:8000` 查看欢迎信息。

    爬虫和邮件推送任务将在后台自动运行。

## 如何测试

项目包含一套完整的单元测试和集成测试，以确保代码质量。

1.  **安装测试依赖:**

    `pytest` 已经包含在 `requirements.txt` 中。

2.  **运行测试:**

    在项目根目录下执行以下命令：

    ```bash
    pytest
    ```

    或者，如果 `pytest` 命令未找到，请使用：

    ```bash
    python3 -m pytest
    ```
