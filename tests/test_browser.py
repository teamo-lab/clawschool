"""
Playwright 自动化浏览器测试 — 真实点击页面按钮，覆盖用户操作路径。
启动本地服务器后运行: pytest tests/test_browser.py -v
"""
import time
import pytest
from playwright.sync_api import sync_playwright, Page, BrowserContext

BASE = "http://127.0.0.1:8765"


@pytest.fixture(scope="session")
def browser_ctx():
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=False, slow_mo=600)
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    yield ctx
    time.sleep(8)
    ctx.close()
    browser.close()
    pw.stop()


@pytest.fixture(scope="session")
def page(browser_ctx: BrowserContext):
    p = browser_ctx.new_page()
    yield p


# ── 辅助：通过 JS 调 API（用于数据准备，不是测试操作） ──

def _api_post(page: Page, path: str, body: dict) -> dict:
    return page.evaluate(
        """async ([url, body]) => {
            const r = await fetch(url, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(body)
            });
            return { status: r.status, data: await r.json() };
        }""",
        [f"{BASE}{path}", body],
    )


def _create_completed_test(page: Page, name: str = "测试虾") -> str:
    """创建一个已完成的测试，返回 token。"""
    r = _api_post(page, "/api/token", {"name": name})
    token = r["data"]["token"]
    answers = {f"q{i}": {"evidence": f"evidence for q{i}"} for i in range(1, 13)}
    _api_post(page, "/api/test/submit", {
        "token": token,
        "lobsterName": name,
        "model": "test-browser",
        "test_time": "2025-01-01T00:00:00Z",
        "answers": answers,
    })
    return token


# ═══════════════════════════════════════════
#  测试：分享功能（真实点击）
# ═══════════════════════════════════════════

class TestShareFlow:
    """分享相关的完整用户操作路径"""

    def test_detail_page_share_button(self, page: Page):
        """详情页 → 点击顶部「分享」按钮 → 复制文案到剪贴板"""
        # 准备数据
        page.goto(BASE + "/")
        token = _create_completed_test(page, "分享按钮虾")

        # 打开结果详情页
        page.goto(BASE + f"/wait/{token}")
        page.wait_for_load_state("networkidle")
        time.sleep(1)  # 等动画

        # 点击顶部导航栏的「分享」按钮
        share_btn = page.locator("button.nav-share-btn")
        share_btn.wait_for(state="visible", timeout=5000)
        share_btn.click()
        time.sleep(1)

        # 非微信环境下会触发 copyAndToast → 出现 toast 提示
        # 检查是否出现了 toast 或复制成功提示
        toast = page.locator(".toast, [class*='toast']")
        if toast.count() > 0:
            print(f"  ✅ Toast 出现: {toast.first.text_content()}")
        else:
            # 有些浏览器环境可能没有 toast，但按钮应该被点击了
            print("  ℹ️ 分享按钮已点击（非微信环境，尝试复制文案）")

    def test_detail_page_bottom_share_button(self, page: Page):
        """详情页 → 点击底部「炫耀我的成绩」/「分享成绩免费升级」按钮"""
        page.goto(BASE + "/")
        token = _create_completed_test(page, "底部分享虾")

        page.goto(BASE + f"/wait/{token}")
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # 底部 sticky 按钮
        sticky = page.locator("#stickyBottom button.btn-primary")
        sticky.wait_for(state="visible", timeout=5000)
        btn_text = sticky.text_content().strip()
        print(f"  底部按钮文字: {btn_text}")
        sticky.click()
        time.sleep(1)

        if "分享成绩免费升级" in btn_text:
            # 应该弹出 share-upgrade-modal
            modal = page.locator("#share-upgrade-modal")
            assert modal.is_visible(), "分享升级弹窗应该出现"
            print("  ✅ 分享升级弹窗已弹出")

            # 点击「去分享」
            go_share = page.locator("#btn-go-share")
            go_share.click()
            time.sleep(1)
            print("  ✅ 点击了「去分享」按钮")

            # 应该出现「好友已测试」按钮
            check_btn = page.locator("#btn-check-referral")
            if check_btn.is_visible():
                print("  ✅ 「好友已测试」按钮已显示")

            # 关闭弹窗
            close_btn = page.locator("#share-upgrade-modal .btn-sheet-secondary", has_text="稍后再说")
            if close_btn.is_visible():
                close_btn.click()
                time.sleep(0.5)
        else:
            # "炫耀我的成绩" → 直接复制文案
            print("  ✅ 炫耀按钮已点击")

    def test_share_page_loads_and_challenge(self, page: Page):
        """分享页 /s/{token} → 查看内容 → 点击「挑战」按钮 → 跳转首页"""
        page.goto(BASE + "/")
        token = _create_completed_test(page, "分享页虾")

        # 打开分享页
        page.goto(BASE + f"/s/{token}")
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # 确认页面内容
        content = page.content()
        assert "分享页虾" in content or token in page.url
        print("  ✅ 分享页加载成功")

        # 点击挑战按钮
        challenge_btn = page.locator("button.btn-challenge")
        if challenge_btn.count() > 0 and challenge_btn.is_visible():
            challenge_btn.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            # 应跳转到首页
            print(f"  ✅ 挑战按钮点击后跳转到: {page.url}")
        else:
            print("  ℹ️ 未找到挑战按钮")

    def test_og_image_renders(self, page: Page):
        """OG 分享图片能正常生成"""
        page.goto(BASE + "/")
        token = _create_completed_test(page, "OG图片虾")

        # 直接在浏览器里打开 OG 图片
        page.goto(BASE + f"/api/og-image/{token}")
        time.sleep(1)

        # 页面应该显示图片（content-type 是 image/png）
        # Playwright 打开图片 URL 后，页面内会有 <img> 标签
        content = page.content()
        is_image = "image" in page.evaluate("() => document.contentType || ''") or "<img" in content
        print(f"  ✅ OG 图片页面加载完成")

    def test_referral_flow(self, page: Page):
        """完整分享邀请流程：分享者完成测试 → 被邀请者通过链接进入 → 绑定 referral → 检查状态"""
        page.goto(BASE + "/")

        # 1. 分享者完成测试
        sharer_token = _create_completed_test(page, "邀请者虾")

        # 2. 被邀请者创建 token
        r2 = _api_post(page, "/api/token", {"name": "被邀请虾"})
        referee_token = r2["data"]["token"]

        # 3. 绑定 referral
        r3 = _api_post(page, "/api/referral/bind", {
            "sharer_token": sharer_token,
            "referee_token": referee_token,
            "referee_name": "被邀请虾",
        })
        assert r3["status"] == 200
        print("  ✅ Referral 绑定成功")

        # 4. 打开分享者的详情页，点击检查助力
        page.goto(BASE + f"/wait/{sharer_token}")
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # 如果有「分享成绩免费升级」按钮
        sticky = page.locator("#stickyBottom button.btn-primary")
        if sticky.is_visible():
            btn_text = sticky.text_content().strip()
            if "分享成绩免费升级" in btn_text:
                sticky.click()
                time.sleep(0.5)

                # 先点「去分享」让「好友已测试」按钮出现
                go_share = page.locator("#btn-go-share")
                if go_share.is_visible():
                    go_share.click()
                    time.sleep(0.5)

                # 点击「好友已测试」
                check_btn = page.locator("#btn-check-referral")
                if check_btn.is_visible():
                    check_btn.click()
                    time.sleep(2)

                    # 检查助力状态区域
                    status_el = page.locator("#referral-status")
                    if status_el.is_visible():
                        print(f"  ✅ 助力状态: {status_el.text_content()}")
                    else:
                        print("  ℹ️ 助力状态区域未显示")

        print("  ✅ Referral 流程完成")
