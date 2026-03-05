from pathlib import Path
import re

# ---------- claude_client.py ----------
p = Path("automation/common/claude_client.py")
s = p.read_text(encoding="utf-8")

# 1) import os
if not re.search(r'^\s*import\s+os\s*$', s, flags=re.M):
    s = "import os\n" + s

# 2) helper
if "def _model_from_env" not in s:
    helper = """
def _model_from_env(kind: str | None = None) -> str:
    # kind: "ARTICLE" / "FAST" / None
    if kind:
        v = os.getenv(f"CLAUDE_MODEL_{kind}")
        if v:
            return v
    return os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
"""
    # class ClaudeClient の直前に入れる
    s = re.sub(r'(^class\s+ClaudeClient:\s*)', helper + r"\n\1", s, flags=re.M)

# 3) __init__ を model_kind 対応にする
# すでに対応済みなら何もしない
if "model_kind" not in s:
    # def __init__(self, api_key: str ...): を探して差し替え
    s = re.sub(
        r'def\s+__init__\s*\(\s*self\s*,\s*api_key\s*:\s*str\s*\)\s*:\s*',
        'def __init__(self, api_key: str, model: str | None = None, model_kind: str | None = None):\n',
        s
    )

# 4) self.model の代入を必ず入れる
# 既存の self.model= があれば置換、なければ self.api_key= の直後に挿入
if re.search(r'^\s*self\.model\s*=', s, flags=re.M):
    s = re.sub(r'^\s*self\.model\s*=.*$', '        self.model = model or _model_from_env(model_kind)', s, flags=re.M)
else:
    s = re.sub(
        r'(^\s*self\.api_key\s*=\s*api_key\s*$)',
        r'\1\n        self.model = model or _model_from_env(model_kind)',
        s,
        flags=re.M
    )

p.write_text(s, encoding="utf-8")
print("patched:", p)

# ---------- run_auto.py ----------
rp = Path("run_auto.py")
rs = rp.read_text(encoding="utf-8")

# client = ClaudeClient(...) を用途別に作る（既にあればスキップ）
if "fast_client" not in rs and "article_client" not in rs:
    rs = re.sub(
        r'(\s*)client\s*=\s*ClaudeClient\(\s*cfg\.anthropic_api_key\s*\)\s*',
        r'\1fast_client = ClaudeClient(cfg.anthropic_api_key, model_kind="FAST")\n'
        r'\1article_client = ClaudeClient(cfg.anthropic_api_key, model_kind="ARTICLE")\n',
        rs
    )

# 呼び出し先の「client」を用途に合わせて置換（存在するものだけ置換される）
# trends / scoring は FAST、記事本体は ARTICLE、それ以外は FAST でまず回す
rs = rs.replace("collect_trends(client,", "collect_trends(fast_client,")
rs = rs.replace("generate_articles(client,", "generate_articles(article_client,")
rs = rs.replace("generate_article(client,", "generate_article(article_client,")
rs = rs.replace("generate_affiliate", "generate_affiliate")  # no-op
rs = rs.replace("generate_premium", "generate_premium")      # no-op
rs = rs.replace("generate_threads(client,", "generate_threads(fast_client,")
rs = rs.replace("generate_thread", "generate_thread")        # no-op

# もしまだ "client," が残ってたら、とりあえず fast_client に寄せる（安全側）
rs = rs.replace("(client,", "(fast_client,")

rp.write_text(rs, encoding="utf-8")
print("patched:", rp)
