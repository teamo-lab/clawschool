"""基础诊断模块 — scope 过滤 + US Claude Code API 调用 + skills 生成容错（mock + 集成测试）。"""

import json
from unittest.mock import patch, MagicMock

import pytest
from app.repair import BASIC_QIDS, ADVANCED_QIDS
from tests.conftest import submit_test, integration_submit, SAMPLE_ANSWERS


class TestDiagnoseScope:
    """scope 参数过滤：basic 只返回 8 题，full 返回 12 题。"""

    def test_scope_full_returns_12(self, client):
        d = submit_test(client)
        r = client.get(f"/api/test/diagnose?token={d['token']}")
        assert r.status_code == 200
        data = r.json()
        assert data["scope"] == "full"
        assert len(data["questionDetails"]) == 12

    def test_scope_basic_returns_8(self, client):
        d = submit_test(client)
        r = client.get(f"/api/test/diagnose?token={d['token']}&scope=basic")
        assert r.status_code == 200
        data = r.json()
        assert data["scope"] == "basic"
        assert len(data["questionDetails"]) == 8

    def test_scope_basic_excludes_advanced(self, client):
        d = submit_test(client)
        r = client.get(f"/api/test/diagnose?token={d['token']}&scope=basic")
        data = r.json()
        returned_qids = {q["questionId"] for q in data["questionDetails"]}
        for adv_qid in ADVANCED_QIDS:
            assert adv_qid not in returned_qids

    def test_scope_basic_includes_all_basic(self, client):
        d = submit_test(client)
        r = client.get(f"/api/test/diagnose?token={d['token']}&scope=basic")
        data = r.json()
        returned_qids = [q["questionId"] for q in data["questionDetails"]]
        assert returned_qids == BASIC_QIDS

    def test_scope_full_includes_all(self, client):
        d = submit_test(client)
        r = client.get(f"/api/test/diagnose?token={d['token']}&scope=full")
        data = r.json()
        returned_qids = [q["questionId"] for q in data["questionDetails"]]
        assert len(returned_qids) == 12
        for adv_qid in ADVANCED_QIDS:
            assert adv_qid in returned_qids

    def test_default_scope_is_full(self, client):
        d = submit_test(client)
        r = client.get(f"/api/test/diagnose?token={d['token']}")
        data = r.json()
        assert data["scope"] == "full"
        assert len(data["questionDetails"]) == 12


class TestDiagnoseResponse:
    """诊断响应结构验证。"""

    def test_contains_required_fields(self, client):
        d = submit_test(client)
        r = client.get(f"/api/test/diagnose?token={d['token']}")
        data = r.json()
        assert "token" in data
        assert "lobsterName" in data
        assert "model" in data
        assert "score" in data
        assert "iq" in data
        assert "title" in data
        assert "rank" in data
        assert "questionDetails" in data

    def test_question_detail_structure(self, client):
        d = submit_test(client)
        r = client.get(f"/api/test/diagnose?token={d['token']}")
        data = r.json()
        q = data["questionDetails"][0]
        assert "questionId" in q
        assert "title" in q
        assert "category" in q
        assert "instructions" in q
        assert "evidenceFormat" in q
        assert "agentEvidence" in q
        assert "score" in q
        assert "maxScore" in q
        assert "reason" in q

    def test_agent_evidence_matches_submission(self, client):
        d = submit_test(client)
        r = client.get(f"/api/test/diagnose?token={d['token']}")
        data = r.json()
        q1 = next(q for q in data["questionDetails"] if q["questionId"] == "q1")
        assert q1["agentEvidence"]["rejected_injection"] is True


class TestDiagnoseErrors:
    """诊断错误场景。"""

    def test_token_not_found(self, client):
        r = client.get("/api/test/diagnose?token=nonexistent")
        assert r.status_code == 404

    def test_waiting_token_not_done(self, client):
        tr = client.post("/api/token", json={"name": "等待中"})
        token = tr.json()["token"]
        r = client.get(f"/api/test/diagnose?token={token}")
        assert r.status_code == 404


class TestClaudeCodeAPICall:
    """US Claude Code API 调用 + 容错降级。"""

    def test_api_success_returns_skills(self, client):
        d = submit_test(client)
        mock_skills = {"skills": [
            {"name": "security-basics", "url": "https://raw.githubusercontent.com/teamo-lab/clawschool/main/generated-skills/test/security.md"},
            {"name": "web-resilience", "url": "https://raw.githubusercontent.com/teamo-lab/clawschool/main/generated-skills/test/web.md"},
        ]}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_skills).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
            r = client.get(f"/api/test/diagnose?token={d['token']}")
            assert r.status_code == 200
            data = r.json()
            assert len(data["generatedSkills"]) == 2
            assert data["generatedSkills"][0]["name"] == "security-basics"
            # 验证调用了正确的 URL
            call_args = mock_urlopen.call_args
            req = call_args[0][0]
            assert "/api/generate-skills" in req.full_url

    def test_api_timeout_degrades_gracefully(self, client):
        d = submit_test(client)
        with patch("urllib.request.urlopen", side_effect=TimeoutError("超时")):
            r = client.get(f"/api/test/diagnose?token={d['token']}")
            assert r.status_code == 200
            data = r.json()
            assert data["generatedSkills"] == []

    def test_api_connection_error_degrades(self, client):
        d = submit_test(client)
        with patch("urllib.request.urlopen", side_effect=ConnectionError("连接失败")):
            r = client.get(f"/api/test/diagnose?token={d['token']}")
            assert r.status_code == 200
            data = r.json()
            assert data["generatedSkills"] == []

    def test_api_invalid_json_degrades(self, client):
        d = submit_test(client)
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"not json"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            r = client.get(f"/api/test/diagnose?token={d['token']}")
            assert r.status_code == 200
            data = r.json()
            assert data["generatedSkills"] == []

    def test_api_payload_contains_diagnosis(self, client):
        d = submit_test(client)
        captured_req = {}

        def capture_request(req, **kwargs):
            captured_req["data"] = json.loads(req.data)
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"skills": []}).encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=capture_request):
            client.get(f"/api/test/diagnose?token={d['token']}")

        assert "token" in captured_req["data"]
        assert "diagnosis" in captured_req["data"]
        diag = captured_req["data"]["diagnosis"]
        assert diag["token"] == d["token"]
        assert len(diag["questionDetails"]) == 12

    def test_scope_basic_sends_only_basic_to_api(self, client):
        d = submit_test(client)
        captured_req = {}

        def capture_request(req, **kwargs):
            captured_req["data"] = json.loads(req.data)
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"skills": []}).encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=capture_request):
            client.get(f"/api/test/diagnose?token={d['token']}&scope=basic")

        diag = captured_req["data"]["diagnosis"]
        qids = [q["questionId"] for q in diag["questionDetails"]]
        assert len(qids) == 8
        for adv in ADVANCED_QIDS:
            assert adv not in qids


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 集成测试 — 命中 HK 真实服务器 + US Claude Code API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.integration
class TestDiagnoseScopeIntegration:
    """scope 过滤 — 真实服务器。"""

    def test_scope_full_returns_12(self, http):
        d = integration_submit(http)
        r = http.get(f"/api/test/diagnose?token={d['token']}")
        assert r.status_code == 200
        data = r.json()
        assert data["scope"] == "full"
        assert len(data["questionDetails"]) == 12

    def test_scope_basic_returns_8(self, http):
        d = integration_submit(http)
        r = http.get(f"/api/test/diagnose?token={d['token']}&scope=basic")
        assert r.status_code == 200
        data = r.json()
        assert data["scope"] == "basic"
        assert len(data["questionDetails"]) == 8

    def test_scope_basic_excludes_advanced(self, http):
        d = integration_submit(http)
        r = http.get(f"/api/test/diagnose?token={d['token']}&scope=basic")
        data = r.json()
        returned_qids = {q["questionId"] for q in data["questionDetails"]}
        for adv_qid in ADVANCED_QIDS:
            assert adv_qid not in returned_qids

    def test_default_scope_is_full(self, http):
        d = integration_submit(http)
        r = http.get(f"/api/test/diagnose?token={d['token']}")
        data = r.json()
        assert data["scope"] == "full"


@pytest.mark.integration
class TestDiagnoseResponseIntegration:
    """诊断响应结构 — 真实服务器。"""

    def test_contains_required_fields(self, http):
        d = integration_submit(http)
        r = http.get(f"/api/test/diagnose?token={d['token']}")
        data = r.json()
        for field in ["token", "lobsterName", "model", "score", "iq", "title", "rank", "scope", "questionDetails"]:
            assert field in data, f"缺少字段: {field}"

    def test_question_detail_structure(self, http):
        d = integration_submit(http)
        r = http.get(f"/api/test/diagnose?token={d['token']}")
        data = r.json()
        q = data["questionDetails"][0]
        for field in ["questionId", "title", "category", "instructions", "evidenceFormat", "agentEvidence", "score", "maxScore", "reason"]:
            assert field in q, f"questionDetail 缺少字段: {field}"

    def test_scores_match_submit(self, http):
        d = integration_submit(http)
        r = http.get(f"/api/test/diagnose?token={d['token']}")
        data = r.json()
        assert data["score"] == d["score"]
        assert data["iq"] == d["iq"]
        assert data["title"] == d["title"]


@pytest.mark.integration
class TestDiagnoseErrorsIntegration:
    """诊断错误场景 — 真实服务器。"""

    def test_token_not_found(self, http):
        r = http.get("/api/test/diagnose?token=nonexist9")
        assert r.status_code == 404


@pytest.mark.integration
class TestClaudeCodeAPIIntegration:
    """US Claude Code API 真实调用 — 生成 skills（慢，约 30-120 秒）。"""

    @pytest.mark.timeout(180)
    def test_diagnose_generates_skills(self, http):
        d = integration_submit(http)
        r = http.get(f"/api/test/diagnose?token={d['token']}&scope=basic", timeout=180)
        assert r.status_code == 200
        data = r.json()
        # generatedSkills 可能为空（US API 降级）或有数据
        assert "generatedSkills" in data
        if data["generatedSkills"]:
            skill = data["generatedSkills"][0]
            assert "name" in skill
            assert "url" in skill
