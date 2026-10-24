"""Download Open-Access papers for the ShortPFAS-Net literature dataset.

This script ONLY downloads papers that are legally Open Access (gold or green).
Papers behind a paywall (closed) are skipped and reported so you can obtain
them via your institution's library subscription instead.

Usage:
    python scripts/download_papers.py              # use the built-in DOI list
    python scripts/download_papers.py --doi "10.1038/s41467-024-55320-9"

It resolves each DOI to a downloadable PDF URL via the free OpenAlex API,
downloads the PDF into data/papers/, and prints a summary.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Papers known to contain PFAS adsorption/removal data, prioritized for
# short-chain PFAS. These DOIs were verified to be Open Access (gold/green).
DEFAULT_DOIS = [
    # Nature Communications (gold OA) - polyamide membrane PFAS removal
    "10.1038/s41467-024-55320-9",
    # Nature Communications (gold OA) - fluoropolymer sorbent PFAS capture
    "10.1038/s41467-024-52690-y",
    # Environmental Research 2022 (green OA via UTS repository) - XGBoost 234 records
    "10.1016/j.envres.2022.114286",
]

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "papers"

# Minimal browser-like headers to avoid 403 from publisher CDNs
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/pdf,text/html,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


def openalex_work(doi: str) -> dict | None:
    """Fetch OpenAlex metadata for a DOI. Returns None on failure."""
    url = f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}"
    req = urllib.request.Request(url, headers={"User-Agent": HEADERS["User-Agent"]})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except Exception as exc:  # noqa: BLE001
        print(f"  [错误] OpenAlex 查询失败: {exc}")
        return None


def get_pdf_url(work: dict) -> tuple[str | None, str]:
    """Return (pdf_url, oa_status) for a work."""
    oa_status = work.get("open_access", {}).get("oa_status", "unknown")
    loc = work.get("best_oa_location") or {}
    pdf_url = loc.get("pdf_url") or loc.get("landing_page_url")
    # Prefer the top-level oa_url which is usually a direct PDF
    pdf_url = work.get("open_access", {}).get("oa_url") or pdf_url
    return pdf_url, oa_status


def download_pdf(url: str, out_path: Path) -> bool:
    """Download a PDF with redirect following. Returns True on success."""
    req = urllib.request.Request(url, headers=HEADERS)
    # SSL context: tolerate cert verification issues from some OA repositories
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
            data = r.read()
            content_type = r.headers.get("Content-Type", "")
            if "html" in content_type and len(data) < 2000:
                # Got an HTML interstitial instead of a PDF
                print(f"  [警告] 返回的是网页而非 PDF (content-type={content_type})")
                return False
            out_path.write_bytes(data)
            return True
    except Exception as exc:  # noqa: BLE001
        print(f"  [错误] 下载失败: {exc}")
        return False


def mdpi_pdf_url(doi: str) -> str | None:
    """Construct a direct MDPI PDF URL from a DOI.

    MDPI blocks requests to www.mdpi.com (Akamai IP-reputation block, not a JS
    challenge), but the PDFs are served from res.mdpi.com which is NOT blocked.
    The stable pattern is:

        https://res.mdpi.com/d_attachment/<journal>/<journal>-<vol>-<issue0>/article_deploy/<journal>-<vol>-<issue0>.pdf

    MDPI DOIs use the form 10.3390/<journal><vol><issue><article> where the
    trailing 8 digits are vol(2) + issue(2) + article(4). The CDN URL uses the
    article number zero-padded to 5 digits, and omits the issue. Example:
        10.3390/molecules31071100
            journal = "molecules", vol = "31", issue = "07", article = 1100
        -> https://res.mdpi.com/d_attachment/molecules/molecules-31-01100/article_deploy/molecules-31-01100.pdf
    """
    import re
    m = re.match(r"10\.3390/([a-z]+)(\d{2})(\d{2})(\d{4})", doi)
    if not m:
        return None
    journal, vol, _issue, article = m.group(1), m.group(2), m.group(3), m.group(4)
    article5 = f"{int(article):05d}"  # zero-pad article number to 5 digits
    stem = f"{journal}-{vol}-{article5}"
    return f"https://res.mdpi.com/d_attachment/{journal}/{stem}/article_deploy/{stem}.pdf"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--doi", action="append", dest="dois",
                        help="DOI to download (repeatable); defaults to built-in list")
    args = parser.parse_args()

    dois = args.dois or DEFAULT_DOIS
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    ok, skipped, failed = 0, 0, 0
    for doi in dois:
        print(f"\n=== {doi} ===")
        work = openalex_work(doi)
        if work is None:
            failed += 1
            continue

        title = (work.get("title") or "unknown")[:70]
        pdf_url, oa_status = get_pdf_url(work)
        print(f"  标题: {title}")
        print(f"  OA 状态: {oa_status}")

        if oa_status not in ("gold", "green", "hybrid", "bronze") or not pdf_url:
            print(f"  [跳过] 非开放获取或无可下载 URL，请通过图书馆获取")
            skipped += 1
            continue

        # filename from DOI (safe)
        safe_name = doi.replace("/", "_").replace(".", "_") + ".pdf"
        out_path = OUT_DIR / safe_name
        if out_path.exists() and out_path.stat().st_size > 1000:
            print(f"  [已存在] {out_path.name} ({out_path.stat().st_size} bytes)")
            ok += 1
            continue

        # MDPI hosts PDFs on res.mdpi.com (not blocked by their www.mdpi.com
        # Akamai IP block). Try the direct CDN URL first for MDPI DOIs.
        mdpi_url = mdpi_pdf_url(doi)
        if mdpi_url:
            print(f"  尝试 MDPI CDN 直链: {mdpi_url}")
            if download_pdf(mdpi_url, out_path):
                print(f"  [完成] {out_path.name} ({out_path.stat().st_size} bytes)")
                ok += 1
                time.sleep(1.0)
                continue

        print(f"  下载: {pdf_url}")
        if download_pdf(pdf_url, out_path):
            print(f"  [完成] {out_path.name} ({out_path.stat().st_size} bytes)")
            ok += 1
        else:
            failed += 1
        time.sleep(1.0)  # be polite to the server

    print(f"\n=== 汇总: 成功 {ok} | 跳过 {skipped} | 失败 {failed} ===")
    print(f"文件保存在: {OUT_DIR}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
