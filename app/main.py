from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from app.db.database import engine, Base, SessionLocal
from app.models.item import Item
from app.services.scraper import scrape_x_trends, run_scrape_x # 导入两个函数
from app.services.pusher import push_hotspots_by_email

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 配置模板
templates = Jinja2Templates(directory="app/templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用启动时执行
    print("应用启动...")
    
    # --- 启动时立即执行一次抓取和推送 ---
    print("立即执行一次启动抓取任务...")
    db = SessionLocal()
    try:
        await scrape_x_trends(db) # 直接await异步函数
        print("启动抓取任务完成。")
        
        print("立即执行一次启动推送任务...")
        push_hotspots_by_email() # 同步函数直接调用
        print("启动推送任务完成。")
    finally:
        db.close()
    
    # --- 初始化并启动定时任务 ---
    scheduler = BackgroundScheduler()
    # 定时任务需要运行在同步函数中，所以我们仍然使用run_scrape_x
    scheduler.add_job(run_scrape_x, 'interval', hours=1, id="scrape_x")
    scheduler.add_job(push_hotspots_by_email, 'cron', minute=5, id="push_email")
    scheduler.start()
    print("调度器已启动，定时抓取和推送任务已安排。")
    
    yield
    
    # 应用关闭时执行 (如果需要)
    print("应用关闭...")

app = FastAPI(
    title="实时热点聚合与推送系统",
    description="一个自动化的信息聚合工具，用于抓取、分析并推送热点信息。",
    version="0.1.0",
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

# 后续将在这里集成后台任务和API路由
