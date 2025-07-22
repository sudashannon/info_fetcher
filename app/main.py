from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from app.db.database import engine, Base, SessionLocal
from app.models.item import Item
from app.services.scraper import run_scrape_x
from app.services.pusher import push_market_summary
from app.services.alerter import check_price_alerts
from app.services.market_data_fetcher import get_market_summary
from datetime import datetime, timedelta

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 配置模板
templates = Jinja2Templates(directory="app/templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("应用启动...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_scrape_x, 'interval', hours=1, id="scrape_x")
    scheduler.add_job(push_market_summary, 'interval', minutes=15, id="push_market_summary")
    scheduler.add_job(check_price_alerts, 'interval', minutes=1, id="check_price_alerts")
    scheduler.add_job(run_scrape_x, 'date', run_date=datetime.now() + timedelta(seconds=2), id="scrape_x_initial")
    scheduler.start()
    print("调度器已启动，所有定时任务已安排。")
    yield
    print("应用关闭...")
    scheduler.shutdown()

app = FastAPI(
    title="实时热点聚合与推送系统",
    description="一个自动化的信息聚合工具，用于抓取、分析并推送热点信息。",
    version="0.3.0",
    lifespan=lifespan
)

@app.get("/", tags=["首页"])
async def read_root():
    return {"message": "欢迎使用实时热点聚合与推送系统"}

@app.get("/dashboard", tags=["管理后台"])
async def view_dashboard(request: Request):
    db = SessionLocal()
    try:
        items = db.query(Item).order_by(Item.created_at.desc()).limit(50).all()
        return templates.TemplateResponse(request, "index.html", {"items": items})
    finally:
        db.close()

@app.get("/financials", tags=["管理后台"])
def view_financials(request: Request):
    try:
        summary_data = get_market_summary()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return templates.TemplateResponse(
            request,
            "financial_dashboard.html",
            {
                "summary": summary_data,
                "timestamp": timestamp,
                "error": None
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            request,
            "financial_dashboard.html",
            {
                "summary": None,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e)
            }
        )