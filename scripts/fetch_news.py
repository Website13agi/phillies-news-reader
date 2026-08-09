import json
import hashlib
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path


# ==========================================
# フィリーズ関連ニュースのRSS
# ==========================================

FEEDS = [
    (
        "Phillies Nation",
        "https://philliesnation.com/feed/"
    ),
    (
        "MLB.com Phillies",
        "https://www.mlb.com/phillies/feeds/news/rss.xml"
    ),
    (
        "Phuture Phillies",
        "https://phuturephillies.com/feed/"
    ),
    (
        "The Good Phight",
        "https://www.thegoodphight.com/rss/current"
    ),
]


# ==========================================
# フィリーズ関連キーワード
# ==========================================

PHILLIES_KEYWORDS = [

    # 球団
    "phillies",
    "philadelphia phillies",
    "philadelphia",
    "phils",

    # MLB関連表現
    "citizens bank park",

    # よく登場する球団関係者・選手
    "rob thomson",
    "john middleton",
    "dave dombrowski",

    # チーム関連
    "phillies rotation",
    "phillies bullpen",
    "phillies lineup",
    "phillies roster",
    "phillies prospect",
    "phillies prospects",
    "phillies farm",
    "phillies minor league",
    "phillies minors",
    "phillies draft",
    "phillies trade",
    "phillies free agency",

]


# ==========================================
# RSS取得
# ==========================================

USER_AGENT = (
    "Mozilla/5.0 "
    "PhilliesNewsReader/1.0"
)


def fetch(url):

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=20
    ) as response:

        return response.read()


# ==========================================
# 日付
# ==========================================

def parse_date(value):

    if not value:

        return datetime.now(
            timezone.utc
        ).isoformat()

    try:

        return (
            parsedate_to_datetime(
                value
            )
            .astimezone(
                timezone.utc
            )
            .isoformat()
        )

    except Exception:

        return value


# ==========================================
# 文字列
# ==========================================

def clean(value):

    if not value:

        return ""

    return re.sub(
        r"\s+",
        " ",
        value
    ).strip()


# ==========================================
# XMLから文字列を取得
# ==========================================

def get_text(element, names):

    for name in names:

        child = element.find(
            name
        )

        if (
            child is not None
            and child.text
        ):

            return clean(
                child.text
            )

    return ""


# ==========================================
# フィリーズ関連記事判定
# ==========================================

def is_phillies_article(
    title,
    description=""
):

    text = (
        title + " " + description
    ).lower()

    for keyword in PHILLIES_KEYWORDS:

        if keyword.lower() in text:

            return True

    return False


# ==========================================
# RSS解析
# ==========================================

def parse_feed(
    xml_data,
    source
):

    root = ET.fromstring(
        xml_data
    )

    items = root.findall(
        ".//item"
    )

    articles = []

    for item in items:

        title = get_text(
            item,
            ["title"]
        )

        link = get_text(
            item,
            ["link"]
        )

        guid = get_text(
            item,
            ["guid"]
        )

        published = get_text(
            item,
            [
                "pubDate",
                "published",
                "updated"
            ]
        )

        description = get_text(
            item,
            [
                "description",
                "summary"
            ]
        )

        if not title or not link:

            continue


        # ----------------------------------
        # フィリーズ関連か判定
        # ----------------------------------

        if not is_phillies_article(
            title,
            description
        ):

            continue


        # ----------------------------------
        # ID
        # ----------------------------------

        raw_id = (
            guid
            or link
            or title
        )

        article_id = hashlib.sha1(
            raw_id.encode("utf-8")
        ).hexdigest()


        articles.append({

            "id": article_id,

            "title": title,

            "url": link,

            "published": parse_date(
                published
            ),

            "source": source

        })


    return articles


# ==========================================
# メイン
# ==========================================

all_articles = []


for source, feed_url in FEEDS:

    try:

        data = fetch(
            feed_url
        )

        articles = parse_feed(
            data,
            source
        )

        all_articles.extend(
            articles
        )

        print(
            "OK:",
            source,
            len(articles)
        )

    except Exception as error:

        print(
            "ERROR:",
            source,
            error
        )


# ==========================================
# 重複削除
# ==========================================

unique = {}

for article in all_articles:

    unique[
        article["id"]
    ] = article


articles = list(
    unique.values()
)


# ==========================================
# 新しい順
# ==========================================

articles.sort(
    key=lambda article:
        article.get(
            "published",
            ""
        ),
    reverse=True
)


# ==========================================
# 最大500件
# ==========================================

articles = articles[:500]


# ==========================================
# 保存
# ==========================================

output = Path(
    "data/articles.json"
)

output.parent.mkdir(
    parents=True,
    exist_ok=True
)

output.write_text(
    json.dumps(
        articles,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)


print(
    "Saved:",
    len(articles),
    "articles"
)
