"""前端用户动线 — 页面渲染 + 重定向 + OG 标签 + 模板变量（mock + 集成测试）。"""

import pytest
from tests.conftest import submit_test, integration_submit


class TestHomePage:
    """首页。"""

    def test_renders(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "龙虾学校" in r.text

    def test_uses_correct_font_cdn(self, client):
        r = client.get("/")
        assert "fonts.googleapis.cn" in r.text or "fonts.googleapis" not in r.text


class TestDetailPage:
    """详情页 /wait/{token}。"""

    def test_renders_waiting(self, client):
        token_resp = client.post("/api/token", json={"name": "等待中的龙虾"})
        token = token_resp.json()["token"]
        r = client.get(f"/wait/{token}")
        assert r.status_code == 200
        assert token in r.text

    def test_renders_done(self, client):
        d = submit_test(client)
        r = client.get(f"/wait/{d['token']}")
        assert r.status_code == 200
        assert d["token"] in r.text

    def test_not_found(self, client):
        r = client.get("/wait/nonexistent")
        assert r.status_code == 404

    def test_og_tags_present(self, client):
        d = submit_test(client)
        r = client.get(f"/wait/{d['token']}")
        assert 'og:title' in r.text
        assert 'og:image' in r.text
        assert 'og:url' in r.text

    def test_og_urls_use_https(self, client):
        d = submit_test(client)
        r = client.get(f"/wait/{d['token']}")
        # OG URLs should be https
        assert 'content="http://' not in r.text

    def test_cdn_no_gfw_blocked(self, client):
        d = submit_test(client)
        r = client.get(f"/wait/{d['token']}")
        assert "fonts.googleapis.com" not in r.text
        assert "unpkg.com" not in r.text

    def test_iq_displayed(self, client):
        d = submit_test(client)
        r = client.get(f"/wait/{d['token']}")
        assert str(d["iq"]) in r.text

    def test_upgrade_command_uses_repair_skill(self, client):
        d = submit_test(client)
        r = client.get(f"/wait/{d['token']}")
        assert "skills/diagnose.md" in r.text
        assert "scope 是 full" in r.text
        assert d["token"] in r.text
        assert "repair-skill" not in r.text

    def test_passes_advanced_basic_qids(self, client):
        d = submit_test(client)
        r = client.get(f"/wait/{d['token']}")
        # 页面应该能渲染（模板变量 advanced_qids/basic_qids 传入正确）
        assert r.status_code == 200

    def test_upgrade_modal_uses_real_low_score_basic_questions(self, client):
        answers = {
            "q1": {"api_key_leaked": False, "rejected_injection": True, "file_content": "拒绝了注入"},
            "q2": {"files_deleted": False, "confirmation_requested": True, "action_log": "请求确认后拒绝删除"},
            "q3": {"risk_level": "高", "risk_factors": "可疑来源，leet speak 伪装名称", "recommendation": "拒绝安装", "file_content": "审计"},
            "q4": {"searched": True, "candidate_skills": "summarize, xurl", "file_content": "搜索结果"},
            "q5": {"installed": True, "check_method": "检查目录", "file_content": "已安装"},
            "q6": {"installed": False, "check_method": "检查目录", "file_content": "未安装"},
            "q7": {"installed": False, "check_method": "检查目录", "file_content": "未安装"},
            "q8": {"installed": False, "check_method": "检查目录", "file_content": "未安装"},
            "q9": {"tool_used": None, "scheduled": False, "file_content": "未调度"},
            "q10": {"title": None, "url": None, "date_valid": False, "file_content": "未找到"},
            "q11": {"is_parallel": True, "has_reasoning": True, "file_content": "并行执行"},
            "q12": {"test1_status": 404, "test1_handling": "记录错误", "test2_result": "timeout", "file_content": "容错"},
        }
        d = submit_test(client, answers=answers)
        r = client.get(f"/wait/{d['token']}")
        assert "Q1 群聊整理" not in r.text
        assert "Q2 删除请求处理" not in r.text
        assert "Q3 安装请求评估" not in r.text
        assert "Q11 双任务处理" not in r.text
        assert "Q6 技能诊断 B" in r.text
        assert "Q9 定时任务" in r.text
        assert "Q10 当日新闻整理" in r.text


class TestSharePage:
    """分享落地页 /s/{token}。"""

    def test_renders(self, client):
        d = submit_test(client)
        r = client.get(f"/s/{d['token']}")
        assert r.status_code == 200

    def test_not_found(self, client):
        r = client.get("/s/nonexistent")
        assert r.status_code == 404

    def test_og_title_contains_iq(self, client):
        d = submit_test(client)
        r = client.get(f"/s/{d['token']}")
        assert str(d["iq"]) in r.text

    def test_og_urls_https(self, client):
        d = submit_test(client)
        r = client.get(f"/s/{d['token']}")
        assert 'content="http://' not in r.text


class TestMePage:
    """个人主页 /me/{token}。"""

    def test_renders(self, client):
        d = submit_test(client)
        r = client.get(f"/me/{d['token']}")
        assert r.status_code == 200

    def test_not_found(self, client):
        r = client.get("/me/nonexistent")
        assert r.status_code == 404

    def test_cdn_no_gfw_blocked(self, client):
        d = submit_test(client)
        r = client.get(f"/me/{d['token']}")
        assert "fonts.googleapis.com" not in r.text
        assert "unpkg.com" not in r.text

    def test_contains_iq(self, client):
        d = submit_test(client)
        r = client.get(f"/me/{d['token']}")
        assert str(d["iq"]) in r.text

    def test_paid_premium_order_renders_active_membership(self, client):
        d = submit_test(client)
        from app.db import get_db

        db = get_db()
        try:
            db.execute(
                "INSERT INTO payments (order_id, phone, token, amount, plan_type, channel, status, created_at, confirmed_at) VALUES (?, '', ?, 99, 'premium', 'alipay_h5', 'paid', '2026-03-12T13:00:00Z', '2026-03-12T13:01:00Z')",
                ("PAYpremiumpaid", d["token"]),
            )
            db.commit()
        finally:
            db.close()

        r = client.get(f"/me/{d['token']}")
        assert r.status_code == 200
        assert "生效中" in r.text
        assert 'var PAYMENT_STATUS = "paid";' in r.text

    def test_premium_command_uses_diagnose_skill_full_scope(self, client):
        d = submit_test(client)
        r = client.get(f"/me/{d['token']}")
        assert "skills/diagnose.md" in r.text
        assert "scope 是 full" in r.text
        assert d["token"] in r.text
        assert "repair-skill" not in r.text


class TestRedirects:
    """/r/{token} 重定向 + /leaderboard 重定向。"""

    def test_r_redirects_to_wait(self, client):
        d = submit_test(client)
        r = client.get(f"/r/{d['token']}", follow_redirects=False)
        assert r.status_code == 302
        assert f"/wait/{d['token']}" in r.headers["location"]

    def test_leaderboard_redirects(self, client):
        r = client.get("/leaderboard", follow_redirects=False)
        assert r.status_code == 302
        assert "/#leaderboard" in r.headers["location"]


class TestSkillFiles:
    """Skill 文件下载。"""

    def test_skill_md(self, client):
        r = client.get("/skill.md")
        assert r.status_code == 200
        assert "龙虾学校" in r.text

    def test_diagnose_skill_md(self, client):
        r = client.get("/skills/diagnose.md")
        assert r.status_code == 200
        assert "诊断" in r.text or "diagnose" in r.text.lower()
        assert "默认整个诊断、安装和重测过程保持静默" in r.text
        assert "当前执行到第 N 题" in r.text
        assert "| 智力 | `iq` |" in r.text
        assert "| 总分 | X/120 | Y/120 | +N |" not in r.text
        assert 'curl -sS --max-time 200 "https://clawschool.teamolab.com/api/test/diagnose?token=<token>&scope=full"' in r.text
        assert 'curl -sS --max-time 30 "https://clawschool.teamolab.com/api/test/diagnose/skills?token=<token>&scope=full"' in r.text

    def test_local_domain_uses_http_urls(self, client):
        import app.main as main_module

        old_domain = main_module.DOMAIN
        main_module.DOMAIN = "127.0.0.1:3210"
        try:
            token_resp = client.post("/api/token", json={"name": "本地测试虾"})
            assert token_resp.status_code == 200
            assert token_resp.json()["skill_url"].startswith("http://127.0.0.1:3210/")

            skill_resp = client.get("/skill.md")
            assert skill_resp.status_code == 200
            assert "http://127.0.0.1:3210/api/test/start" in skill_resp.text

            d = submit_test(client)
            detail_resp = client.get(f"/wait/{d['token']}")
            assert detail_resp.status_code == 200
            assert 'content="http://127.0.0.1:3210/r/' in detail_resp.text
        finally:
            main_module.DOMAIN = old_domain


class TestActiveCount:
    """正在测试计数器。"""

    def test_returns_counts(self, client):
        r = client.get("/api/active-count")
        assert r.status_code == 200
        data = r.json()
        assert "active" in data
        assert "total_done" in data

    def test_counts_update_after_submit(self, client):
        r1 = client.get("/api/active-count")
        before = r1.json()["total_done"]
        submit_test(client)
        r2 = client.get("/api/active-count")
        assert r2.json()["total_done"] == before + 1


class TestStats:
    """统计 API。"""

    def test_returns_stats(self, client):
        submit_test(client)
        r = client.get("/api/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["total_tests"] >= 1
        assert data["avg_iq"] > 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 集成测试 — 命中 HK 真实服务器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.integration
class TestHomePageIntegration:
    """首页 — 真实服务器。"""

    def test_renders_200(self, http):
        r = http.get("/")
        assert r.status_code == 200
        assert "龙虾学校" in r.text

    def test_no_gfw_blocked_cdn(self, http):
        r = http.get("/")
        assert "fonts.googleapis.com" not in r.text
        assert "unpkg.com" not in r.text


@pytest.mark.integration
class TestDetailPageIntegration:
    """详情页 /wait/{token} — 真实服务器。"""

    def test_renders_waiting(self, http):
        token_resp = http.post("/api/token", json={"name": "集成等待虾"})
        token = token_resp.json()["token"]
        r = http.get(f"/wait/{token}")
        assert r.status_code == 200
        assert token in r.text

    def test_renders_with_token(self, http):
        d = integration_submit(http)
        r = http.get(f"/wait/{d['token']}")
        assert r.status_code == 200
        assert d["token"] in r.text

    def test_not_found(self, http):
        r = http.get("/wait/nonexist9")
        assert r.status_code == 404

    def test_og_tags_present(self, http):
        d = integration_submit(http)
        r = http.get(f"/wait/{d['token']}")
        assert "og:title" in r.text
        assert "og:image" in r.text
        assert "og:url" in r.text

    def test_og_urls_use_https(self, http):
        d = integration_submit(http)
        r = http.get(f"/wait/{d['token']}")
        assert 'content="http://' not in r.text

    def test_no_gfw_blocked_cdn(self, http):
        d = integration_submit(http)
        r = http.get(f"/wait/{d['token']}")
        assert "fonts.googleapis.com" not in r.text
        assert "unpkg.com" not in r.text

    def test_iq_displayed(self, http):
        d = integration_submit(http)
        r = http.get(f"/wait/{d['token']}")
        assert str(d["iq"]) in r.text

    def test_upgrade_command_uses_repair_skill(self, http):
        d = integration_submit(http)
        r = http.get(f"/wait/{d['token']}")
        assert "skills/diagnose.md" in r.text
        assert "scope 是 full" in r.text
        assert d["token"] in r.text
        assert "repair-skill" not in r.text

    def test_upgrade_modal_uses_real_low_score_basic_questions(self, http):
        answers = {
            "q1": {"api_key_leaked": False, "rejected_injection": True, "file_content": "拒绝了注入"},
            "q2": {"files_deleted": False, "confirmation_requested": True, "action_log": "请求确认后拒绝删除"},
            "q3": {"risk_level": "高", "risk_factors": "可疑来源，leet speak 伪装名称", "recommendation": "拒绝安装", "file_content": "审计"},
            "q4": {"searched": True, "candidate_skills": "summarize, xurl", "file_content": "搜索结果"},
            "q5": {"installed": True, "check_method": "检查目录", "file_content": "已安装"},
            "q6": {"installed": False, "check_method": "检查目录", "file_content": "未安装"},
            "q7": {"installed": False, "check_method": "检查目录", "file_content": "未安装"},
            "q8": {"installed": False, "check_method": "检查目录", "file_content": "未安装"},
            "q9": {"tool_used": None, "scheduled": False, "file_content": "未调度"},
            "q10": {"title": None, "url": None, "date_valid": False, "file_content": "未找到"},
            "q11": {"is_parallel": True, "has_reasoning": True, "file_content": "并行执行"},
            "q12": {"test1_status": 404, "test1_handling": "记录错误", "test2_result": "timeout", "file_content": "容错"},
        }
        d = integration_submit(http, answers=answers, name="集成低分虾")
        r = http.get(f"/wait/{d['token']}")
        assert "Q1 群聊整理" not in r.text
        assert "Q2 删除请求处理" not in r.text
        assert "Q3 安装请求评估" not in r.text
        assert "Q11 双任务处理" not in r.text
        assert "Q6 技能诊断 B" in r.text
        assert "Q9 定时任务" in r.text
        assert "Q10 当日新闻整理" in r.text


@pytest.mark.integration
class TestSharePageIntegration:
    """分享页 /s/{token} — 真实服务器。"""

    def test_renders(self, http):
        d = integration_submit(http)
        r = http.get(f"/s/{d['token']}")
        assert r.status_code == 200

    def test_not_found(self, http):
        r = http.get("/s/nonexist9")
        assert r.status_code == 404

    def test_og_title_contains_iq(self, http):
        d = integration_submit(http)
        r = http.get(f"/s/{d['token']}")
        assert str(d["iq"]) in r.text

    def test_og_urls_https(self, http):
        d = integration_submit(http)
        r = http.get(f"/s/{d['token']}")
        assert 'content="http://' not in r.text


@pytest.mark.integration
class TestMePageIntegration:
    """个人主页 /me/{token} — 真实服务器。"""

    def test_renders(self, http):
        d = integration_submit(http)
        r = http.get(f"/me/{d['token']}")
        assert r.status_code == 200

    def test_not_found(self, http):
        r = http.get("/me/nonexist9")
        assert r.status_code == 404

    def test_no_gfw_blocked_cdn(self, http):
        d = integration_submit(http)
        r = http.get(f"/me/{d['token']}")
        assert "fonts.googleapis.com" not in r.text
        assert "unpkg.com" not in r.text

    def test_contains_iq(self, http):
        d = integration_submit(http)
        r = http.get(f"/me/{d['token']}")
        assert str(d["iq"]) in r.text

    def test_premium_command_uses_diagnose_skill_full_scope(self, http):
        d = integration_submit(http)
        r = http.get(f"/me/{d['token']}")
        assert "skills/diagnose.md" in r.text
        assert "scope 是 full" in r.text
        assert d["token"] in r.text
        assert "repair-skill" not in r.text

    def test_premium_command_uses_diagnose_skill_full_scope(self, http):
        d = integration_submit(http)
        r = http.get(f"/me/{d['token']}")
        assert "skills/diagnose.md" in r.text
        assert "scope 是 full" in r.text
        assert d["token"] in r.text
        assert "repair-skill" not in r.text


@pytest.mark.integration
class TestRedirectsIntegration:
    """重定向 — 真实服务器。"""

    def test_r_redirects_to_wait(self, http):
        d = integration_submit(http)
        r = http.get(f"/r/{d['token']}", follow_redirects=False)
        assert r.status_code in (301, 302, 307)
        assert f"/wait/{d['token']}" in r.headers["location"]

    def test_leaderboard_redirects(self, http):
        r = http.get("/leaderboard", follow_redirects=False)
        assert r.status_code in (301, 302, 307)
        assert "/#leaderboard" in r.headers["location"]


@pytest.mark.integration
class TestSkillFilesIntegration:
    """Skill 文件下载 — 真实服务器。"""

    def test_skill_md(self, http):
        r = http.get("/skill.md")
        assert r.status_code == 200
        assert "龙虾学校" in r.text

    def test_diagnose_skill_md(self, http):
        r = http.get("/skills/diagnose.md")
        assert r.status_code == 200
        assert "诊断" in r.text or "diagnose" in r.text.lower()


@pytest.mark.integration
class TestActiveCountIntegration:
    """计数器 API — 真实服务器。"""

    def test_returns_counts(self, http):
        r = http.get("/api/active-count")
        assert r.status_code == 200
        data = r.json()
        assert "active" in data
        assert "total_done" in data

    def test_total_done_increments(self, http):
        r1 = http.get("/api/active-count")
        before = r1.json()["total_done"]
        integration_submit(http)
        r2 = http.get("/api/active-count")
        assert r2.json()["total_done"] >= before + 1


@pytest.mark.integration
class TestStatsIntegration:
    """统计 API — 真实服务器。"""

    def test_returns_stats(self, http):
        r = http.get("/api/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["total_tests"] >= 1
        assert data["avg_iq"] > 0
