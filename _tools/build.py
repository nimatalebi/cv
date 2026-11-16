"""
Static blog builder for nimatalebi.ir (GitHub Pages, no server-side build).

Write a post as  _posts/<slug>.html :

    <!--meta
    {
      "title": "...",
      "description": "...",
      "date": "2026-11-15",
      "tags": ["ai", "automation"],
      "keyword": "..."
    }
    -->
    <h2 id="intro">...</h2>
    <p>...</p>

Then run:   python _tools/build.py

It writes  blog/<slug>/index.html  (clean URL /blog/<slug>/),
blog/index.html, sitemap.xml and the latest-posts list on the homepage.
Folders starting with "_" are not published by GitHub Pages.
"""
import html, json, math, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"
SITE = "https://nimatalebi.ir"

TAGS = {
    "ai": "هوش مصنوعی",
    "automation": "اتوماسیون",
    "software": "نرم‌افزار سازمانی",
    "web": "طراحی سایت",
    "seo": "سئو",
    "network": "شبکه و زیرساخت",
}

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
FA_MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
             "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]


def g2j(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm, jd = 1 + days // 31, 1 + days % 31
    else:
        jm, jd = 7 + (days - 186) // 30, 1 + (days - 186) % 30
    return jy, jm, jd


def fa_date(iso):
    y, m, d = map(int, iso.split("-"))
    jy, jm, jd = g2j(y, m, d)
    return f"{jd} {FA_MONTHS[jm - 1]} {jy}".translate(FA_DIGITS)


def esc(s):
    return html.escape(s, quote=True)


def load():
    posts = []
    for f in sorted(POSTS.glob("*.html")):
        raw = f.read_text(encoding="utf-8")
        m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->\s*(.*)", raw, re.S)
        if not m:
            raise SystemExit(f"missing meta block: {f.name}")
        meta = json.loads(m.group(1))
        meta["slug"] = f.stem
        meta["body"] = m.group(2).strip()
        words = len(re.sub(r"<[^>]+>", " ", meta["body"]).split())
        meta["read"] = max(2, math.ceil(words / 200))
        meta.setdefault("order", 0)
        posts.append(meta)
    posts.sort(key=lambda p: (p["date"], p["order"]), reverse=True)
    return posts


HEAD = """<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#0c0c0b">
<meta property="og:type" content="{ogtype}">
<meta property="og:locale" content="fa_IR">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{ogtitle}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{image}">
<meta name="twitter:card" content="summary_large_image">
{extra}<link rel="icon" href="/assets/img/favicon.ico">
<link rel="preload" href="/assets/fonts/vazirmatn-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css">
{jsonld}</head>
<body>
"""

BAR = """<header class="bar">
  <div class="wrap">
    <a class="brand" href="/"><i aria-hidden="true"></i>نیما طالبی</a>
    <nav class="nav" aria-label="ناوبری اصلی">
      <a href="/#about">درباره من</a>
      <a href="/#work">تخصص‌ها</a>
      <a href="/#experience">تجربه</a>
      <a href="/blog/" class="cur"{cur}>نوشته‌ها</a>
      <a href="/#contact">تماس</a>
    </nav>
    <div class="clock mono ltr"><span class="dot" aria-hidden="true"></span><span>TEHRAN</span><b id="clock">--:--</b></div>
  </div>
</header>
"""

FOOT = """<footer>
  <div class="wrap mono ltr"><span>© <span id="yr">2026</span> NIMA TALEBI</span><a href="{href}">{label}</a></div>
</footer>

<script src="/assets/js/site.js" defer></script>
</body>
</html>
"""


def tag_line(p):
    return " · ".join(TAGS[t] for t in p["tags"])


def render_post(p, prev, nxt, related):
    url = f"{SITE}/blog/{p['slug']}/"
    image = SITE + p.get("image", "/assets/img/avatar.png")
    ld = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": p["title"], "description": p["description"],
        "datePublished": p["date"], "dateModified": p.get("updated", p["date"]),
        "inLanguage": "fa", "mainEntityOfPage": url, "image": image,
        "keywords": p.get("keyword", ""),
        "author": {"@type": "Person", "name": "نیما طالبی", "url": SITE + "/"},
    }
    out = HEAD.format(
        title=esc(p["title"] + " — نیما طالبی"), desc=esc(p["description"]), url=url,
        ogtype="article", ogtitle=esc(p["title"]), image=image,
        extra=f'<meta property="article:published_time" content="{p["date"]}">\n',
        jsonld='<script type="application/ld+json">\n' + json.dumps(ld, ensure_ascii=False, indent=1) + "\n</script>\n",
    )
    out += '<div class="progress" aria-hidden="true"><i></i></div>\n\n' + BAR.format(cur="")
    rel = "".join(
        f'\n      <a class="post" href="/blog/{r["slug"]}/"><span class="d">{TAGS[r["tags"][0]]}</span><h3>{esc(r["title"])}</h3><span class="go">←</span></a>'
        for r in related)
    out += f"""
<main>
<article>
  <header class="art-head">
    <div class="wrap">
      <nav class="crumbs mono" aria-label="مسیر"><a href="/">خانه</a><span aria-hidden="true">/</span><a href="/blog/">نوشته‌ها</a><span aria-hidden="true">/</span><span>{p['slug']}</span></nav>
      <h1>{esc(p['title'])}</h1>
      <p class="lede">{p.get('lede', esc(p['description']))}</p>
      <div class="art-meta mono">
        <span>تاریخ <b>{fa_date(p['date'])}</b></span>
        <span>زمان مطالعه <b>{str(p['read']).translate(FA_DIGITS)} دقیقه</b></span>
        <span>موضوع <b>{tag_line(p)}</b></span>
      </div>
    </div>
  </header>

  <div class="art-body">
    <div class="wrap">
      <aside class="toc" aria-label="فهرست مطالب">
        <h2>CONTENTS</h2>
        <ol id="toc"></ol>
      </aside>

      <div class="prose">
{p['body']}
      </div>
    </div>
  </div>
</article>

<section class="sec related">
  <div class="wrap">
    <div class="sec-head"><span class="idx mono">→</span><h2>نوشته‌های مرتبط</h2></div>{rel}
  </div>
</section>

<nav class="art-foot" aria-label="ناوبری مقاله">
  <div class="wrap">
    {f'<a href="/blog/{nxt["slug"]}/"><small>NEXT</small><b>{esc(nxt["title"])}</b></a>' if nxt else '<a href="/blog/"><small>BACK</small><b>همه‌ی نوشته‌ها</b></a>'}
    {f'<a href="/blog/{prev["slug"]}/"><small>PREVIOUS</small><b>{esc(prev["title"])}</b></a>' if prev else '<a href="/#contact"><small>CONTACT</small><b>پروژه‌ای در ذهن دارید؟</b></a>'}
  </div>
</nav>
</main>

"""
    out += FOOT.format(href="/blog/", label="← BLOG")
    return out


def post_row(p, cls="post"):
    return (f'      <a class="{cls}" href="/blog/{p["slug"]}/" data-tags="{" ".join(p["tags"])}">\n'
            f'        <span class="d">{fa_date(p["date"])}</span>\n'
            f'        <div>\n'
            f'          <h3>{esc(p["title"])}</h3>\n'
            f'          <p>{esc(p["description"])}</p>\n'
            f'          <div class="tg">{tag_line(p)}</div>\n'
            f'        </div>\n'
            f'        <span class="go">←</span>\n'
            f'      </a>\n')


def render_index(posts):
    used = [t for t in TAGS if any(t in p["tags"] for p in posts)]
    buttons = '        <button type="button" data-tag="*" aria-pressed="true">همه</button>\n' + "".join(
        f'        <button type="button" data-tag="{t}" aria-pressed="false">{TAGS[t]}</button>\n' for t in used)
    out = HEAD.format(
        title="نوشته‌ها — نیما طالبی",
        desc="مقاله‌های نیما طالبی درباره‌ی هوشمندسازی کسب‌وکار، راهکارهای هوش مصنوعی، اتوماسیون سازمان، طراحی سایت، سئو و شبکه.",
        url=SITE + "/blog/", ogtype="website", ogtitle="نوشته‌ها — نیما طالبی",
        image=SITE + "/assets/img/avatar.png", extra="", jsonld="")
    out += BAR.format(cur=' aria-current="page"')
    out += f"""
<main>
  <section class="page-head">
    <div class="wrap">
      <nav class="crumbs mono" aria-label="مسیر"><a href="/">خانه</a><span aria-hidden="true">/</span><span>نوشته‌ها</span></nav>
      <h1>نوشته‌ها</h1>
      <p class="intro">یادداشت‌هایی از کار واقعی: هوشمندسازی کسب‌وکار، راهکارهای هوش مصنوعی، خودکارسازی عملیات سازمان، طراحی سایت، سئو و زیرساخت شبکه.</p>
      <div class="filters" role="group" aria-label="فیلتر موضوع">
{buttons}      </div>
    </div>
  </section>

  <section class="sec">
    <div class="wrap posts">
{''.join(post_row(p) for p in posts)}      <p class="empty" hidden>فعلاً نوشته‌ای با این موضوع منتشر نشده.</p>
    </div>
  </section>
</main>

"""
    out += FOOT.format(href="/", label="← HOME")
    return out


def render_sitemap(posts):
    newest = posts[0]["date"] if posts else ""
    urls = [(SITE + "/", newest), (SITE + "/blog/", newest)] + [
        (f"{SITE}/blog/{p['slug']}/", p.get("updated", p["date"])) for p in posts]
    body = "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "</urlset>\n")


def update_home(posts):
    f = ROOT / "index.html"
    s = f.read_text(encoding="utf-8")
    rows = "".join(
        f'    <a class="post rv" href="/blog/{p["slug"]}/"><span class="d">{TAGS[p["tags"][0]]}</span><h3>{esc(p["title"])}</h3><span class="go">←</span></a>\n'
        for p in posts[:5])
    s2 = re.sub(r"(<!-- posts:start -->\n).*?(\s*<!-- posts:end -->)", lambda m: m.group(1) + rows + m.group(2).lstrip("\n"), s, flags=re.S)
    if s2 == s and "<!-- posts:start -->" not in s:
        raise SystemExit("index.html is missing <!-- posts:start --> / <!-- posts:end --> markers")
    f.write_text(s2, encoding="utf-8")


def related_for(p, posts, n=3):
    scored = sorted((r for r in posts if r is not p),
                    key=lambda r: (-len(set(r["tags"]) & set(p["tags"])), r["date"]), reverse=False)
    return scored[:n]


def main():
    posts = load()
    for i, p in enumerate(posts):
        prev = posts[i + 1] if i + 1 < len(posts) else None
        nxt = posts[i - 1] if i > 0 else None
        d = ROOT / "blog" / p["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render_post(p, prev, nxt, related_for(p, posts)), encoding="utf-8")
    (ROOT / "blog" / "index.html").write_text(render_index(posts), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(render_sitemap(posts), encoding="utf-8")
    update_home(posts)
    print(f"built {len(posts)} posts")


if __name__ == "__main__":
    main()
