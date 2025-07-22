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

import logging
from datetime import datetime

# ... (imports)

logger = logging.getLogger(__name__)

# ... (get_logged_in_page function)

async def login_to_x(page):
    """
    执行登录X的具体操作，采用模拟键盘回车的方式进行提交。
    """
    try:
        # --- 步骤 1: 导航并输入用户名 ---
        logger.info("导航到 X 登录页面...")
        await page.goto("https://x.com/login", wait_until='domcontentloaded')
        logger.info(f"输入用户名: {config.X_USERNAME}")
        username_input = page.locator('input[name="text"]')
        await username_input.fill(config.X_USERNAME)
        await username_input.press('Enter')
        logger.info("用户名已通过键盘回车提交。")

        # --- 步骤 2: 处理验证或密码 ---
        logger.info("等待验证或密码页面加载...")
        await page.wait_for_timeout(5000)

        # 判断当前页面状态
        password_input = page.locator('input[name="password"]')
        # 使用更精确的选择器来定位验证输入框
        verification_input = page.locator('input[data-testid="ocfEnterTextTextInput"]')

        if await verification_input.is_visible():
            logger.warning("检测到账户安全验证步骤。")
            identifier_to_use = config.X_VERIFICATION_IDENTIFIER or config.X_USERNAME
            logger.info(f"使用标识符 '{identifier_to_use}' 进行验证...")
            await verification_input.fill(identifier_to_use)
            await verification_input.press('Enter')
            logger.info("验证信息已通过键盘回车提交。")
            await page.wait_for_timeout(5000)

        # --- 步骤 3: 输入密码并登录 ---
        logger.info("等待密码输入框出现并输入密码...")
        await password_input.wait_for(state='visible', timeout=30000)
        await password_input.fill(config.X_PASSWORD)
        await password_input.press('Enter')
        logger.info("密码已通过键盘回车提交。")

        # --- 步骤 4: 验证登录成功 ---
        logger.info("等待登录成功后的主页加载...")
        await page.wait_for_url("**/home", timeout=60000)
        await page.wait_for_selector('[data-testid="primaryColumn"]', timeout=30000)
        logger.info("成功登录X！")

    except Exception as e:
        logger.error(f"登录X时发生决定性错误: {e}", exc_info=True)
        debug_dir = "debug"
        os.makedirs(debug_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = os.path.join(debug_dir, f"x_login_error_{timestamp}.png")
        await page.screenshot(path=screenshot_path)
        logger.info(f"已在 {screenshot_path} 保存最终错误截图。")
        raise e
