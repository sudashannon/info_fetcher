import asyncio
from playwright.async_api import async_playwright
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.item import Item
from app.services.login_manager import get_logged_in_page
from sqlalchemy import func # 导入 func

# X 探索/趋势页面
X_TRENDS_URL = "https://x.com/explore/tabs/trending"

def _parse_hot_score(text: str) -> float:
    """将 '5,123 posts' 或 '45.1K posts' 这样的文本解析为浮点数。"""
    if not text:
        return 0.0
    
    # 获取文本中的数字部分，例如 "45.1K posts" -> "45.1k"
    parts = text.lower().split()
    if not parts:
        return 0.0
    text = parts[0]
    text = text.replace(',', '')
    
    multiplier = 1
    if 'k' in text:
        multiplier = 1000
        text = text.replace('k', '')
    elif 'm' in text:
        multiplier = 1_000_000
        text = text.replace('m', '')

    try:
        return float(text) * multiplier
    except (ValueError, TypeError):
        return 0.0

async def scrape_x_trends(db: Session):
    """
    使用Playwright抓取X的趋势，更新或创建条目，并记录热度。
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
            items_updated = 0
            for container in trend_containers:
                try:
                    # 最终方案：通过唯一的“粗体”CSS类来定位标题，不再依赖顺序
                    title_element = container.locator('div.r-b88u0q > span').first
                    title = await title_element.text_content()
                    title = title.strip() if title else ""

                    if not title:
                        continue

                    # 提取热度值
                    post_count_text = ""
                    # 尝试找到包含 "posts" 的 span
                    # 在容器中查找所有span，然后检查文本内容
                    all_spans = await container.locator('span').all_text_contents()
                    for text in all_spans:
                        if text and 'posts' in text.lower():
                            post_count_text = text
                            break
                    
                    hot_score = _parse_hot_score(post_count_text)

                    from urllib.parse import quote
                    query = quote(title)
                    url = f"https://x.com/search?q={query}"
                    
                    item = db.query(Item).filter(Item.url == url).first()

                    if item:
                        # 更新已存在的条目
                        item.hot_score = hot_score
                        item.updated_at = func.now()
                        items_updated += 1
                        print(f"[更新] '{title}' (热度: {hot_score})")
                    else:
                        # 创建新条目
                        new_item = Item(
                            title=title,
                            url=url,
                            source="X 趋势",
                            hot_score=hot_score
                        )
                        db.add(new_item)
                        items_added += 1
                        print(f"[新增] '{title}' (热度: {hot_score})")

                except Exception as e:
                    print(f"解析单个趋势时出错: {e}")

            db.commit()
            print(f"抓取完成，新增 {items_added} 条，更新 {items_updated} 条。")

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
