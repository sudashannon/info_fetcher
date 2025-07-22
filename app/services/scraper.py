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

from app.services.pusher import push_email

async def scrape_x_trends(db: Session):
    """
    使用Playwright抓取X的趋势，更新或创建条目，并推送新条目。
    Args:
        db: SQLAlchemy数据库会话
    """
    print("开始使用Playwright抓取X趋势...")
    new_items_for_push = []  # 用于收集新条目以进行推送
    async with async_playwright() as p:
        page = None
        try:
            page = await get_logged_in_page(p, 'x')
            
            print(f"正在访问: {X_TRENDS_URL}")
            await page.goto(X_TRENDS_URL, wait_until='domcontentloaded', timeout=60000)
            print("页面导航完成，等待趋势数据...")

            timeline_selector = 'div[aria-label="时间线：探索"]'
            await page.wait_for_selector(timeline_selector, timeout=30000)
            print("主时间线已加载。")

            trend_selector = 'div[data-testid="trend"]'
            await page.locator(timeline_selector).locator(trend_selector).first.wait_for(timeout=30000)
            print("第一个趋势项目已渲染。")

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
                    title_element = container.locator('div.r-b88u0q > span').first
                    title = await title_element.text_content()
                    title = title.strip() if title else ""

                    if not title:
                        continue

                    post_count_text = ""
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
                        item.hot_score = hot_score
                        item.updated_at = func.now()
                        items_updated += 1
                        print(f"[更新] '{title}' (热度: {hot_score})")
                    else:
                        new_item = Item(
                            title=title,
                            url=url,
                            source="X 趋势",
                            hot_score=hot_score
                        )
                        db.add(new_item)
                        new_items_for_push.append(new_item) # 收集新条目
                        items_added += 1
                        print(f"[新增] '{title}' (热度: {hot_score})")

                except Exception as e:
                    print(f"解析单个趋势时出错: {e}")

            db.commit()
            print(f"抓取完成，新增 {items_added} 条，更新 {items_updated} 条。")

            # 如果有新条目，则触发邮件推送
            if new_items_for_push:
                print(f"发现 {len(new_items_for_push)} 个新条目，准备推送...")
                push_email(new_items_for_push)
            else:
                print("没有发现新条目，本次不推送。")

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
