# Info Fetcher: 实时信息聚合与推送系统

本项目是一个自动化的信息聚合与推送平台，旨在监控并传递对您最重要的信息。它结合了社交媒体趋势分析和金融市场数据监控，并通过邮件系统为您提供及时的更新和预警。

## 核心功能

目前，平台包含两大核心功能模块：

### 1. X/Twitter 趋势监控
- **自动抓取**: 定时使用 Playwright 抓取 X (前身为 Twitter) 的“探索”页面，获取最新的热门趋势。
- **增量推送**: 智能比对新旧数据，只在发现新的、之前未出现过的热门趋势时，才会通过邮件进行推送。
- **数据持久化**: 所有抓取到的趋势都将被存储在数据库中，方便回顾。
- **Web 界面**: 提供一个简洁的 `/dashboard` 页面，用于展示所有已抓取的历史趋势。

### 2. 金融信息监控 (基于 TradingView)
- **可靠的数据源**: 所有金融数据均通过 `tradingview-ta` 库直接从 **TradingView** 获取，确保了数据的专业性、稳定性和实时性（需要您提供自己的 TradingView 账户）。
- **市场概览**: 提供一个 `/financials` 金融仪表盘，集中展示：
    - **主要市场指数**: 如 S&P 500 和 Nasdaq 100 的最新价格和涨跌幅。
    - **个股观察列表**: 自动获取并展示您在 `monitor_config.yaml` 文件中定义的所有股票的最新价格。
- **可配置的价格预警**: 
    - **灵活配置**: 您可以在 `monitor_config.yaml` 文件中轻松添加、修改或删除您关心的股票价格预警规则。
    - **即时推送**: 后台任务会以分钟级的频率检查股价，一旦满足您设定的条件（如高于或低于某个价格），系统会立即发送一封预警邮件到您的邮箱。

## 技术栈

- **Web 框架**: FastAPI
- **后台任务**: APScheduler
- **数据抓取**: Playwright (用于 X/Twitter), tradingview-ta (用于金融数据)
- **数据库**: SQLAlchemy, SQLite
- **前端**: Jinja2 模板引擎

## 如何运行

### 1. 安装依赖

首先，请确保您已安装所有必需的 Python 库：
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量 (关键步骤)

在启动应用前，您**必须**在您的终端中设置以下环境变量。这是确保所有功能正常运行的前提。

**对于 X/Twitter 抓取 (首次运行):**
```bash
# 您的 X/Twitter 登录用户名或邮箱
export X_USERNAME="your-x-username"
# 您的 X/Twitter 登录密码
export X_PASSWORD="your-x-password"
# (可选) 如果登录时需要手机号进行二次验证，请设置此项
export X_VERIFICATION_IDENTIFIER="your-phone-number"
```
> **注意**: 首次运行后，系统会生成一个 `sessions/x_session.json` 文件。在此之后，只要该文件不过期，您就不再需要设置 X 的环境变量。

**对于金融数据获取 (必需):**
```bash
# 您的 TradingView 登录用户名
export TRADINGVIEW_USERNAME="your-tv-username"
# 您的 TradingView 登录密码
export TRADINGVIEW_PASSWORD="your-tv-password"
```

**对于邮件推送 (必需):**
```bash
# 您的邮件服务器地址 (例如: smtp.gmail.com)
export MAIL_SERVER="smtp.example.com"
# 您的邮件服务器端口 (例如: 587)
export MAIL_PORT="587"
# 您的邮箱用户名
export MAIL_USERNAME="your-email@example.com"
# 您的邮箱密码或应用专用密码
export MAIL_PASSWORD="your-password"
# 您的发件邮箱地址
export MAIL_FROM="your-email@example.com"
# 收件人邮箱列表 (用逗号分隔)
export MAIL_TO="recipient1@example.com,recipient2@example.com"
```

### 3. 配置价格预警 (可选)

打开项目根目录下的 `monitor_config.yaml` 文件，您可以按照文件中的示例格式，添加或修改您想要监控的股票和预警条件。

### 4. 启动应用

完成所有配置后，执行以下命令来启动应用：
```bash
uvicorn app.main:app --reload
```

### 5. 访问应用

- **热点新闻**: `http://127.0.0.1:8000/dashboard`
- **金融仪表盘**: `http://127.0.0.1:8000/financials`

所有后台任务（抓取、预警检查、推送）都将自动运行。