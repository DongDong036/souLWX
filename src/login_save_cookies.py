"""
韭研公社登录并保存 Cookies 工具
使用方法：
1. 运行此脚本
2. 在弹出的浏览器窗口中手动登录
3. 登录成功后按回车键
4. 自动保存 cookies 到文件
"""

from playwright.sync_api import sync_playwright
import json
import time
from datetime import datetime

def login_and_save_cookies():
    """手动登录并保存 cookies"""
    print("=" * 60)
    print("韭研公社 - 登录并保存 Cookies 工具")
    print("=" * 60)
    print("\n步骤说明：")
    print("1. 即将打开浏览器窗口")
    print("2. 在浏览器中访问韭研公社并登录")
    print("3. 登录成功后，返回此窗口按回车键")
    print("4. 系统将自动保存 cookies")
    print("\n提示：可以使用微信、QQ 或账号密码登录\n")
    
    input("按回车键继续...")
    
    with sync_playwright() as p:
        # 启动浏览器（可见模式）
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        # 访问首页
        print("\n正在打开韭研公社...")
        page.goto('https://www.jiuyangongshe.com/', wait_until='networkidle')
        
        print("请在浏览器窗口中完成登录操作...")
        print("登录完成后，在此终端按回车键保存 cookies")
        
        # 等待用户登录
        input("\n按回车键表示已完成登录...")
        
        # 检查登录状态
        login_button = page.query_selector('.name[style*="color: #8590a6"]')
        if login_button:
            login_text = login_button.inner_text()
            if '登录' in login_text:
                print("\n❌ 检测到您还未登录，请完成登录后再按回车")
                input("登录完成后按回车...")
        
        # 获取 cookies
        print("\n正在获取 cookies...")
        cookies = context.cookies()
        print(f"✓ 成功获取 {len(cookies)} 个 cookies")
        
        # 保存 cookies
        cookies_data = {
            'cookies': cookies,
            'timestamp': datetime.now().isoformat(),
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        cookies_file = 'cookies.json'
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Cookies 已保存到：{cookies_file}")
        
        # 验证登录状态
        print("\n正在验证登录状态...")
        page.goto('https://www.jiuyangongshe.com/agree/me', wait_until='networkidle')
        time.sleep(2)
        
        # 检查是否成功访问个人中心
        page_content = page.content()
        if '登录注册' in page_content:
            print("⚠️  警告：个人中心页面仍显示登录提示，可能登录未生效")
        else:
            print("✓ 成功访问个人中心，登录状态正常")
        
        # 尝试访问通知
        try:
            notice_icon = page.query_selector('.ic_tongzhi')
            if notice_icon:
                print("✓ 找到通知图标")
                notice_icon.click()
                time.sleep(1)
                
                dropdown = page.query_selector('.downNoticesMenus')
                if dropdown:
                    menu_text = dropdown.inner_text()
                    if '暂无数据' in menu_text:
                        print("ℹ️  通知列表为空（这是正常的）")
                    else:
                        print(f"✓ 通知菜单内容：{menu_text[:50]}...")
        except Exception as e:
            print(f"ℹ️  通知检查：{e}")
        
        browser.close()
        
        print("\n" + "=" * 60)
        print("登录完成！Cookies 已保存！")
        print("=" * 60)
        print(f"\n保存的文件：{cookies_file}")
        print("下次使用可以直接运行采集脚本，无需再次登录")
        
        return True

def test_cookies():
    """测试保存的 cookies 是否有效"""
    print("=" * 60)
    print("测试 Cookies 有效性")
    print("=" * 60)
    
    cookies_file = 'cookies.json'
    try:
        with open(cookies_file, 'r', encoding='utf-8') as f:
            cookies_data = json.load(f)
        
        print(f"✓ 成功加载 cookies 文件")
        print(f"保存时间：{cookies_data.get('timestamp', '未知')}")
        print(f"cookies 数量：{len(cookies_data['cookies'])}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=cookies_data.get('user_agent', '')
            )
            context.add_cookies(cookies_data['cookies'])
            page = context.new_page()
            
            # 访问个人中心
            print("\n正在访问个人中心...")
            page.goto('https://www.jiuyangongshe.com/agree/me', wait_until='networkidle')
            time.sleep(3)
            
            # 检查登录状态
            page_content = page.content()
            if '登录注册' in page_content:
                print("❌ Cookies 已失效，需要重新登录")
                return False
            else:
                print("✓ Cookies 有效，登录状态正常")
                
                # 尝试获取广播消息
                print("\n尝试访问广播消息...")
                try:
                    # 点击通知图标
                    notice_icon = page.query_selector('.ic_tongzhi')
                    if notice_icon:
                        notice_icon.click()
                        time.sleep(1)
                        
                        # 查找广播消息选项
                        broadcast_option = page.query_selector('text=广播消息')
                        if broadcast_option:
                            print("✓ 找到广播消息选项")
                        else:
                            print("⚠️  未找到广播消息选项")
                except Exception as e:
                    print(f"ℹ️  广播消息检查：{e}")
            
            browser.close()
            return True
            
    except FileNotFoundError:
        print(f"❌ 未找到 cookies 文件：{cookies_file}")
        print("请先运行登录脚本保存 cookies")
        return False
    except Exception as e:
        print(f"❌ 测试失败：{e}")
        return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # 测试模式
        test_cookies()
    else:
        # 登录模式
        login_and_save_cookies()
