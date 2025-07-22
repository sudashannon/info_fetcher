import os

# 邮件配置
# 警告：在生产环境中，请务必使用环境变量替换这些硬编码的值！
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.example.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "your-email@example.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "your-password")
MAIL_FROM = os.getenv("MAIL_FROM", "your-email@example.com")

# 推送目标邮箱
MAIL_TO = os.getenv("MAIL_TO", "recipient@example.com").split(",")

# X (Twitter) 登录凭据
# 警告：请务必通过环境变量提供这些值！
X_USERNAME = os.getenv("X_USERNAME")
X_PASSWORD = os.getenv("X_PASSWORD")
# 在登录过程中，如果触发了安全验证，使用此标识符（通常是手机号或邮箱）进行验证
X_VERIFICATION_IDENTIFIER = os.getenv("X_VERIFICATION_IDENTIFIER")

# Financial Modeling Prep (FMP) API 密钥
# 警告：请务必通过环境变量提供此值！
FMP_API_KEY = os.getenv("FMP_API_KEY")

# TradingView 凭据
# 警告：请务必通过环境变量提供这些值！
TRADINGVIEW_USERNAME = os.getenv("TRADINGVIEW_USERNAME")
TRADINGVIEW_PASSWORD = os.getenv("TRADINGVIEW_PASSWORD")
