"""
Backward-compatible wrapper — delegates to infrastructure.claude_gateway.
"""
from infrastructure.claude_gateway import generate_report, format_bazi_for_prompt, _sample_report  # noqa: F401
