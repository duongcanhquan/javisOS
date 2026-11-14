"""Thẻ gói mất đăng nhập: nhận ra câu từ chối, và _route_ready bỏ qua thẻ đã đánh dấu.

    python tests/run.py signin_loss
"""
from _paths import SERVER  # noqa: E402,F401
import time

import signin_loss


def test_detector_catches_plan_refusals_and_leaves_real_answers_alone():
    assert signin_loss.is_signin_error("Please run /login")
    assert signin_loss.is_signin_error(
        "Your refresh token was already used. Please log out and sign in again.")
    assert signin_loss.is_signin_error("ChatGPT 401: token_invalidated")
    assert not signin_loss.is_signin_error("MCP server returned 401 Unauthorized")
    long_answer = "Not logged in\n" + ("nội dung thật. " * 40)
    assert not signin_loss.is_signin_error(long_answer, answer=True)
    assert signin_loss.is_signin_error("Not logged in · Please run /login", answer=True)


def test_a_signed_out_card_is_not_ready_until_the_window_ends():
    import main
    prov = "openai-oauth"
    main._SIGNED_OUT[prov] = time.time() + 600
    try:
        assert main._signed_out_until(prov) > time.time()
        assert main._route_ready({}, prov) is False
        main._SIGNED_OUT[prov] = time.time() - 1
        assert main._signed_out_until(prov) == 0.0
        assert "mất đăng nhập" in main._signin_lost_message(prov)
    finally:
        main._SIGNED_OUT.pop(prov, None)


def test_claude_exit_names_the_three_common_causes():
    import claude_exit_reason as cer
    bare = "Command failed with exit code 1 (exit code: 1)\nError output: Check stderr output for details"
    assert cer.explain("a normal answer", ["cannot be used with root/sudo"]) is None
    root = cer.explain(bare, ["--dangerously-skip-permissions cannot be used with root/sudo privileges"])
    assert root and "root" in root.lower()
    mcp = cer.explain(bare, ["Error: Invalid MCP configuration:"])
    assert mcp and "MCP" in mcp
    old = cer.explain(bare, ["error: unknown option '--effort'"])
    assert old and "claude update" in old
