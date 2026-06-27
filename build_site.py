#!/usr/bin/env python3
"""
SecuLog 정적 사이트 빌더
-----------------------------------------
data/*.json (헤르메스가 매일 하나씩 추가) 을 읽어서
  posts/<날짜>.html   각 브리핑 페이지
  index.html          전체 아카이브(목록)
  feed.xml            RSS 구독 피드
를 생성한다.

사용법:  python3 build_site.py
"""
import json
import datetime
from email.utils import format_datetime
from pathlib import Path

from render_briefing import render, esc, CSS, BRAND_MAIN, BRAND_ACCENT, AUTHOR, LINKEDIN_URL

# ── 사이트 설정 (배포 후 본인 주소로 변경) ──────────────────
SITE_URL = "https://macbong83.github.io"          # ← GitHub Pages / 커스텀 도메인 주소
SITE_TITLE = f"{BRAND_MAIN}{BRAND_ACCENT}"
SITE_DESC = "EDR · SASE · CTEM · 취약점 관리 중심의 매일 보안 브리핑"
KST = datetime.timezone(datetime.timedelta(hours=9))
PUBLISH_HOUR = 8                                       # 발행 시각(RSS pubDate용)
# ───────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
POSTS_DIR = ROOT / "posts"


def slug_for(data, fallback):
    return data.get("date_short", fallback).replace(".", "-")


def post_datetime(slug):
    try:
        d = datetime.date.fromisoformat(slug)
        return datetime.datetime(d.year, d.month, d.day, PUBLISH_HOUR, tzinfo=KST)
    except ValueError:
        return datetime.datetime.now(KST)


def load_all():
    items = []
    for f in sorted(DATA_DIR.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        items.append((slug_for(d, f.stem), d))
    items.sort(key=lambda x: x[0], reverse=True)   # 최신순
    return items


def preview_headlines(d, n=3):
    out = []
    for sec in d.get("sections", []):
        if sec.get("type") == "trends":
            continue
        for it in sec.get("items", []):
            out.append(it.get("headline", ""))
    return out[:n]


def build_posts(items):
    POSTS_DIR.mkdir(exist_ok=True)
    for slug, d in items:
        (POSTS_DIR / f"{slug}.html").write_text(render(d), encoding="utf-8")


INDEX_EXTRA_CSS = """
  .site-head { max-width: 700px; margin: 32px auto 0; padding: 0 8px; display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
  .site-head .wordmark { font-size: 30px; }
  .site-desc { font-size: 13px; color: #6b7488; margin-top: 6px; }
  .site-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .rss-link { font-size: 12px; font-weight: 700; color: #b94d00; border: 1px solid #fdd5a8; background: #fff7ee; padding: 6px 12px; border-radius: 6px; }
  .site-linkedin { font-size: 12px; font-weight: 800; color: #fff; background: #0a66c2; padding: 7px 12px; border-radius: 6px; box-shadow: 0 6px 14px rgba(10,102,194,0.16); }
  .site-linkedin:hover { background: #004182; color: #fff; }
  .archive { max-width: 700px; margin: 20px auto 48px; background: #fff; border-radius: 12px; box-shadow: 0 2px 20px rgba(0,0,0,0.08); overflow: hidden; }
  .post-item { display: block; padding: 22px 32px; border-bottom: 1px solid #f0f1f3; transition: background 0.15s; }
  .post-item:last-child { border-bottom: none; }
  .post-item:hover { background: #f8f9fc; }
  .post-date { font-size: 11px; letter-spacing: 0.08em; color: #2563eb; font-weight: 700; text-transform: uppercase; }
  .post-title { font-size: 18px; font-weight: 700; color: #0d1b3e; margin: 4px 0 10px; }
  .post-preview { list-style: none; }
  .post-preview li { font-size: 13px; color: #4a5568; padding: 3px 0 3px 14px; position: relative; }
  .post-preview li:before { content: '·'; position: absolute; left: 2px; color: #a0a8b8; }
  .site-foot { max-width: 700px; margin: 0 auto 48px; padding: 0 8px; font-size: 11px; color: #9aa0b0; text-align: center; }
"""


def build_index(items):
    cards = []
    for slug, d in items:
        previews = "".join(f"<li>{esc(h)}</li>" for h in preview_headlines(d))
        cards.append(
            f'    <a class="post-item" href="posts/{slug}.html">\n'
            f'      <div class="post-date">{esc(d.get("date_display", slug))}</div>\n'
            f'      <div class="post-title">{esc(d.get("title", "보안 브리핑"))}</div>\n'
            f'      <ul class="post-preview">{previews}</ul>\n'
            f'    </a>'
        )
    html_doc = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(SITE_TITLE)} — 정보보안 브리핑</title>
<meta name="description" content="{esc(SITE_DESC)}">
<link rel="alternate" type="application/rss+xml" title="{esc(SITE_TITLE)}" href="{SITE_URL}/feed.xml">
<style>{CSS}{INDEX_EXTRA_CSS}</style>
</head>
<body>
  <div class="site-head">
    <div>
      <span class="wordmark">{esc(BRAND_MAIN)}<span class="accent">{esc(BRAND_ACCENT)}</span></span>
      <div class="site-desc">{esc(SITE_DESC)}</div>
    </div>
    <div class="site-actions">
      <a class="rss-link" href="{SITE_URL}/feed.xml">RSS 구독</a>
      <a class="site-linkedin" href="{esc(LINKEDIN_URL)}" target="_blank" rel="noopener noreferrer">LinkedIn</a>
    </div>
  </div>
  <div class="archive">
{chr(10).join(cards)}
  </div>
  <div class="site-foot">© 2026 {esc(AUTHOR)} · {esc(SITE_TITLE)}. 공개된 보안 뉴스를 기반으로 작성합니다.</div>
</body>
</html>
"""
    (ROOT / "index.html").write_text(html_doc, encoding="utf-8")


def build_feed(items):
    now = format_datetime(datetime.datetime.now(KST))
    entries = []
    for slug, d in items:
        link = f"{SITE_URL}/posts/{slug}.html"
        desc = " / ".join(preview_headlines(d, 4))
        entries.append(
            "    <item>\n"
            f"      <title>{esc(SITE_TITLE)} 보안 브리핑 — {esc(d.get('date_short', slug))}</title>\n"
            f"      <link>{link}</link>\n"
            f"      <guid isPermaLink=\"true\">{link}</guid>\n"
            f"      <pubDate>{format_datetime(post_datetime(slug))}</pubDate>\n"
            f"      <description>{esc(desc)}</description>\n"
            "    </item>"
        )
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{esc(SITE_TITLE)}</title>
    <link>{SITE_URL}/</link>
    <description>{esc(SITE_DESC)}</description>
    <language>ko</language>
    <lastBuildDate>{now}</lastBuildDate>
{chr(10).join(entries)}
  </channel>
</rss>
"""
    (ROOT / "feed.xml").write_text(feed, encoding="utf-8")


def main():
    items = load_all()
    if not items:
        print("data/ 에 JSON이 없습니다.")
        return
    build_posts(items)
    build_index(items)
    build_feed(items)
    print(f"빌드 완료: posts {len(items)}개 + index.html + feed.xml")


if __name__ == "__main__":
    main()
