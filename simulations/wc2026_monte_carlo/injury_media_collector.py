"""Collect in-tournament injury signals from sports media outlets."""

from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
import requests

from .config import DATA_DIR, DEFAULT_SQUAD_CLUBS_PATH

GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
)
GUARDIAN_WC_RSS = "https://www.theguardian.com/football/world-cup-2026/rss"
ESPN_WC_NEWS_API = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/news"

_USER_AGENT = "wc2026-injury-collector/1.0 (research; contact: local)"

_INJURY_KEYWORDS = re.compile(
    r"\b(?:injur(?:y|ies|ed)|hamstring|concussion|muscle strain|strained|"
    r"knock|torn|rupture|cramp|sprain|fracture|dislocat\w*|calf|ankle|knee|"
    r"groin|thigh|ligament)\b",
    re.IGNORECASE,
)
_INJURY_OUT_KEYWORDS = re.compile(
    r"\b(?:ruled out|will miss|out of|out for|unable to|sidelined|"
    r"miss(?:es)?\s+(?:the\s+)?(?:next|world cup))\b",
    re.IGNORECASE,
)
_SUB_KEYWORDS = re.compile(
    r"\b(?:subbed|substitut\w*|forced off|taken off|withdrawn|early exit|"
    r"halftime sub|half-time sub|half time sub)\b",
    re.IGNORECASE,
)
_RECOVERY_KEYWORDS = re.compile(
    r"\b(?:plays down|good news|returns? to (?:training|practice)|"
    r"back in training|fit again|shrugs off|available for|starts? after)\b",
    re.IGNORECASE,
)
_RECOVERY_CLEAR_KEYWORDS = re.compile(
    r"\b(?:returns? to (?:training|practice|action)|back in training|"
    r"available|fit again|cleared to play|passed fitness|recovered|"
    r"back in (?:the )?lineup|named in (?:squad|lineup)|starts? (?:against|vs))\b",
    re.IGNORECASE,
)
_PREMATCH_KEYWORDS = re.compile(
    r"\b(?:lineups?|team news|starts? for|starting lineup|confirmed lineups?|"
    r"prediction|preview|how to watch|kick[- ]?off time)\b",
    re.IGNORECASE,
)
_SUBBED_OUT = re.compile(r"\bsubbed out\b", re.IGNORECASE)
_VS_OPPONENT = re.compile(
    r"\bvs\.?\s+([A-Za-z][A-Za-z\s\-']+?)(?:\s+at|\s+in|\s+for|\s+on\b|,|$|\s+\d)",
    re.IGNORECASE,
)

# Outlets referenced in news_sources_reference.md and match_events.csv.
KNOWN_OUTLETS = (
    "AP News",
    "Reuters",
    "ESPN",
    "BBC Sport",
    "BBC",
    "The Guardian",
    "Guardian",
    "NYT Athletic",
    "The Athletic",
    "USA Today",
    "FOX Sports",
    "Fox Sports",
    "CBS Sports",
    "Yahoo Sports",
    "Sky Sports",
    "Al Jazeera",
    "NY Post",
    "New York Post",
    "Bleacher Report",
    "Transfermarkt",
    "beIN SPORTS",
    "The Independent",
    "Independent",
    "Korea Herald",
    "NYT Athletic",
)

_SOURCE_ALIASES = {
    "The Athletic - The New York Times": "NYT Athletic",
    "The New York Times": "NYT Athletic",
    "Fox Sports": "FOX Sports",
    "Fox News": "FOX Sports",
}

_SOURCE_PRIORITY = {
    "curated": 100,
    "AP News": 90,
    "Reuters": 90,
    "ESPN": 85,
    "BBC Sport": 85,
    "BBC": 85,
    "FIFA": 85,
    "The Guardian": 80,
    "Guardian": 80,
    "NYT Athletic": 80,
    "USA Today": 75,
    "FOX Sports": 75,
    "CBS Sports": 75,
    "Yahoo Sports": 75,
    "Sky Sports": 70,
    "Al Jazeera": 70,
    "Transfermarkt": 65,
    "Wikipedia": 60,
}


def _source_priority(source: str) -> int:
    return _SOURCE_PRIORITY.get(source, 50)


def _normalize_source(raw: str) -> str:
    source = unescape(raw).strip()
    return _SOURCE_ALIASES.get(source, source)


def _split_headline_source(headline: str) -> tuple[str, str]:
    text = unescape(headline).strip()
    if " - " not in text:
        return text, "Google News"
    title, source = text.rsplit(" - ", 1)
    return title.strip(), _normalize_source(source.strip())


def _fetch_text(url: str, timeout: int = 20) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": _USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.text


def _parse_rss_items(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    items: list[dict] = []
    for item in root.findall(".//item"):
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        pub = item.findtext("pubDate") or ""
        description = item.findtext("description") or ""
        published: date | None = None
        if pub:
            try:
                published = parsedate_to_datetime(pub).date()
            except (TypeError, ValueError, OverflowError):
                published = None
        items.append(
            {
                "headline": unescape(title),
                "link": link,
                "published": published,
                "description": unescape(description),
            }
        )
    return items


def load_squad_players(
    home: str,
    away: str,
    path: Path | str = DEFAULT_SQUAD_CLUBS_PATH,
) -> dict[str, str]:
    """Map player name -> team for the two sides in a fixture."""
    path = Path(path)
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    mask = df["team"].isin([home, away])
    players = df.loc[mask, ["player", "team"]].dropna()
    return {
        str(row["player"]).strip(): str(row["team"])
        for _, row in players.iterrows()
    }


def _match_player(text: str, players: dict[str, str]) -> str | None:
    lowered = text.lower()
    for name in sorted(players, key=len, reverse=True):
        if name.lower() in lowered:
            return name
    last_name_hits = []
    for name in players:
        parts = name.split()
        if parts and parts[-1].lower() in lowered:
            last_name_hits.append(name)
    if len(last_name_hits) == 1:
        return last_name_hits[0]
    return None


def _injury_notes(title: str) -> str:
    body = re.search(r"\(([^)]+)\)", title)
    if body and _INJURY_KEYWORDS.search(body.group(1)):
        return f"{body.group(1)}; {title[:120]}"
    return title[:160]


def _is_injury_out(title: str) -> bool:
    if _SUBBED_OUT.search(title):
        return False
    return bool(_INJURY_OUT_KEYWORDS.search(title))


def _mentions_wrong_opponent(title: str, home: str, away: str) -> bool:
    allowed = {home.lower(), away.lower()}
    for match in _VS_OPPONENT.finditer(title):
        opponent = match.group(1).strip().lower()
        if any(team in opponent or opponent in team for team in allowed):
            continue
        if len(opponent) >= 4 and home.lower() in title.lower():
            return True
    clash = re.search(
        r"(?:clash|match|game|fixture)\s+with\s+([A-Za-z][A-Za-z\s\-']+)",
        title,
        re.IGNORECASE,
    )
    if clash:
        opponent = clash.group(1).strip().lower()
        if opponent not in allowed and home.lower() in title.lower():
            return True
    return False


def _classify_headline(title: str) -> tuple[str, float, bool] | None:
    if _PREMATCH_KEYWORDS.search(title) and not _SUB_KEYWORDS.search(title):
        return None
    if _RECOVERY_KEYWORDS.search(title) and not _is_injury_out(title):
        return None
    if not (_INJURY_KEYWORDS.search(title) or _SUB_KEYWORDS.search(title)):
        return None

    if _is_injury_out(title):
        return "injury_out", 0.10, True
    if re.search(r"concussion", title, re.IGNORECASE):
        return "injury_monitor", 0.08, False
    if _SUB_KEYWORDS.search(title):
        return "injury_monitor", 0.05, False
    return "injury_monitor", 0.05, False


def parse_injury_headline(
    headline: str,
    players: dict[str, str],
    *,
    home: str = "",
    away: str = "",
    default_source: str = "Google News",
) -> dict | None:
    title, source = _split_headline_source(headline)
    source = source or default_source
    if home and away and _mentions_wrong_opponent(title, home, away):
        return None
    classification = _classify_headline(title)
    if classification is None:
        return None

    player = _match_player(title, players)
    if not player:
        return None

    event_type, severity, misses_next = classification
    return {
        "team": players[player],
        "player": player,
        "event_type": event_type,
        "severity": severity,
        "misses_next_match": misses_next,
        "yellow_count": 0,
        "notes": _injury_notes(title),
        "source": source,
    }


def _date_window(match_date: str, days_after: int = 2) -> tuple[str, str]:
    start = date.fromisoformat(match_date)
    end = start + timedelta(days=days_after)
    return start.isoformat(), end.isoformat()


def _google_news_queries(home: str, away: str, match_date: str) -> list[str]:
    start, end = _date_window(match_date)
    teams = f"({home} OR {away})"
    return [
        f"{home} {away} World Cup injury after:{start} before:{end}",
        f"{teams} World Cup injury after:{start} before:{end}",
        f"{home} {away} World Cup subbed after:{start} before:{end}",
    ]


def _google_recovery_queries(home: str, away: str, match_date: str) -> list[str]:
    start, end = _date_window(match_date, days_after=5)
    return [
        f"{home} World Cup available returns training after:{start} before:{end}",
        f"{away} World Cup available returns training after:{start} before:{end}",
        f"{home} {away} World Cup cleared to play after:{start} before:{end}",
    ]


def parse_recovery_headline(
    headline: str,
    players: dict[str, str],
    *,
    home: str = "",
    away: str = "",
    default_source: str = "Google News",
) -> dict | None:
    title, source = _split_headline_source(headline)
    source = source or default_source
    if home and away and _mentions_wrong_opponent(title, home, away):
        return None
    if not _RECOVERY_CLEAR_KEYWORDS.search(title):
        return None
    if _is_injury_out(title):
        return None

    player = _match_player(title, players)
    if not player:
        return None

    return {
        "team": players[player],
        "player": player,
        "event_type": "injury_clear",
        "severity": 0.0,
        "misses_next_match": False,
        "yellow_count": 0,
        "notes": title[:160],
        "source": source,
    }


def _fetch_google_news(query: str) -> list[dict]:
    url = GOOGLE_NEWS_RSS.format(query=quote_plus(query))
    return _parse_rss_items(_fetch_text(url))


def _fetch_guardian_items() -> list[dict]:
    try:
        return _parse_rss_items(_fetch_text(GUARDIAN_WC_RSS))
    except Exception:
        return []


def _fetch_espn_items() -> list[dict]:
    try:
        payload = requests.get(
            ESPN_WC_NEWS_API,
            headers={"User-Agent": _USER_AGENT},
            timeout=20,
        ).json()
    except Exception:
        return []

    items: list[dict] = []
    for article in payload.get("articles", []):
        published: date | None = None
        ts = article.get("published")
        if ts:
            try:
                published = datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
            except ValueError:
                published = None
        items.append(
            {
                "headline": article.get("headline", ""),
                "link": article.get("links", {}).get("web", {}).get("href", ""),
                "published": published,
                "description": article.get("description", ""),
                "source": "ESPN",
            }
        )
    return items


def _item_matches_fixture(
    item: dict,
    home: str,
    away: str,
    match_date: str,
    *,
    window_days: int = 2,
) -> bool:
    text = f"{item.get('headline', '')} {item.get('description', '')}".lower()
    home_hit = home.lower() in text
    away_hit = away.lower() in text
    if not (home_hit or away_hit):
        return False

    published = item.get("published")
    if published is None:
        return home_hit and away_hit
    start = date.fromisoformat(match_date)
    end = start + timedelta(days=window_days)
    return start <= published <= end


def collect_media_injuries_for_match(
    home: str,
    away: str,
    match_date: str,
    *,
    squad_path: Path | str = DEFAULT_SQUAD_CLUBS_PATH,
    sleep_s: float = 0.25,
) -> list[dict]:
    """
    Search sports media (Google News aggregation + Guardian + ESPN) for
    post-match injury reports involving either team.
    """
    players = load_squad_players(home, away, squad_path)
    if not players:
        return []

    candidates: dict[tuple, dict] = {}
    seen_headlines: set[str] = set()

    def add_headline(headline: str, default_source: str = "Google News") -> None:
        norm = headline.strip().lower()
        if not norm or norm in seen_headlines:
            return
        seen_headlines.add(norm)
        event = parse_injury_headline(
            headline,
            players,
            home=home,
            away=away,
            default_source=default_source,
        )
        if not event:
            return
        key = (
            match_date,
            event["team"],
            event["player"],
            event["event_type"],
        )
        existing = candidates.get(key)
        if existing is None or _source_priority(event["source"]) > _source_priority(
            existing["source"]
        ):
            candidates[key] = event

    for query in _google_news_queries(home, away, match_date):
        try:
            for item in _fetch_google_news(query):
                add_headline(item["headline"])
        except Exception:
            pass
        time.sleep(sleep_s)

    for item in _fetch_guardian_items():
        if not _item_matches_fixture(item, home, away, match_date):
            continue
        add_headline(item["headline"], default_source="The Guardian")

    for item in _fetch_espn_items():
        if not _item_matches_fixture(item, home, away, match_date):
            continue
        headline = item["headline"]
        if item.get("source"):
            headline = f"{headline} - {item['source']}"
        add_headline(headline, default_source="ESPN")

    return list(candidates.values())


def collect_media_recovery_for_match(
    home: str,
    away: str,
    match_date: str,
    *,
    squad_path: Path | str = DEFAULT_SQUAD_CLUBS_PATH,
    sleep_s: float = 0.25,
) -> list[dict]:
    """Collect injury clearance signals from sports media headlines."""
    players = load_squad_players(home, away, squad_path)
    if not players:
        return []

    clears: dict[tuple, dict] = {}
    seen_headlines: set[str] = set()

    def add_headline(headline: str, default_source: str = "Google News") -> None:
        norm = headline.strip().lower()
        if not norm or norm in seen_headlines:
            return
        seen_headlines.add(norm)
        event = parse_recovery_headline(
            headline,
            players,
            home=home,
            away=away,
            default_source=default_source,
        )
        if not event:
            return
        key = (event["team"], event["player"])
        existing = clears.get(key)
        if existing is None or _source_priority(event["source"]) > _source_priority(
            existing["source"]
        ):
            clears[key] = event

    for query in _google_recovery_queries(home, away, match_date):
        try:
            for item in _fetch_google_news(query):
                add_headline(item["headline"])
        except Exception:
            pass
        time.sleep(sleep_s)

    for item in _fetch_guardian_items():
        if not _item_matches_fixture(item, home, away, match_date, window_days=5):
            continue
        add_headline(item["headline"], default_source="The Guardian")

    for item in _fetch_espn_items():
        if not _item_matches_fixture(item, home, away, match_date, window_days=5):
            continue
        headline = item["headline"]
        if item.get("source"):
            headline = f"{headline} - {item['source']}"
        add_headline(headline, default_source="ESPN")

    return list(clears.values())


def should_replace_event(existing: dict, candidate: dict) -> bool:
    """Prefer curated supplements, then higher-priority media sources."""
    if candidate.get("source") == "curated":
        return True
    if existing.get("source") == "curated":
        return False
    cand_pri = _source_priority(str(candidate.get("source", "")))
    exist_pri = _source_priority(str(existing.get("source", "")))
    if cand_pri != exist_pri:
        return cand_pri > exist_pri
    return float(candidate.get("severity", 0)) > float(existing.get("severity", 0))