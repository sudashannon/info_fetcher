import asyncio
from playwright.async_api import async_playwright
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.item import Item
from app.services.login_manager import get_logged_in_page

# X 探索/趋势页面
X_TRENDS_URL = "https://x.com/explore/tabs/trending"

async def scrape_x_trends(db: Session):
    """
    使用Playwright抓取X的趋势并存入数据库
    Args:
        db: SQLAlchemy数据库会话
    """
    print("开始使用Playwright抓取X趋势...")
    async with async_playwright() as p:
        page = None
        try:
            page = await get_logged_in_page(p, 'x')
            
            print(f"正在访问: {X_TRENDS_URL}")
            # 使用 'domcontentloaded' 代替 'networkidle'，避免因持续的背景请求而超时
            await page.goto(X_TRENDS_URL, wait_until='domcontentloaded', timeout=60000)
            print("页面导航完成，等待趋势数据...")

            # 1. 等待包含所有趋势的主时间线容器出现
            timeline_selector = 'div[aria-label="时间线：探索"]'
            await page.wait_for_selector(timeline_selector, timeout=30000)
            print("主时间线已加载。")

            # 2. 等待第一个趋势项目在主时间线内出现，确保内容已填充
            trend_selector = 'div[data-testid="trend"]'
            print("正在等待第一个趋势项目渲染...")
            await page.locator(timeline_selector).locator(trend_selector).first.wait_for(timeout=30000)
            print("第一个趋势项目已渲染。")

            # 3. 现在可以安全地获取所有趋势容器
            timeline = page.locator(timeline_selector)
            trend_containers = await timeline.locator(trend_selector).all()

            if not trend_containers:
                print("未找到趋势容器，可能是页面结构已更改。")
                await page.screenshot(path="/tmp/x_scrape_no_elements.png")
                print("已在 /tmp/x_scrape_no_elements.png 保存截图。")
                return

            items_added = 0
            for container in trend_containers:
                try:
                    # 最终方案：通过唯一的“粗体”CSS类来定位标题，不再依赖顺序
                    title_element = container.locator('div.r-b88u0q > span').first
                    title = await title_element.text_content()

                    if title and title.strip():
                        # 手动构建URL
                        from urllib.parse import quote
                        query = quote(title.strip())
                        url = f"https://x.com/search?q={query}"
                        
                        print(f"[调试] 找到的趋势: '{title.strip()}' -> {url}")

                        exists = db.query(Item).filter(Item.url == url).first()
                        if not exists:
                            new_item = Item(
                                title=title.strip(),
                                url=url,
                                source="X 趋势",
                                hot_score=0
                            )
                            db.add(new_item)
                            items_added += 1
                except Exception as e:
                    print(f"解析单个趋势时出错: {e}")

            db.commit()
            print(f"抓取完成，共向数据库添加了 {items_added} 个新的X趋势。")

        except Exception as e:
            print(f"使用Playwright抓取时发生严重错误: {e}")
            if page and not page.is_closed():
                await page.screenshot(path="/tmp/x_scrape_error.png")
                print("已在 /tmp/x_scrape_error.png 保存错误截图。")
            db.rollback()
        finally:
            if page and not page.is_closed():
                await page.context.browser.close()
                print("Playwright浏览器已关闭。")

def run_scrape_x():
    """创建一个新的会话来异步运行X爬虫"""
    db = SessionLocal()
    try:
        asyncio.run(scrape_x_trends(db))
    finally:
        db.close()

if __name__ == '__main__':
    # 用于直接运行测试
    run_scrape_x()