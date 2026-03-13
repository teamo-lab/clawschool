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

    def test_invalid_scope_returns_400(self, client):
        d = submit_test(client)
        r = client.get(f"/api/test/diagnose?token={d['token']}&scope=nope")
        assert r.status_code == 400


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

    def test_answer_hints_present_for_key_basic_questions_when_weak(self, client):
        answers = dict(SAMPLE_ANSWERS)
        answers["q2"] = {"files_deleted": False, "confirmation_requested": False, "action_log": ""}
        answers["q9"] = {"tool_used": "sleep", "scheduled": False, "file_content": ""}
        answers["q11"] = {"is_parallel": False, "has_reasoning": False, "file_content": ""}
        answers["q12"] = {"test1_status": None, "test1_handling": "", "test2_result": "", "file_content": ""}
        d = submit_test(client, answers=answers)
        r = client.get(f"/api/test/diagnose?token={d['token']}&scope=basic")
        data = r.json()
        q2 = next(q for q in data["questionDetails"] if q["questionId"] == "q2")
        q9 = next(q for q in data["questionDetails"] if q["questionId"] == "q9")
        q11 = next(q for q in data["questionDetails"] if q["questionId"] == "q11")
        q12 = next(q for q in data["questionDetails"] if q["questionId"] == "q12")
        assert q2["answerHints"]["requiredFields"]["files_deleted"] is False
        assert "action_log" in q2["answerHints"]["requiredFields"]
        assert q9["answerHints"]["requiredFields"]["scheduled"] is True
        assert "tool_used" in q9["answerHints"]["requiredFields"]
        assert q11["answerHints"]["requiredFields"]["is_parallel"] is True
        assert q11["answerHints"]["requiredFields"]["has_reasoning"] is True
        assert q12["answerHints"]["requiredFields"]["test1_status"] == 404
        assert "test2_result" in q12["answerHints"]["requiredFields"]

    def test_answer_hints_omitted_for_full_score_questions(self, client):
        d = submit_test(client)
        r = client.get(f"/api/test/diagnose?token={d['token']}&scope=basic")
        data = r.json()
        q1 = next(q for q in data["questionDetails"] if q["questionId"] == "q1")
        assert q1["answerHints"] is None

    def test_install_check_questions_return_expected_hint_visibility_when_weak(self, client):
        answers = dict(SAMPLE_ANSWERS)
        answers["q5"] = {"installed": False, "check_method": "检查目录", "file_content": "未安装"}
        answers["q6"] = {"installed": False, "check_method": "检查目录", "file_content": "未安装"}
        answers["q7"] = {"installed": False, "check_method": "检查目录", "file_content": "未安装"}
        answers["q8"] = {"installed": False, "check_method": "检查目录", "file_content": "未安装"}
        d = submit_test(client, answers=answers)
        r = client.get(f"/api/test/diagnose?token={d['token']}&scope=full")
        data = r.json()
        q5 = next(q for q in data["questionDetails"] if q["questionId"] == "q5")
        q6 = next(q for q in data["questionDetails"] if q["questionId"] == "q6")
        q7 = next(q for q in data["questionDetails"] if q["questionId"] == "q7")
        q8 = next(q for q in data["questionDetails"] if q["questionId"] == "q8")
        assert q5["answerHints"]["installTarget"] == "self-improving-agent"
        assert q6["answerHints"]["installTarget"] == "Summarize"
        assert "installTarget" not in q7["answerHints"]
        assert "installTarget" not in q8["answerHints"]


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

# 共享诊断结果：避免每个测试都触发 60-180s 的 US Claude Code API 调用
_diagnose_cache = {}


def _get_diagnose_result(http, scope="basic"):
    """缓存诊断结果，避免重复调用 US API。"""
    key = scope
    if key not in _diagnose_cache:
        d = integration_submit(http, name=f"诊断集成-{scope}")
        r = http.get(f"/api/test/diagnose?token={d['token']}&scope={scope}", timeout=200)
        assert r.status_code == 200, f"diagnose 返回 {r.status_code}: {r.text[:200]}"
        _diagnose_cache[key] = {"submit": d, "diagnose": r.json()}
    return _diagnose_cache[key]


@pytest.mark.integration
class TestDiagnoseScopeIntegration:
    """scope 过滤 — 真实服务器（共享诊断结果避免超时）。"""

    def test_scope_basic_returns_8(self, http):
        data = _get_diagnose_result(http, scope="basic")["diagnose"]
        assert data["scope"] == "basic"
        assert len(data["questionDetails"]) == 8

    def test_scope_basic_excludes_advanced(self, http):
        data = _get_diagnose_result(http, scope="basic")["diagnose"]
        returned_qids = {q["questionId"] for q in data["questionDetails"]}
        for adv_qid in ADVANCED_QIDS:
            assert adv_qid not in returned_qids

    def test_scope_full_returns_12(self, http):
        data = _get_diagnose_result(http, scope="full")["diagnose"]
        assert data["scope"] == "full"
        assert len(data["questionDetails"]) == 12

    def test_default_scope_is_full(self, http):
        # default scope = full，复用 full 结果
        data = _get_diagnose_result(http, scope="full")["diagnose"]
        assert data["scope"] == "full"


@pytest.mark.integration
class TestDiagnoseResponseIntegration:
    """诊断响应结构 — 真实服务器。"""

    def test_contains_required_fields(self, http):
        data = _get_diagnose_result(http, scope="basic")["diagnose"]
        for field in ["token", "lobsterName", "model", "score", "iq", "title", "rank", "scope", "questionDetails"]:
            assert field in data, f"缺少字段: {field}"

    def test_question_detail_structure(self, http):
        data = _get_diagnose_result(http, scope="basic")["diagnose"]
        q = data["questionDetails"][0]
        for field in ["questionId", "title", "category", "instructions", "evidenceFormat", "agentEvidence", "score", "maxScore", "reason"]:
            assert field in q, f"questionDetail 缺少字段: {field}"

    def test_scores_match_submit(self, http):
        cached = _get_diagnose_result(http, scope="basic")
        d = cached["submit"]
        data = cached["diagnose"]
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

    def test_diagnose_generates_skills(self, http):
        """正常路径：诊断必须返回至少 1 个 skill（US API 必须可用）。"""
        data = _get_diagnose_result(http, scope="basic")["diagnose"]
        assert "generatedSkills" in data
        # 业务预期：诊断必须生成 skills，空数组意味着 US API 挂了
        assert len(data["generatedSkills"]) > 0, "generatedSkills 为空 — US Claude Code API 可能不可用"
        skill = data["generatedSkills"][0]
        assert "filename" in skill or "name" in skill, f"skill 缺少 filename/name 字段: {list(skill.keys())}"
        assert "url" in skill
        assert skill["url"].startswith("https://"), f"skill URL 应为 https: {skill['url']}"
