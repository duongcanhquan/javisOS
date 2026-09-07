"""OpenMAIC public URL + rewrite — chống audioUrl host.docker.internal.

    python tests/run.py openmaic_urls

Không chạm mạng.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import openmaic_urls as om  # noqa: E402

_fails = []


def check(name, cond):
    print(("ok  " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


# ---- forward headers ----
h = om.public_forward_headers("https://openmaic.vietmycollege.com")
check("forward host domain", h.get("X-Forwarded-Host") == "openmaic.vietmycollege.com")
check("forward proto https", h.get("X-Forwarded-Proto") == "https")

h2 = om.public_forward_headers("http://165.101.46.238:3000")
check("forward host ip:port", h2.get("X-Forwarded-Host") == "165.101.46.238:3000")
check("forward proto http", h2.get("X-Forwarded-Proto") == "http")
check("forward empty → {}", om.public_forward_headers("") == {})

# ---- detect internal ----
check(
    "host.docker.internal là nội bộ",
    om.is_internal_openmaic_url("http://host.docker.internal:3000/api/classroom-media/x/audio/a.mp3"),
)
check("127.0.0.1 là nội bộ", om.is_internal_openmaic_url("http://127.0.0.1:3000/a.mp3"))
check("public không nội bộ", not om.is_internal_openmaic_url("https://openmaic.vietmycollege.com/a.mp3"))
check("chuỗi thường không phải URL", not om.is_internal_openmaic_url("xin chào"))

# ---- replace origin ----
u = om.replace_url_origin(
    "http://host.docker.internal:3000/api/classroom-media/cid/audio/tts.mp3",
    "https://openmaic.vietmycollege.com",
)
check(
    "replace origin giữ path",
    u == "https://openmaic.vietmycollege.com/api/classroom-media/cid/audio/tts.mp3",
)

# ---- deep rewrite payload ----
payload = {
    "result": {
        "classroomId": "abc",
        "url": "http://host.docker.internal:3000/classroom/abc",
    },
    "scenes": [
        {
            "actions": [
                {
                    "type": "speech",
                    "text": "Xin chào",
                    "audioUrl": "http://host.docker.internal:3000/api/classroom-media/abc/audio/t.mp3",
                    "audioId": "tts_s0_1",
                },
                {
                    "type": "spotlight",
                    "note": "http://example.com/keep",
                },
            ]
        }
    ],
}
fixed = om.rewrite_openmaic_payload(
    payload,
    "https://openmaic.vietmycollege.com",
    internal_bases=["http://host.docker.internal:3000"],
)
check(
    "rewrite classroom url",
    fixed["result"]["url"] == "https://openmaic.vietmycollege.com/classroom/abc",
)
check(
    "rewrite audioUrl",
    fixed["scenes"][0]["actions"][0]["audioUrl"]
    == "https://openmaic.vietmycollege.com/api/classroom-media/abc/audio/t.mp3",
)
check(
    "không đụng URL ngoài",
    fixed["scenes"][0]["actions"][1]["note"] == "http://example.com/keep",
)
check("không đụng text thường", fixed["scenes"][0]["actions"][0]["text"] == "Xin chào")

# ---- json text repair ----
raw = '{"audioUrl":"http://127.0.0.1:3000/api/classroom-media/x/audio/a.mp3"}'
out = om.rewrite_classroom_json_text(raw, "http://165.101.46.238:3000")
check("json text chứa public host", "http://165.101.46.238:3000/api/classroom-media/x/audio/a.mp3" in out)
check("json text hết 127.0.0.1", "127.0.0.1" not in out)

if _fails:
    print("FAILED:", ", ".join(_fails))
    raise SystemExit(1)
print("all ok")
