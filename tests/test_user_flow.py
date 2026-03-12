"""前端用户动线 — 页面渲染 + 重定向 + OG 标签 + 模板变量。"""

import pytest
from tests.conftest import submit_test


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

    def test_upgrade_command_uses_diagnose_skill(self, client):
        d = submit_test(client)
        r = client.get(f"/wait/{d['token']}")
        assert "skills/diagnose.md" in r.text
        assert "scope" in r.text
        assert "basic" in r.text
        # 不再使用 repair-skill
        assert "repair-skill" not in r.text

    def test_passes_advanced_basic_qids(self, client):
        d = submit_test(client)
        r = client.get(f"/wait/{d['token']}")
        # 页面应该能渲染（模板变量 advanced_qids/basic_qids 传入正确）
        assert r.status_code == 200


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
