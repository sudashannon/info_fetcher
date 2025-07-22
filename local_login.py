import asyncio
import os
from playwright.async_api import async_playwright

SESSION_DIR = "sessions"
SESSION_PATH = os.path.join(SESSION_DIR, "x_session.json")

async def main():
    """
    启动一个非无头浏览器，让用户手动登录X，然后保存会话状态。
    """
    async with async_playwright() as p:
        # 确保 sessions 目录存在
        os.makedirs(SESSION_DIR, exist_ok=True)

        print("--- X/Twitter 手动登录程序 ---")
        print("一个浏览器窗口即将打开，请在其中完成登录。")
        print("请完成所有步骤，包括任何验证码或两步验证。")
        
        # 启动一个非无头的浏览器
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # 导航到登录页面
            await page.goto("https://x.com/login", timeout=60000)
            print("\n浏览器已打开。请在浏览器中手动完成登录...")

            # 等待用户登录成功，标志是URL包含 /home
            print("脚本正在等待您登录成功 (标志: URL跳转到 /home)...")
            await page.wait_for_url("**/home", timeout=300000) # 5分钟超时，足够手动操作

            print("\n检测到登录成功！")
            
            # 保存会话状态
            await context.storage_state(path=SESSION_PATH)
            print(f"会话文件已成功保存到: {SESSION_PATH}")
            print("现在您可以关闭此脚本，并将 sessions/x_session.json 文件上传到您的服务器。")

        except Exception as e:
            print(f"\n在等待登录时发生错误: {e}")
            print("请确保您已完全登录，并看到了您的主页时间线。")
        finally:
            # 给用户一点时间查看消息，然后关闭浏览器
            await page.wait_for_timeout(10000)
            await browser.close()
            print("\n浏览器已关闭。")

if __name__ == "__main__":
    asyncio.run(main())