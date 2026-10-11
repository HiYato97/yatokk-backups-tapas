#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tapas_backup.py - one-shot archival backup for a Tapas.io series or full author catalog.

Archives, for every episode of a series:
  * episode info JSON,
  * the full server-rendered <article> HTML,
  * creator / author note for each episode,
  * cover image (cover.jpg/png),
  * every reader comment and reply,
  * author / creator profile information saved to author.json.

Stdlib only (urllib.request + regex/html parsing). Python 3.8+.
"""

import argparse
import html as html_mod
import json
import os
import random
import re
import socket
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = "https://tapas.io"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
JSON_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}

MAX_LIST_PAGES = 300
MAX_COMMENT_PAGES = 500
MAX_REPLY_PAGES = 100


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg):
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"), flush=True)


def sanitize_filename(name):
    if not name:
        return "series"
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', name)
    return cleaned.strip().rstrip('.')


# --------------------------------------------------------------------------
# HTTP layer
# --------------------------------------------------------------------------

class FetchError(Exception):
    pass


class Fetcher:
    def __init__(self, rate=2.0, max_tries=4, timeout=30, cookie=None, jitter=0.25):
        self.min_interval = 1.0 / rate if rate and rate > 0 else 0.0
        self.max_tries = max(1, max_tries)
        self.timeout = timeout
        self.cookie = cookie
        self.jitter = jitter
        self.last_ts = 0.0
        self.requests = 0
        self.retries = 0

    def _throttle(self):
        if self.min_interval <= 0:
            return
        wait = self.min_interval - (time.monotonic() - self.last_ts)
        if wait > 0:
            time.sleep(wait * (1.0 + random.uniform(0.0, self.jitter)))
        self.last_ts = time.monotonic()

    def _backoff(self, attempt):
        time.sleep((2 ** (attempt - 1)) * (1.0 + random.uniform(0.0, 0.5)))
        self.retries += 1

    def get(self, url, as_json=False, referer=None):
        headers = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
        if referer:
            headers["Referer"] = referer
        if as_json:
            headers.update(JSON_HEADERS)
        else:
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        if self.cookie:
            headers["Cookie"] = self.cookie

        last_err = None
        for attempt in range(1, self.max_tries + 1):
            self._throttle()
            self.requests += 1
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                text = raw.decode("utf-8", "replace")
                if as_json:
                    text = text.strip()
                    obj = json.loads(text)
                    if obj.get("code") is not None and obj.get("code") != 200:
                        raise FetchError("endpoint code=%s msg=%r for %s"
                                         % (obj.get("code"), obj.get("msg"), url))
                    return obj
                return text
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code >= 500:
                    last_err = FetchError("HTTP %d for %s" % (e.code, url))
                    if attempt == self.max_tries:
                        raise last_err
                    self._backoff(attempt)
                    continue
                raise FetchError("HTTP %d (non-retryable) for %s" % (e.code, url))
            except (urllib.error.URLError, socket.timeout, TimeoutError,
                    ConnectionError, json.JSONDecodeError, ValueError, OSError) as e:
                last_err = FetchError("%s: %s for %s" % (type(e).__name__, e, url))
                if attempt == self.max_tries:
                    raise last_err
                self._backoff(attempt)
        raise last_err

    def get_bytes(self, url, referer=None):
        headers = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9",
                   "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"}
        if referer:
            headers["Referer"] = referer
        if self.cookie:
            headers["Cookie"] = self.cookie
        last_err = None
        for attempt in range(1, self.max_tries + 1):
            self._throttle()
            self.requests += 1
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return resp.read()
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code >= 500:
                    last_err = FetchError("HTTP %d for %s" % (e.code, url))
                    if attempt == self.max_tries:
                        raise last_err
                    self._backoff(attempt)
                    continue
                raise FetchError("HTTP %d (non-retryable) for %s" % (e.code, url))
            except (urllib.error.URLError, socket.timeout, TimeoutError,
                    ConnectionError, OSError) as e:
                last_err = FetchError("%s: %s for %s" % (type(e).__name__, e, url))
                if attempt == self.max_tries:
                    raise last_err
                self._backoff(attempt)
        raise last_err


# --------------------------------------------------------------------------
# Atomic file writes
# --------------------------------------------------------------------------

def atomic_write_text(path, text):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=".part")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_json(path, obj):
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=1))


def atomic_write_bytes(path, data):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=".part")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# --------------------------------------------------------------------------
# HTML parsing helpers
# --------------------------------------------------------------------------

def maybe_unescape(h):
    if h and "&lt;" in h and "<" not in h:
        return html_mod.unescape(h)
    return h


def element_inner(text, start, tag):
    pat = re.compile(r"<(/?)" + re.escape(tag) + r"\b[^>]*?(/?)>", re.IGNORECASE | re.DOTALL)
    depth = 1
    for m in pat.finditer(text, start):
        if m.group(1):
            depth -= 1
        elif not m.group(2):
            depth += 1
        if depth == 0:
            return text[start:m.start()]
    return None


def tag_attr(tag_text, name):
    m = re.search(name + r'\s*=\s*"([^"]*)"', tag_text)
    return m.group(1) if m else None


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


ARTICLE_RE = re.compile(r"<article\b[^>]*>", re.IGNORECASE | re.DOTALL)


def extract_article(page_html):
    matches = list(ARTICLE_RE.finditer(page_html))
    chosen = None
    for m in matches:
        if "js-episode-article" in m.group(0):
            chosen = m
            break
    if chosen is None and matches:
        chosen = matches[0]
    if chosen is None:
        return None, None
    inner = element_inner(page_html, chosen.end(), "article")
    if inner is None:
        return None, None
    full = page_html[chosen.start():chosen.end() + len(inner) + len("</article>")]
    return full, inner


PARENT_ROW_RE = re.compile(r"<div\b[^>]*js-comment-parent-row[^>]*>", re.IGNORECASE)
REPLY_ROW_RE = re.compile(r"<div\b[^>]*js-comment-reply[^>]*>", re.IGNORECASE)
ROW_ID_RE = re.compile(r'id="comment-row-(\d+)"')
NAME_RE = re.compile(r'<a\b(?P<attrs>[^>]*\bwriter__name[^>]*)>(?P<inner>.*?)</a>',
                     re.IGNORECASE | re.DOTALL)
DATE_RE = re.compile(r'<p\b[^>]*class="[^"]*writer__date[^"]*"[^>]*>([^<]*)</p>')
BODY_OPEN_RE = re.compile(r"<div\b[^>]*js-comment-body[^>]*>", re.IGNORECASE)
CREATOR_RE = re.compile(r'class="[^"]*writer__label')
TOGGLE_BTN_RE = re.compile(r"<a\b[^>]*js-toggle-reply-btn[^>]*>", re.IGNORECASE)


def _parse_common(chunk, row_id):
    rec = {"id": row_id, "username": None, "display_name": "",
           "date": None, "text": None, "likes": 0, "is_creator": False}
    m = NAME_RE.search(chunk)
    if m:
        href = tag_attr(m.group("attrs"), "href") or ""
        rec["username"] = urllib.parse.unquote(href.lstrip("/")) or None
        rec["display_name"] = html_mod.unescape(strip_tags(m.group("inner"))).strip()
    m = DATE_RE.search(chunk)
    if m:
        rec["date"] = html_mod.unescape(m.group(1)).strip()
    m = BODY_OPEN_RE.search(chunk)
    if m:
        inner = element_inner(chunk, m.end(), "div")
        if inner is None:
            fm = re.compile(r"</div>").search(chunk, m.end())
            inner = chunk[m.end():fm.start()] if fm else ""
        rec["text"] = inner.strip()
    for pat in (r'id="comment-like-%s"[^>]*?data-cnt="(\d+)"' % row_id,
                r'data-cnt="(\d+)"[^>]*?id="comment-like-%s"' % row_id,
                r'<span class="js-like-cnt">\s*(\d+)\s*</span>',
                r'data-cnt="(\d+)"'):
        lm = re.search(pat, chunk)
        if lm:
            try:
                rec["likes"] = int(lm.group(1))
            except (TypeError, ValueError):
                pass
            break
    rec["is_creator"] = bool(CREATOR_RE.search(chunk))
    return rec


def parse_comment_rows(h):
    rows = []
    anchors = list(PARENT_ROW_RE.finditer(h))
    for i, m in enumerate(anchors):
        end = anchors[i + 1].start() if i + 1 < len(anchors) else len(h)
        chunk = h[m.start():end]
        idm = ROW_ID_RE.search(m.group(0)) or ROW_ID_RE.search(chunk)
        if not idm:
            continue
        rec = _parse_common(chunk, int(idm.group(1)))
        rec["replies"] = []
        reply_cnt, found_matching = 0, False
        for bm in TOGGLE_BTN_RE.finditer(chunk):
            cnt = tag_attr(bm.group(0), "data-reply-cnt")
            did = tag_attr(bm.group(0), "data-id")
            if did is not None and str(did) == str(rec["id"]):
                reply_cnt = int(cnt) if cnt and cnt.isdigit() else 0
                found_matching = True
                break
            if cnt and cnt.isdigit() and not found_matching:
                reply_cnt = int(cnt)
        rec["reply_cnt"] = reply_cnt
        rows.append(rec)
    return rows


def parse_reply_rows(h):
    rows = []
    anchors = list(REPLY_ROW_RE.finditer(h))
    for i, m in enumerate(anchors):
        end = anchors[i + 1].start() if i + 1 < len(anchors) else len(h)
        chunk = h[m.start():end]
        idm = ROW_ID_RE.search(m.group(0)) or ROW_ID_RE.search(chunk)
        if not idm:
            continue
        rows.append(_parse_common(chunk, int(idm.group(1))))
    return rows


def parse_episode_ids(body_html):
    ids, seen = [], set()
    for m in re.finditer(r'data-href="/episode/(\d+)"', body_html):
        eid = m.group(1)
        if eid not in seen:
            seen.add(eid)
            ids.append(eid)
    return ids


# --------------------------------------------------------------------------
# Author & Creator Info Fetching
# --------------------------------------------------------------------------
def parse_profile_wall_rows(h):
    rows = []
    stream_pat = re.compile(r'<div\b[^>]*class="[^"]*\bcomment-stream\b[^"]*"[^>]*>', re.IGNORECASE)
    anchors = list(stream_pat.finditer(h))
    
    for i, m in enumerate(anchors):
        end = anchors[i + 1].start() if i + 1 < len(anchors) else len(h)
        chunk = h[m.start():end]
        
        rec = {
            "id": None, "username": None, "display_name": "", 
            "date": None, "text": None, "likes": 0, "is_creator": False, "replies": []
        }
        
        idm = re.search(r'data-post-id="(\d+)"', chunk)
        if idm:
            try:
                rec["id"] = int(idm.group(1))
            except ValueError:
                pass
                
        name_m = re.search(r'<a\b[^>]*href="/([^/?#\s"]+)"[^>]*class="[^"]*\bcommenter\b[^"]*"[^>]*>(.*?)</a>', chunk, re.IGNORECASE | re.DOTALL)
        if not name_m:
            name_m = re.search(r'<a\b[^>]*class="[^"]*\bcommenter\b[^"]*"[^>]*href="/([^/?#\s"]+)"[^>]*>(.*?)</a>', chunk, re.IGNORECASE | re.DOTALL)
            
        if name_m:
            rec["username"] = name_m.group(1)
            rec["display_name"] = html_mod.unescape(strip_tags(name_m.group(2))).strip()
            
        date_m = re.search(r'<span\b[^>]*class="[^"]*\bdate\b[^"]*"[^>]*>([^<]+)</span>', chunk, re.IGNORECASE)
        if date_m:
            rec["date"] = html_mod.unescape(date_m.group(1)).strip()
            
        txt_m = re.search(r'<div\b[^>]*class="[^"]*\bcomment-txt\b[^"]*"[^>]*>(.*?)</div>', chunk, re.IGNORECASE | re.DOTALL)
        if txt_m:
            rec["text"] = txt_m.group(1).strip()

        reply_pat = re.compile(r'<div\b[^>]*class="[^"]*\breply-stream\b[^"]*"[^>]*>', re.IGNORECASE)
        reply_anchors = list(reply_pat.finditer(chunk))
        
        for r_i, r_m in enumerate(reply_anchors):
            r_end = reply_anchors[r_i + 1].start() if r_i + 1 < len(reply_anchors) else len(chunk)
            r_chunk = chunk[r_m.start():r_end]
            
            rep_rec = {
                "id": None, "username": None, "display_name": "",
                "date": None, "text": None, "likes": 0, "is_creator": False
            }
            
            r_idm = re.search(r'id="fan-comment-(\d+)"', r_chunk) or re.search(r'data-post-id="(\d+)"', r_chunk)
            if r_idm:
                try:
                    rep_rec["id"] = int(r_idm.group(1))
                except ValueError:
                    pass
                    
            r_name_m = re.search(r'<a\b[^>]*href="/([^/?#\s"]+)"[^>]*class="[^"]*\bcommenter\b[^"]*"[^>]*>(.*?)</a>', r_chunk, re.IGNORECASE | re.DOTALL)
            if not r_name_m:
                r_name_m = re.search(r'<a\b[^>]*class="[^"]*\bcommenter\b[^"]*"[^>]*href="/([^/?#\s"]+)"[^>]*>(.*?)</a>', r_chunk, re.IGNORECASE | re.DOTALL)
                
            if r_name_m:
                rep_rec["username"] = r_name_m.group(1)
                rep_rec["display_name"] = html_mod.unescape(strip_tags(r_name_m.group(2))).strip()
                
            r_date_m = re.search(r'<span\b[^>]*class="[^"]*\bdate\b[^"]*"[^>]*>([^<]+)</span>', r_chunk, re.IGNORECASE)
            if r_date_m:
                rep_rec["date"] = html_mod.unescape(r_date_m.group(1)).strip()
                
            r_txt_m = re.search(r'<div\b[^>]*class="[^"]*\bcomment-txt\b[^"]*"[^>]*>(.*?)</div>', r_chunk, re.IGNORECASE | re.DOTALL)
            if r_txt_m:
                rep_rec["text"] = r_txt_m.group(1).strip()
                
            if rep_rec["username"] or rep_rec["text"]:
                rec["replies"].append(rep_rec)

        if rec["id"] or rec["text"]:
            rows.append(rec)
            
    return rows


def fetch_author_profile_comments(fetcher, username, max_pages=50):
    all_comments = []
    page = 1
    while page <= max_pages:
        url = "%s/artist-post/list/%s?page=%d" % (BASE, urllib.parse.quote(username), page)
        try:
            j = fetcher.get(url, as_json=True, referer="%s/%s" % (BASE, username))
            data = j.get("data") or {}
            h = maybe_unescape(data.get("html") or data.get("body") or "")
            if not h:
                break
            rows = parse_profile_wall_rows(h)
            if not rows:
                break
            all_comments.extend(rows)
            pg = data.get("pagination") or {}
            has_next = pg.get("has_next")
            if not has_next and len(rows) < 5: 
                break
            page += 1
        except FetchError:
            break
    return all_comments


def fetch_author_info(fetcher, sdata, out, args, episode_html=None):
    author_info = {
        "username": None,
        "display_name": None,
        "joined_date": None,
        "location": None,
        "bio": None,
        "tools": None,
        "subscribers_cnt": None,
        "supporters_cnt": None,
        "profile_comments": [],
        "social_links": {}
    }

    username = None
    display_name = None

    if episode_html:
        m_profile = re.search(r'class="[^"]*name-wrapper[^"]*".*?href="/([^/?#\s]+)".*?>(.*?)</a>', episode_html, re.IGNORECASE | re.DOTALL)
        if not m_profile:
            m_profile = re.search(r'data-fb-event="screen_profile"\s+href="/([^/?#\s]+)"', episode_html, re.IGNORECASE)
        
        if m_profile:
            username = m_profile.group(1)
            if len(m_profile.groups()) > 1 and m_profile.group(2):
                display_name = html_mod.unescape(strip_tags(m_profile.group(2))).strip()

    if not username:
        author_node = sdata.get("creator") or sdata.get("author") or sdata.get("owner") or {}
        username = author_node.get("username") or author_node.get("alias")
        display_name = author_node.get("fullname") or author_node.get("name")

    if not username or username == "__anonymous__":
        log("[author] aviso: nome de usuário/slug do autor não encontrado.")
        return author_info, out

    author_info["username"] = username
    author_info["display_name"] = display_name or username

    profile_url = "%s/%s" % (BASE, urllib.parse.quote(username))
    log("[author] obtendo informações do perfil do autor em %s..." % profile_url)
    try:
        html = fetcher.get(profile_url)
    except FetchError as e:
        log("[author] aviso: não foi possível carregar a página do perfil (%s)" % e)
        return author_info, out

    m_joined = re.search(r'(?:Joined|Member since)\s*[:]?\s*([A-Za-z]+\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4})', html, re.IGNORECASE)
    if m_joined:
        author_info["joined_date"] = m_joined.group(1).strip()

    m_loc = re.search(r'<i class="ico sp-field-location"></i>\s*([^<\n]+)', html, re.IGNORECASE)
    if m_loc:
        author_info["location"] = m_loc.group(1).strip()

    m_subs = re.search(r'data-sub-cnt\s*=\s*"(\d+)"', html) or re.search(r'data-title="([\d,.]+)\s*subscribers"', html, re.IGNORECASE)
    if m_subs:
        try:
            cnt_str = m_subs.group(1).replace(",", "").replace(".", "")
            author_info["subscribers_cnt"] = int(cnt_str)
        except ValueError:
            pass

    m_supp = re.search(r'data-title="([\d,.]+)\s*supporters"', html, re.IGNORECASE)
    if m_supp:
        try:
            cnt_str = m_supp.group(1).replace(",", "").replace(".", "")
            author_info["supporters_cnt"] = int(cnt_str)
        except ValueError:
            pass

    author_info["avatar_url"] = None
    m_avatar = re.search(r'<div[^>]*class="[^"]*thumb-wrap[^"]*"[^>]*>.*?<img\b[^>]*src="([^"]+)"[^>]*class="[^"]*profile-thumb[^"]*"', html, re.IGNORECASE | re.DOTALL)
    if not m_avatar:
        m_avatar = re.search(r'<img\b[^>]*class="[^"]*\bprofile-thumb\b[^"]*"[^>]*src="([^"]+)"', html, re.IGNORECASE)
    if m_avatar:
        author_info["avatar_url"] = html_mod.unescape(m_avatar.group(1)).strip()

    m_bio = re.search(r'class="[^"]*\bjs-creator-description\b[^"]*"[^>]*>(.*?)</p>', html, re.IGNORECASE | re.DOTALL)
    if m_bio:
        author_info["bio"] = html_mod.unescape(strip_tags(m_bio.group(1))).strip()

    m_tools = re.search(r'<div class="tools-wrap">.*?<h3>Tools</h3>\s*<div class="desc">(.*?)</div>', html, re.IGNORECASE | re.DOTALL)
    if m_tools:
        author_info["tools"] = html_mod.unescape(strip_tags(m_tools.group(1))).strip()

    links = {}
    user_sites_section = re.search(r'<ul\b[^>]*class="[^"]*\buser-sites\b[^"]*"[^>]*>(.*?)</ul>', html, re.IGNORECASE | re.DOTALL)
    if user_sites_section:
        site_html = user_sites_section.group(1)
        social_matches = re.findall(r'href="([^"]+)"', site_html, re.IGNORECASE)
        for link in social_matches:
            parsed_url = urllib.parse.urlparse(link)
            domain = parsed_url.netloc.lower()
            if domain and not domain.endswith("tapas.io"):
                links[domain] = link
    author_info["social_links"] = links

    log("[author] buscando posts do mural do perfil...")
    author_info["profile_comments"] = fetch_author_profile_comments(fetcher, username)

    target_author_dir = out
    if args.author_structure:
        author_folder_name = sanitize_filename("Backup %s Tapas" % author_info["display_name"])
        target_author_dir = os.path.join(os.path.dirname(out), author_folder_name)
        os.makedirs(target_author_dir, exist_ok=True)

    series_page_url = "%s/%s/series" % (BASE, urllib.parse.quote(username))
    log("[author] buscando a miniatura (cover) da série atual em %s..." % series_page_url)
    try:
        s_page_html = fetcher.get(series_page_url, referer=profile_url)
        series_items = re.findall(r'<li class="content-item">.*?</li>', s_page_html, re.DOTALL | re.IGNORECASE)
        for item_html in series_items:
            sid_match = re.search(r'data-series-id="(\d+)"', item_html)
            if sid_match and sid_match.group(1) == str(sdata.get("id") or args.series):
                img_match = re.search(r'<img\b[^>]*src="([^"]+)"', item_html, re.IGNORECASE)
                if img_match:
                    img_url = html_mod.unescape(img_match.group(1)).strip()
                    if img_url:
                        try:
                            thumb_bytes = fetcher.get_bytes(img_url, referer=series_page_url)
                            if thumb_bytes and valid_image_bytes(thumb_bytes):
                                ext = os.path.splitext(urllib.parse.urlparse(img_url).path)[1].lstrip(".").lower()
                                if not ext or ext not in ("png", "jpg", "jpeg", "gif"):
                                    ext = "jpg"
                                # Salva explicitamente como cover na pasta da série
                                specific_thumb_path = os.path.join(out, "cover.%s" % ext)
                                atomic_write_bytes(specific_thumb_path, thumb_bytes)
                                log("[series] cover da série salva com sucesso.")
                        except Exception:
                            pass
                break
    except Exception as e:
        log("[author] aviso: não foi possível carregar a página de séries do autor (%s)" % e)

    return author_info, target_author_dir


# --------------------------------------------------------------------------
# Comic panel images
# --------------------------------------------------------------------------

PANEL_IMG_RE = re.compile(
    r'<img\b[^>]*?\bdata-src\s*=\s*(?P<q>["\'])(?P<url>[^"\'>]*?)(?P=q)[^>]*>',
    re.IGNORECASE | re.DOTALL)

IMG_EXT_OK = ("png", "jpg", "jpeg", "gif")
MIN_PANEL_BYTES = 1000


def find_panels(article_html):
    out = []
    for m in PANEL_IMG_RE.finditer(article_html or ""):
        out.append({"url": html_mod.unescape(m.group("url")), "tag": m.group(0)})
    return out


def sniff_image(data):
    if not data:
        return None
    if data.startswith(b"\x89PNG"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"GIF8"):
        return "gif"
    return None


def valid_image_bytes(data):
    return bool(data) and len(data) > MIN_PANEL_BYTES and sniff_image(data) is not None


def panel_ext_from_url(url):
    try:
        path = urllib.parse.urlparse(url).path
    except ValueError:
        path = ""
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    return ext if ext in IMG_EXT_OK else "png"


def rewrite_panel_tag(tag_text, local_path):
    t = re.sub(r"\s+data-src\s*=\s*(\"[^\"]*\"|'[^']*')", "", tag_text, count=1)
    if re.search(r'\bsrc\s*=\s*"', t):
        t = re.sub(r'(\bsrc\s*=\s*")([^"]*)(")',
                   lambda mm: mm.group(1) + local_path + mm.group(3), t, count=1)
    elif re.search(r"\bsrc\s*=\s*'", t):
        t = re.sub(r"(\bsrc\s*=\s*')([^']*)(')",
                   lambda mm: mm.group(1) + local_path + mm.group(3), t, count=1)
    else:
        t = t[:4] + ' src="%s"' % local_path + t[4:]
    return t


def rewrite_article_panels(article_html, panels, prov):
    if not panels:
        return article_html
    matches = list(PANEL_IMG_RE.finditer(article_html))
    out, last = [], 0
    for i, m in enumerate(matches):
        p = prov[i] if i < len(prov) else None
        out.append(article_html[last:m.start()])
        out.append(rewrite_panel_tag(m.group(0), p["file"])
                   if (p and p.get("ok")) else m.group(0))
        last = m.end()
    out.append(article_html[last:])
    return "".join(out)


def download_panels(fetcher, ep_dir, panels, referer=None):
    img_dir = os.path.join(ep_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    prev = {}
    prev_path = os.path.join(ep_dir, "images.json")
    if os.path.isfile(prev_path):
        try:
            with open(prev_path, "r", encoding="utf-8") as f:
                for e in json.load(f):
                    if isinstance(e, dict) and e.get("file"):
                        prev[e["file"]] = e.get("url")
        except (OSError, ValueError):
            prev = {}
    prov, failed = [], []
    for i, p in enumerate(panels, 1):
        url = p["url"]
        rel = "images/panel-%03d.%s" % (i, panel_ext_from_url(url))
        apath = os.path.join(ep_dir, "images", os.path.basename(rel))
        data = None
        if os.path.isfile(apath):
            try:
                with open(apath, "rb") as f:
                    data = f.read()
            except OSError:
                data = None
        if data is not None and valid_image_bytes(data):
            prov.append({"panel": i, "url": prev.get(rel) or url,
                         "file": rel, "bytes": len(data), "ok": True})
            continue
        ok = False
        for attempt in (1, 2):
            try:
                data = fetcher.get_bytes(url, referer=referer)
            except FetchError:
                data = None
            if data is not None and valid_image_bytes(data):
                ok = True
                break
            if attempt == 1:
                time.sleep(1.0)
        if not ok:
            prov.append({"panel": i, "url": url, "file": rel,
                         "bytes": len(data or b""), "ok": False})
            failed.append({"panel": i, "url": url, "file": rel,
                           "reason": "download failed or placeholder/invalid image bytes"})
            continue
        atomic_write_bytes(apath, data)
        prov.append({"panel": i, "url": url, "file": rel,
                     "bytes": len(data), "ok": True})
    return prov, failed


# --------------------------------------------------------------------------
# Paginated walks
# --------------------------------------------------------------------------

def _next_page(pg, page):
    nxt = pg.get("page")
    if isinstance(nxt, int) and nxt > page:
        return nxt
    return page + 1


def walk_episode_list(fetcher, sid):
    ids, seen = [], set()
    page, has_next, pages = 1, True, 0
    total = None
    while has_next and pages < MAX_LIST_PAGES:
        if page == 1:
            url = ("%s/series/%s/episodes?page=1&sort=OLDEST&last_access=0&max_limit=20"
                   % (BASE, sid))
        else:
            url = ("%s/series/%s/episodes?eid=%s&page=%d&sort=OLDEST&last_access=0&max_limit=20"
                   % (BASE, sid, ids[0], page))
        j = fetcher.get(url, as_json=True)
        data = j.get("data") or {}
        pg = data.get("pagination") or {}
        total = pg.get("total", total)
        body = maybe_unescape(data.get("body") or "")
        new = 0
        for eid in parse_episode_ids(body):
            if eid not in seen:
                seen.add(eid)
                ids.append(eid)
                new += 1
        pages += 1
        if new == 0:
            has_next = False
            break
        has_next = bool(pg.get("has_next"))
        page = _next_page(pg, page)
    complete = (not has_next) and pages < MAX_LIST_PAGES
    return ids, pages, total, complete


def fetch_comment_pages(fetcher, ep_id, limit_pages=None):
    comments, pages, capped = [], 0, False
    page, has_next = 1, True
    while has_next:
        if limit_pages is not None and pages >= limit_pages:
            capped = True
            break
        if pages >= MAX_COMMENT_PAGES:
            capped = True
            break
        url = ("%s/comment/%s?page=%d&sort=NEWEST&since=0&init_load=0&wr=true&ep=false"
               % (BASE, ep_id, page))
        j = fetcher.get(url, as_json=True, referer="%s/episode/%s" % (BASE, ep_id))
        data = j.get("data") or {}
        pg = data.get("pagination") or {}
        h = maybe_unescape(data.get("html") or "")
        rows = parse_comment_rows(h)
        if not rows:
            break
        comments.extend(rows)
        pages += 1
        has_next = bool(pg.get("has_next"))
        page = _next_page(pg, page)
    return comments, pages, capped


def fetch_replies(fetcher, ep_id, comment_id, limit_pages=None):
    replies, pages, capped = [], 0, False
    page, has_next = 1, True
    while has_next:
        if limit_pages is not None and pages >= limit_pages:
            capped = True
            break
        if pages >= MAX_REPLY_PAGES:
            capped = True
            break
        url = "%s/comment/%s/%s/replies?page=%d" % (BASE, ep_id, comment_id, page)
        j = fetcher.get(url, as_json=True, referer="%s/episode/%s" % (BASE, ep_id))
        data = j.get("data") or {}
        pg = data.get("pagination") or {}
        h = maybe_unescape(data.get("html") or "")
        rows = parse_reply_rows(h)
        if not rows:
            break
        replies.extend(rows)
        pages += 1
        has_next = bool(pg.get("has_next"))
        page = _next_page(pg, page)
    return replies, pages, capped


# --------------------------------------------------------------------------
# Series arg resolution & Author Series Discovery
# --------------------------------------------------------------------------

SERIES_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:m\.)?tapas\.io/series/([^/?#\s]+)",
    re.IGNORECASE)

SLUG_OK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._~-]*$")


def resolve_author_slug(value):
    v = (value or "").strip()
    m = re.search(r"(?:https?://)?(?:www\.)?(?:m\.)?tapas\.io/([^/?#\s]+)", v, re.IGNORECASE)
    if m:
        slug = m.group(1)
        if slug.lower() not in ("series", "episode", "comment", "artist-post"):
            return slug
    if v and "/" not in v and ":" not in v:
        return v
    return None


def fetch_author_series_list(fetcher, author_slug):
    series_list = []
    url = "%s/%s/series" % (BASE, urllib.parse.quote(author_slug))
    log("[author] procurando todas as obras do autor em %s..." % url)
    try:
        html = fetcher.get(url)
        items = re.findall(r'<li class="content-item">.*?</li>', html, re.DOTALL | re.IGNORECASE)
        for item in items:
            sid_m = re.search(r'data-series-id="(\d+)"', item)
            title_m = re.search(r'<a[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</a>', item, re.IGNORECASE | re.DOTALL)
            if sid_m:
                sid = sid_m.group(1)
                title = html_mod.unescape(strip_tags(title_m.group(1))).strip() if title_m else sid
                series_list.append({"id": sid, "title": title})
    except Exception as e:
        log("[author] erro ao buscar lista de séries do autor: %s" % e)
    return series_list


def series_slug_from_arg(value):
    v = (value or "").strip()
    m = re.search(r"(?:https?://)?(?:www\.)?(?:m\.)?tapas\.io/series/([^/?#\s]+)", v, re.IGNORECASE)
    if m:
        slug = urllib.parse.unquote(m.group(1))
    elif v and "/" not in v and ":" not in v:
        slug = v
    else:
        return None
    return slug if SLUG_OK_RE.match(slug) else None


SERIES_ID_PATTERNS = (
    r"tapastic://series/(\d+)",
    r'data-series-id="(\d+)"',
    r'data-tiara-event-meta-series-id="(\d+)"',
    r"series/(\d+)/episodes",
    r"/series/(\d+)",
)


def extract_series_id_from_series_html(page_html):
    for pat in SERIES_ID_PATTERNS:
        m = re.search(pat, page_html or "")
        if m:
            return m.group(1)
    return None


def resolve_series_arg(value, fetcher):
    v = (value or "").strip()
    if not v:
        raise FetchError("--series is empty.")
    if v.isdigit():
        return v
    slug = series_slug_from_arg(v)
    if slug is None:
        raise FetchError("--series %r inválido." % (value,))
    if slug.isdigit():
        return slug
    url = "%s/series/%s" % (BASE, urllib.parse.quote(slug))
    log("[series] resolvendo link da série %r (%s)..." % (value, url))
    page_html = fetcher.get(url)
    sid = extract_series_id_from_series_html(page_html)
    if not sid:
        raise FetchError("id numérico da série não encontrado para %r." % (slug,))
    return sid


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------

def manifest_path(out):
    return os.path.join(out, "manifest.json")


def load_manifest(out, sid):
    path = manifest_path(out)
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                m = json.load(f)
            if m.get("series_id") == sid:
                m.setdefault("episodes", {})
                m.setdefault("gaps", [])
                m.setdefault("warnings", [])
                return m
        except (OSError, ValueError):
            pass
    return {"series_id": sid, "created": now_iso(), "updated": now_iso(),
            "episodes": {}, "gaps": [], "warnings": []}


def save_manifest(out, m):
    m["updated"] = now_iso()
    atomic_write_json(manifest_path(out), m)


def add_gap(m, num, eid, reason):
    for g in m["gaps"]:
        if g.get("episode_id") == eid and g.get("reason") == reason:
            return
    m["gaps"].append({"num": num, "episode_id": eid, "reason": reason, "ts": now_iso()})


def write_gaps(out, m):
    lines = ["# gaps for series %s" % m.get("series_id"), "# generated %s" % now_iso(), ""]
    for g in m["gaps"]:
        lines.append("ep %s (id %s): %s" % (g.get("num"), g.get("episode_id"), g.get("reason")))
    atomic_write_text(os.path.join(out, "gaps.txt"), "\n".join(lines) + "\n")


# --------------------------------------------------------------------------
# Episode processing
# --------------------------------------------------------------------------

def episode_dir(out, num, eid):
    return os.path.join(out, "episodes", "%04d-%s" % (num, eid))


def to_json_comment(c):
    return {"id": c["id"], "username": c["username"], "display_name": c["display_name"],
            "date": c["date"], "text": c["text"], "likes": c["likes"],
            "is_creator": c["is_creator"],
            "replies": [to_json_reply(r) for r in c["replies"]]}


def to_json_reply(r):
    return {"id": r["id"], "username": r["username"], "display_name": r["display_name"],
            "date": r["date"], "text": r["text"], "likes": r["likes"],
            "is_creator": r["is_creator"]}


def should_skip(out, manifest, num, eid, args):
    rec = manifest["episodes"].get(str(eid))
    if not rec or rec.get("status") != "complete":
        return False
    d = episode_dir(out, num, eid)
    if not os.path.isfile(os.path.join(d, "index.json")):
        return False
    if not os.path.isfile(os.path.join(d, "comments.json")):
        return False
    need_content = (not args.comments_only) and rec.get("free", True)
    if need_content and rec.get("content_saved") and not os.path.isfile(os.path.join(d, "article.html")):
        return False
    if rec.get("images", 0):
        if not rec.get("images_complete", True):
            return False
        ipath = os.path.join(d, "images.json")
        if not os.path.isfile(ipath):
            return False
        try:
            with open(ipath, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except (OSError, ValueError):
            return False
        if len(entries) < rec.get("images", 0):
            return False
        for e in entries:
            try:
                if os.path.getsize(os.path.join(d, e.get("file") or "")) != e.get("bytes"):
                    return False
            except OSError:
                return False
    return True


def process_episode(fetcher, out, manifest, num, eid, args):
    d = episode_dir(out, num, eid)
    os.makedirs(d, exist_ok=True)
    rec = {"num": num, "episode_id": eid, "ts": now_iso(), "status": "complete"}

    j = fetcher.get("%s/episode/%s/info" % (BASE, eid), as_json=True)
    info = j.get("data") or {}
    if not info:
        raise FetchError("episode info returned no data")

    free = bool(info.get("free"))
    open_comments = bool(info.get("open_comments"))
    comment_cnt = info.get("comment_cnt") or 0
    
    ep_views = info.get("view_cnt")
    ep_likes = info.get("like_cnt")

    creator_note = None
    page_html = ""
    try:
        page_html = fetcher.get("%s/episode/%s" % (BASE, eid))
        m_story = re.search(r'<p\b[^>]*class="[^"]*\bjs-episode-story\b[^"]*"[^>]*>(.*?)</p>', page_html, re.IGNORECASE | re.DOTALL)
        if m_story:
            creator_note = html_mod.unescape(m_story.group(1)).strip()
    except Exception:
        pass

    info["creator_note"] = creator_note

    atomic_write_json(os.path.join(d, "index.json"),
                      {"num": num, "episode_id": eid, "fetched_at": now_iso(), "data": info})

    rec.update({"title": info.get("title"), "free": free,
                "open_comments": open_comments, "comment_cnt": comment_cnt,
                "views": ep_views, "likes": ep_likes, "creator_note": creator_note})

    if not args.comments_only and free:
        if not page_html:
            page_html = fetcher.get("%s/episode/%s" % (BASE, eid))
        full, inner = extract_article(page_html)
        if full is None:
            add_gap(manifest, num, eid, "article element not found on free episode")
            rec["status"] = "error"
            rec["error"] = "no-article"
            return rec
        panels = find_panels(full)
        if panels:
            prov, failed = download_panels(fetcher, d, panels,
                                           referer="%s/episode/%s" % (BASE, eid))
            full = rewrite_article_panels(full, panels, prov)
            ok = [e for e in prov if e.get("ok")]
            atomic_write_json(os.path.join(d, "images.json"),
                              [{"panel": e["panel"], "url": e["url"],
                                "file": e["file"], "bytes": e["bytes"]}
                               for e in ok])
            rec["images"] = len(panels)
            rec["images_ok"] = len(ok)
            rec["images_complete"] = not failed
            if failed:
                for fp in failed:
                    add_gap(manifest, num, eid, "panel %d failed" % fp["panel"])
                rec["status"] = "error"
                rec["error"] = "images-incomplete"
        atomic_write_text(os.path.join(d, "article.html"), full)
        rec["content_saved"] = True
        rec["article_bytes"] = len(full.encode("utf-8"))
    elif not free:
        add_gap(manifest, num, eid, "locked (free=false)")

    comments = []
    cpages = 0
    ccapped = False
    if comment_cnt > 0 or open_comments:
        comments, cpages, ccapped = fetch_comment_pages(fetcher, eid, args.limit_comments_pages)
    rec["comments"] = len(comments)

    reply_total = 0
    rpages_max = 0
    rcapped_any = False
    for c in comments:
        if c.get("reply_cnt", 0) > 0:
            reps, rpages, rcapped = fetch_replies(fetcher, eid, c["id"], args.limit_reply_pages)
            c["replies"] = reps
            reply_total += len(reps)
            rpages_max = max(rpages_max, rpages)
    rec["replies"] = reply_total

    atomic_write_json(os.path.join(d, "comments.json"),
                      [to_json_comment(c) for c in comments])
    return rec


# --------------------------------------------------------------------------
# Process single series runner
# --------------------------------------------------------------------------

def run_single_series(series_id, args, fetcher):
    args.series = series_id
    base_out = args.out if args.out else "."
    
    temp_sj_data = {}
    series_info_html = ""
    try:
        j_pre = fetcher.get("%s/series/%s" % (BASE, args.series), as_json=True)
        temp_sj_data = j_pre.get("data") or {}
    except Exception:
        pass

    series_slug = temp_sj_data.get("url") or args.series
    info_url = "%s/series/%s/info" % (BASE, urllib.parse.quote(series_slug))
    try:
        series_info_html = fetcher.get(info_url)
    except Exception:
        try:
            series_info_html = fetcher.get("%s/series/%s" % (BASE, args.series))
        except Exception:
            pass

    series_title = temp_sj_data.get("title") or args.series
    
    if args.original_name:
        folder_name = sanitize_filename(series_title)
    else:
        folder_name = "tapas-archive-%s" % args.series

    out = os.path.abspath(os.path.join(base_out, folder_name))
    os.makedirs(out, exist_ok=True)
    
    manifest = load_manifest(out, args.series)

    if manifest.get("episode_ids") and not args.refresh_list and not args.force:
        ids = [str(i) for i in manifest["episode_ids"]]
    else:
        log("[list] obtendo lista de episódios...")
        ids, pages, total, complete = walk_episode_list(fetcher, args.series)
        manifest["episode_ids"] = ids
        save_manifest(out, manifest)

    sj = os.path.join(out, "series.json")
    
    publish_date = None
    last_updated_date = None
    if ids:
        try:
            first_info_j = fetcher.get("%s/episode/%s/info" % (BASE, ids[0]), as_json=True)
            publish_date = (first_info_j.get("data") or {}).get("publish_date")
            
            if len(ids) > 1:
                last_info_j = fetcher.get("%s/episode/%s/info" % (BASE, ids[-1]), as_json=True)
                last_updated_date = (last_info_j.get("data") or {}).get("publish_date")
            else:
                last_updated_date = publish_date
        except Exception:
            pass

    s_views = None
    s_subs = None
    s_likes = None
    s_desc = None

    if series_info_html:
        m_v = re.search(r'data-title="([\d,.]+)\s*views"', series_info_html, re.IGNORECASE) or re.search(r'>([\d,.]+k?)\s*views</a>', series_info_html, re.IGNORECASE)
        if m_v:
            s_views = m_v.group(1).strip()
            
        m_sub = re.search(r'data-title="([\d,.]+)\s*subscribers"', series_info_html, re.IGNORECASE) or re.search(r'data-cnt="(\d+)"[^>]*>([\d,.]+k?)\s*subscribers', series_info_html, re.IGNORECASE)
        if m_sub:
            s_subs = m_sub.group(1).strip()
            
        m_l = re.search(r'data-title="([\d,.]+)\s*likes"', series_info_html, re.IGNORECASE) or re.search(r'>([\d,.]+k?)\s*likes</a>', series_info_html, re.IGNORECASE)
        if m_l:
            s_likes = m_l.group(1).strip()
            
        m_d = re.search(r'<p\b[^>]*class="[^"]*\bdescription\b[^"]*"[^>]*>.*?<span\b[^>]*class="[^"]*\bdescription__body\b[^"]*"[^>]*>(.*?)</span>', series_info_html, re.IGNORECASE | re.DOTALL)
        if not m_d:
            m_d = re.search(r'<p\b[^>]*class="[^"]*\bdescription\b[^"]*"[^>]*>(.*?)</p>', series_info_html, re.IGNORECASE | re.DOTALL)
        if m_d:
            s_desc = html_mod.unescape(strip_tags(m_d.group(1))).strip()

    if os.path.isfile(sj) and not args.force:
        log("[series] series.json exists -> cached")
        try:
            with open(sj, "r", encoding="utf-8") as f:
                existing_sj = json.load(f)
                sdata = existing_sj.get("data") or {}
            manifest["series_title"] = sdata.get("title")
        except (OSError, ValueError):
            sdata = {}
    else:
        sdata = temp_sj_data if temp_sj_data else (fetcher.get("%s/series/%s" % (BASE, args.series), as_json=True).get("data") or {})
        
        series_output_obj = {
            "series_id": args.series,
            "title": series_title,
            "description": s_desc,
            "views": s_views,
            "subscribers": s_subs,
            "likes": s_likes,
            "publish_date": publish_date,
            "last_updated_date": last_updated_date,
            "fetched_at": now_iso(),
            "data": sdata
        }
        atomic_write_json(sj, series_output_obj)
        manifest["series_title"] = sdata.get("title") or series_title
        log("[series] %s (%s)" % (manifest["series_title"], sdata.get("type")))
        save_manifest(out, manifest)

    author_json_path = os.path.join(out, "author.json")
    author_comments_path = os.path.join(out, "author_comments.json")
    
    ep_full_page_html = ""
    first_eid = ids[0] if ids else None
    if first_eid:
        try:
            ep_full_page_html = fetcher.get("%s/episode/%s" % (BASE, first_eid))
        except Exception:
            pass

    if not os.path.isfile(author_json_path) or args.force:
        log("[author] extraindo informações do autor...")
        author_data, final_out_dir = fetch_author_info(fetcher, sdata, out, args, episode_html=ep_full_page_html)
        
        if final_out_dir != out:
            old_out = out
            out = final_out_dir
            os.makedirs(out, exist_ok=True)
            series_folder_name = os.path.basename(old_out)
            new_series_out = os.path.join(out, series_folder_name)
            if old_out != out and os.path.exists(old_out) and not os.path.exists(new_series_out):
                import shutil
                shutil.move(old_out, new_series_out)
                out = new_series_out
                author_json_path = os.path.join(out, "author.json")
                author_comments_path = os.path.join(out, "author_comments.json")
        
        avatar_url = author_data.pop("avatar_url", None)
        username = author_data.get("username")
        if avatar_url and username:
            profile_url = "%s/%s" % (BASE, urllib.parse.quote(username))
            log("[author] baixando avatar do autor...")
            try:
                avatar_bytes = fetcher.get_bytes(avatar_url, referer=profile_url)
                if avatar_bytes:
                    avatar_ext = os.path.splitext(urllib.parse.urlparse(avatar_url).path)[1].lstrip(".").lower()
                    if not avatar_ext or avatar_ext not in ("png", "jpg", "jpeg", "gif"):
                        avatar_ext = "png"
                    avatar_target_dir = os.path.dirname(out) if args.author_structure else out
                    atomic_write_bytes(os.path.join(avatar_target_dir, "avatar.%s" % avatar_ext), avatar_bytes)
            except Exception:
                pass

        profile_comments = author_data.pop("profile_comments", [])
        atomic_write_json(os.path.join(os.path.dirname(out) if args.author_structure else out, "author.json"), {"fetched_at": now_iso(), "data": author_data})
        atomic_write_json(os.path.join(os.path.dirname(out) if args.author_structure else out, "author_comments.json"), {"fetched_at": now_iso(), "username": username, "comments": profile_comments})

    if ep_full_page_html:
        m_header = re.search(r'class="header-layer"[^>]*style="[^"]*background-image:\s*url\([\'"]?([^\'")]+)[\'"]?\)', ep_full_page_html, re.IGNORECASE)
        if m_header:
            header_url = html_mod.unescape(m_header.group(1)).strip()
            header_path = os.path.join(out, "series-header.jpg")
            if not os.path.isfile(header_path) or args.force:
                try:
                    h_bytes = fetcher.get_bytes(header_url)
                    if h_bytes:
                        atomic_write_bytes(header_path, h_bytes)
                except Exception:
                    pass

        m_sthumb = re.search(r'<div\b[^>]*class="[^"]*thumb-wrapper[^"]*"[^>]*>.*?<img\b[^>]*src="([^"]+)"', ep_full_page_html, re.IGNORECASE | re.DOTALL)
        if m_sthumb:
            sthumb_url = html_mod.unescape(m_sthumb.group(1)).strip()
            sthumb_path = os.path.join(out, "series-thumb.jpg")
            if not os.path.isfile(sthumb_path) or args.force:
                try:
                    st_bytes = fetcher.get_bytes(sthumb_url)
                    if st_bytes:
                        atomic_write_bytes(sthumb_path, st_bytes)
                except Exception:
                    pass

    lo, hi = parse_range(args.episode_range) if args.episode_range else (1, len(ids))
    hi = min(hi, len(ids))
    if args.limit_episodes is not None:
        hi = min(hi, lo + args.limit_episodes - 1) if lo > 1 else min(hi, args.limit_episodes)
    selected = [(n, ids[n - 1]) for n in range(lo, hi + 1)]

    processed = skipped = failed = 0
    for num, eid in selected:
        if not args.force and should_skip(out, manifest, num, eid, args):
            skipped += 1
            continue
        log("[ep %d] id %s: baixando..." % (num, eid))
        try:
            rec = process_episode(fetcher, out, manifest, num, eid, args)
            manifest["episodes"][str(eid)] = rec
            if rec.get("status") == "complete":
                processed += 1
            else:
                failed += 1
        except (FetchError, OSError) as e:
            failed += 1
            add_gap(manifest, num, eid, "falha: %s" % e)
            manifest["episodes"][str(eid)] = {"num": num, "episode_id": eid,
                                              "status": "error", "error": str(e), "ts": now_iso()}
        save_manifest(out, manifest)

    write_gaps(out, manifest)
    log("\n== resumo série ==\nsérie: %s\nprocessados: %d | ignorados: %d | falhas: %d\nsaída: %s"
        % (manifest.get("series_title"), processed, skipped, failed, out))
    return 0 if failed == 0 else 1


def parse_range(spec):
    m = re.match(r"^\s*(\d+)(?:\s*-\s*(\d+))?\s*$", spec or "")
    if not m:
        raise argparse.ArgumentTypeError("bad --episode-range")
    lo = int(m.group(1))
    hi = int(m.group(2)) if m.group(2) else lo
    return lo, hi


def run(args):
    fetcher = Fetcher(rate=args.rate, max_tries=args.max_tries,
                      timeout=args.timeout, cookie=args.cookie)
    
    if args.author:
        author_slug = resolve_author_slug(args.author)
        if not author_slug:
            raise FetchError("--author inválido. Informe o link ou o nome do autor.")
        
        series_list = fetch_author_series_list(fetcher, author_slug)
        if not series_list:
            log("[author] nenhuma série encontrada para o autor %s." % author_slug)
            return 1
            
        log("[author] encontradas %d séries para o autor %s." % (len(series_list), author_slug))
        exit_code = 0
        for s in series_list:
            log("\n--- Processando série: %s (ID: %s) ---" % (s["title"], s["id"]))
            try:
                res = run_single_series(s["id"], args, fetcher)
                if res != 0:
                    exit_code = 1
            except Exception as e:
                log("[erro] falha ao processar a série %s: %s" % (s["id"], e))
                exit_code = 1
        return exit_code
    elif args.series:
        sid = resolve_series_arg(args.series, fetcher)
        return run_single_series(sid, args, fetcher)
    else:
        raise FetchError("Você deve fornecer --series ou --author.")


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    p = argparse.ArgumentParser(description="Archive a Tapas.io series or full author catalog.")
    p.add_argument("--series", help="numeric series id, slug, or series URL")
    p.add_argument("--author", help="author profile URL or username slug to download all works")
    p.add_argument("--out", default=None, help="output directory")
    p.add_argument("--cookie", default=None, help="optional Cookie header")
    p.add_argument("--episode-range", default=None, help="episode range, e.g. 1-50")
    p.add_argument("--limit-episodes", type=int, default=None)
    p.add_argument("--comments-only", action="store_true")
    p.add_argument("--limit-comments-pages", type=int, default=None)
    p.add_argument("--limit-reply-pages", type=int, default=None)
    p.add_argument("--rate", type=float, default=2.0)
    p.add_argument("--max-tries", type=int, default=4)
    p.add_argument("--timeout", type=int, default=30)
    p.add_argument("--refresh-list", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--original-name", action="store_true", help="Salva a pasta da série com o nome original do Tapas.")
    p.add_argument("--author-structure", action="store_true", help="Organiza a estrutura em uma pasta raiz com o nome do autor.")
    args = p.parse_args(argv)

    if not args.series and not args.author:
        p.error("Você deve especificar --series ou --author")
    try:
        return run(args)
    except FetchError as e:
        log("[erro] %s" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main())