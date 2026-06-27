#!/usr/bin/env python3
"""
SecuLog 보안 브리핑 생성기
-----------------------------------------
헤르메스 에이전트가 만든 briefing.json 을 받아
고정 디자인 템플릿에 끼워 넣어 완성된 HTML 페이지를 만든다.

사용법:
    python3 render_briefing.py briefing.json
    python3 render_briefing.py briefing.json -o 출력파일.html

핵심 원칙: LLM 은 'JSON(데이터)' 만 생성한다. 디자인(HTML/CSS)은 절대 생성하지 않는다.
그래야 매번 디자인이 동일하고 자동화가 안 깨진다.
"""
import json
import sys
import html
import argparse
from pathlib import Path

# ── 브랜드 설정 (여기만 바꾸면 전체에 반영) ──────────────────
BRAND_MAIN = "Secu"        # 워드마크 앞부분 (진한 남색)
BRAND_ACCENT = "Log"       # 워드마크 뒷부분 (파란색 강조)
AUTHOR = "Felix"           # 푸터 저작권 표기
LINKEDIN_URL = "https://www.linkedin.com/in/insun-lee-b1201a10b/"
# ───────────────────────────────────────────────────────────

# 심각도 -> (badge 클래스, 좌측 바 클래스, 기본 라벨)
SEV = {
    "critical": ("badge-critical", "sev-critical", "긴급"),
    "high":     ("badge-high",     "sev-high",     "높음"),
    "medium":   ("badge-medium",   "sev-medium",   "중간"),
    "incident": ("badge-incident", "sev-incident", "사고"),
}

# 올려주신 원본의 CSS 를 그대로 보존 + 워드마크 규칙만 추가
CSS = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, 'Malgun Gothic', 'Apple SD Gothic Neo', Arial, sans-serif; background: #f4f5f7; color: #1a1a2e; line-height: 1.6; }
  a { text-decoration: none; color: inherit; }
  .wrapper { max-width: 700px; margin: 32px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 20px rgba(0,0,0,0.08); }
  .header { background: #eef0f4; padding: 28px 36px 24px; display: flex; align-items: center; justify-content: space-between; gap: 16px; border-bottom: 3px solid #0d1b3e; }
  .wordmark { font-size: 26px; font-weight: 800; letter-spacing: -0.02em; color: #0d1b3e; }
  .wordmark .accent { color: #2563eb; }
  .header-meta { text-align: right; }
  .header-meta .nl-label { font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: #6b7488; margin-bottom: 4px; }
  .header-meta .nl-title { font-size: 17px; font-weight: 700; color: #0d1b3e; }
  .header-meta .nl-date { font-size: 12px; color: #8a93a8; margin-top: 3px; }
  .body { padding: 28px 36px 32px; }
  .section-label { font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: #8a93a8; font-weight: 600; padding-bottom: 8px; border-bottom: 1px solid #e8eaed; margin-bottom: 4px; margin-top: 28px; }
  .section-label:first-child { margin-top: 0; }
  .card { display: block; padding: 16px 0; border-bottom: 1px solid #f0f1f3; transition: background 0.15s; }
  .card:last-child { border-bottom: none; }
  .card:hover { background: #f8f9fc; margin: 0 -36px; padding: 16px 36px; }
  .card-top { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }
  .badge { font-size: 10px; font-weight: 700; padding: 3px 9px; border-radius: 4px; letter-spacing: 0.04em; }
  .badge-critical { background: #fff0f0; color: #c0392b; border: 1px solid #f5c6c6; }
  .badge-high { background: #fff7ee; color: #b94d00; border: 1px solid #fdd5a8; }
  .badge-medium { background: #fff9e6; color: #856900; border: 1px solid #f9e0a0; }
  .badge-incident { background: #f3f0ff; color: #6133c0; border: 1px solid #cfc0f5; }
  .source { font-size: 11px; color: #a0a8b8; }
  .card-headline { font-size: 14px; font-weight: 600; color: #0d1b3e; margin-bottom: 5px; line-height: 1.45; }
  .card-headline .arrow { font-size: 12px; color: #2563eb; margin-left: 4px; opacity: 0; transition: opacity 0.15s; }
  .card:hover .card-headline .arrow { opacity: 1; }
  .card-summary { font-size: 13px; color: #4a5568; line-height: 1.65; }
  .trend-box { background: #f8f9fc; border-radius: 10px; padding: 18px 20px; margin-top: 6px; }
  .trend-row { display: flex; gap: 12px; padding: 10px 0; border-bottom: 1px solid #e8eaed; align-items: flex-start; }
  .trend-row:last-child { border-bottom: none; padding-bottom: 0; }
  .trend-num { font-size: 11px; font-weight: 700; color: #2563eb; min-width: 22px; padding-top: 2px; }
  .trend-text { font-size: 13px; color: #4a5568; line-height: 1.6; }
  .trend-text strong { color: #0d1b3e; font-weight: 600; }
  .footer { background: #f4f5f7; border-top: 1px solid #e8eaed; padding: 16px 36px; font-size: 11px; color: #9aa0b0; line-height: 1.6; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
  .footer-meta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
  .linkedin-link { display: inline-flex; align-items: center; justify-content: center; min-height: 28px; padding: 6px 12px; border-radius: 6px; background: #0a66c2; color: #fff; font-size: 12px; font-weight: 800; letter-spacing: 0.01em; box-shadow: 0 6px 14px rgba(10,102,194,0.16); }
  .linkedin-link:hover { background: #004182; color: #fff; }
  .card-inner { display: flex; gap: 14px; }
  .sev-bar { width: 3px; border-radius: 2px; flex-shrink: 0; margin: 3px 0; }
  .sev-critical { background: #e74c3c; }
  .sev-high { background: #e67e22; }
  .sev-medium { background: #f0b429; }
  .sev-incident { background: #7c3aed; }
  .card-content { flex: 1; }
"""


def esc(value: str) -> str:
    return html.escape(str(value), quote=True)


def render_card(item: dict) -> str:
    badge_cls, bar_cls, default_label = SEV.get(item.get("severity", "medium"), SEV["medium"])
    label = item.get("severity_label") or default_label
    return (
        f'    <a class="card" href="{esc(item["url"])}" target="_blank">\n'
        f'      <div class="card-inner"><div class="sev-bar {bar_cls}"></div><div class="card-content">\n'
        f'        <div class="card-top"><span class="badge {badge_cls}">{esc(label)}</span>'
        f'<span class="source">{esc(item["source"])}</span></div>\n'
        f'        <div class="card-headline">{esc(item["headline"])}<span class="arrow">↗</span></div>\n'
        f'        <div class="card-summary">{esc(item["summary"])}</div>\n'
        f'      </div></div>\n'
        f'    </a>'
    )


def render_trends(items: list) -> str:
    rows = []
    for i, t in enumerate(items, 1):
        if isinstance(t, dict):
            lead, body = t.get("lead", ""), t.get("body", "")
        else:
            lead, body = "", t
        strong = f"<strong>{esc(lead)}</strong> — " if lead else ""
        rows.append(
            f'      <div class="trend-row">\n'
            f'        <div class="trend-num">{i:02d}</div>\n'
            f'        <div class="trend-text">{strong}{esc(body)}</div>\n'
            f'      </div>'
        )
    return '    <div class="trend-box">\n' + "\n".join(rows) + "\n    </div>"


def render_section(sec: dict) -> str:
    head = f'    <div class="section-label">{esc(sec["label"])}</div>'
    if sec.get("type") == "trends":
        return head + "\n" + render_trends(sec["items"])
    cards = "\n\n".join(render_card(it) for it in sec["items"])
    return head + "\n\n" + cards


def render(data: dict) -> str:
    body = "\n\n".join(render_section(s) for s in data["sections"])
    page_title = f'{BRAND_MAIN}{BRAND_ACCENT} {data.get("title", "보안 브리핑")} — {data.get("date_short", "")}'.strip(" —")

    seo = data.get("seo", {})
    seo_title = seo.get("title") or page_title
    seo_desc  = seo.get("description", "")
    seo_kw    = seo.get("keywords", "")
    site_url  = "https://macbong83.github.io"
    date_short = data.get("date_short", "").replace(".", "-")
    og_url    = f"{site_url}/posts/{date_short}.html" if date_short else site_url
    full_title = f"{esc(seo_title)} | {BRAND_MAIN}{BRAND_ACCENT}"

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{full_title}</title>
<meta name="description" content="{esc(seo_desc)}">
<meta name="keywords" content="{esc(seo_kw)}">
<meta name="author" content="{esc(AUTHOR)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(seo_title)}">
<meta property="og:description" content="{esc(seo_desc)}">
<meta property="og:url" content="{esc(og_url)}">
<meta property="og:site_name" content="{BRAND_MAIN}{BRAND_ACCENT}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(seo_title)}">
<meta name="twitter:description" content="{esc(seo_desc)}">
<link rel="canonical" href="{esc(og_url)}">
<style>{CSS}</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <div class="header-logo">
      <span class="wordmark">{esc(BRAND_MAIN)}<span class="accent">{esc(BRAND_ACCENT)}</span></span>
    </div>
    <div class="header-meta">
      <div class="nl-label">{esc(data.get("tagline", "글로벌 정보보안 뉴스레터"))}</div>
      <div class="nl-title">{esc(data.get("title", "보안 브리핑"))}</div>
      <div class="nl-date">{esc(data.get("date_display", ""))}</div>
    </div>
  </div>
  <div class="body">
{body}
  </div>
  <div class="footer">
    <div>출처: {esc(data.get("sources_line", ""))}</div>
    <div class="footer-meta">
      <a class="linkedin-link" href="{esc(LINKEDIN_URL)}" target="_blank" rel="noopener noreferrer">LinkedIn</a>
      <span>© 2026 {esc(AUTHOR)} · {esc(BRAND_MAIN + BRAND_ACCENT)}. 본 브리핑은 공개된 보안 뉴스를 기반으로 작성되었습니다.</span>
    </div>
  </div>
</div>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="briefing.json -> 보안 브리핑 HTML")
    ap.add_argument("input", help="입력 JSON 파일 경로")
    ap.add_argument("-o", "--output", help="출력 HTML 경로 (기본: briefing-<date_short>.html)")
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    out_path = args.output or f"briefing-{data.get('date_short', 'output').replace('.', '-')}.html"
    Path(out_path).write_text(render(data), encoding="utf-8")
    print(f"생성 완료: {out_path}")


if __name__ == "__main__":
    main()
