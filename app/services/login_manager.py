import os
from playwright.async_api import async_playwright, Browser
from app.core import config

SESSION_DIR = "sessions"

async def get_logged_in_page(playwright, site_name: str) -> Browser:
    """
    获取一个已登录的Playwright页面对象。
    如果存在有效的会话文件，则加载它；否则，执行登录并保存会话。

    Args:
        playwright: async_playwright的实例。
        site_name: 网站标识符 (例如, 'x')。

    Returns:
        一个已经登录的Playwright页面对象。
    """
    session_path = os.path.join(SESSION_DIR, f"{site_name}_session.json")
    browser = await playwright.chromium.launch(headless=True)
    context = None

    if os.path.exists(session_path):
        print(f"找到 {site_name} 的会话文件，正在加载...")
        try:
            context = await browser.new_context(storage_state=session_path)
            page = await context.new_page()
            # 验证登录是否仍然有效
            await page.goto("https://x.com", wait_until='domcontentloaded')
            # 等待一个明确的、代表已登录的元素出现，比如“主页”时间线
            await page.wait_for_selector('[data-testid="primaryColumn"]', timeout=30000)
            print("会话有效，登录成功！")
            return page
        except Exception as e:
            print(f"加载会话失败: {e}，将执行手动登录。")
            if context:
                await context.close()

    # 如果没有有效的会话，执行登录
    print("未找到有效会话，开始执行首次登录...")
    if site_name == 'x':
        page = await browser.new_page()
        await login_to_x(page)
        # 保存会话状态
        await page.context.storage_state(path=session_path)
        print(f"新的 {site_name} 会话已保存到 {session_path}")
        return page
    else:
        raise ValueError(f"不支持的网站: {site_name}")

async def login_to_x(page):
    """
    执行登录X的具体操作。
    """
    await page.goto("https://x.com/login")
    
    # 输入用户名
    await page.locator('input[name="text"]').fill(config.X_USERNAME)
    await page.get_by_role("button", name="Next").click()
    
    # 输入密码
    await page.locator('input[name="password"]').fill(config.X_PASSWORD)
    await page.get_by_role("button", name="Log in").click()
    
    # 等待登录成功后的主页加载
    await page.wait_for_url("**/home", timeout=60000)
    print("成功登录X！")
