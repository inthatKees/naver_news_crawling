# -*- coding: utf-8 -*-
"""
네이버 뉴스 검색시 리스트 크롤링하는 프로그램 (_select 사용)
- 크롤링 해오는 것 : 링크, 제목, 신문사, 날짜, 본문
- 날짜, 본문 -> 정제 작업 필요
- 리스트 -> 딕셔너리 -> df -> CSV로 저장
"""
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
import os
import urllib.parse
import time
import random
import argparse
from typing import List, Tuple

# Output path setup (can be overridden via CLI)
RESULT_PATH = "out/"
os.makedirs(RESULT_PATH, exist_ok=True)


# Helper: cleansing functions
def date_cleansing(text):
    try:
        pattern = r"\d+\.(\d+)\.(\d+)\."
        r = re.compile(pattern)
        match = r.search(text).group(0)
        return match
    except Exception:
        pattern = r"\w* (\d\w*)"
        r = re.compile(pattern)
        m = r.search(text)
        return m.group(1) if m else text


def contents_cleansing(contents_html):
    first = re.sub(r"<dl>.*?</a> </div> </dd> <dd>", "", str(contents_html)).strip()
    second = re.sub(r'<ul class="relation_lst">.*?</dd>', "", first).strip()
    third = re.sub(r"<.+?>", "", second).strip()
    return third


def build_url(page_start: int, query: str, s_date: str, e_date: str, s_from: str, e_to: str) -> str:
    return (
        "https://search.naver.com/search.naver?ssc=tab.news.all&query="
        + query
        + "&sm=tab_opt&sort=1&photo=3&field=0&pd=3&ds="
        + s_date
        + "&de="
        + e_date
        + "&docid=&related=0&mynews=0&office_type=0&office_section_code=0&news_office_checked="
        + "&nso=so%3Ar%2Cp%3Afrom"
        + s_from
        + "to"
        + e_to
        + "&is_sug_officeid=0&office_category=0&service_area=0&start="
        + str(page_start)
    )


# Fetch a single page and save raw HTML
def fetch_and_save(url: str) -> str:
    # url = build_url(page_start, query, s_date, e_date, s_from, e_to)
    print("GET", url)
    time.sleep(0.2)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive'
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print("status", r.status_code)
        if r.status_code == 403:
            print("Received 403 Forbidden. Retrying after 5 seconds...")
            time.sleep(5)
            r = requests.get(url, headers=headers, timeout=10)
            print("status", r.status_code)
        html = r.text
    except Exception:
        html = 'NaN'
    # print(r)
    # Save raw for inspection
    # raw_path = os.path.join(RESULT_PATH, f'{s_from}-{e_to}_{page_start}.html')
    # with open(raw_path, 'w', encoding='utf-8') as f:
    #     f.write(html)
    return html

# Parse HTML and select news items using updated selectors
import re

NAVER_NEWS_LINK = re.compile(r"^https?://(?:n\.)?news\.naver\.com/")

def parse_news_items(html: str):
    soup = BeautifulSoup(html, "html.parser")
    # Find all headline anchors that look like Naver news articles
    headline_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].split("?", 1)[0]
        if NAVER_NEWS_LINK.match(href):
            # Title text is usually in the anchor text
            title_text = a.get_text(strip=True)
            if title_text:
                headline_links.append((a, href, title_text))
    # De-duplicate by href to avoid repeated anchors in the same card
    seen = set()
    unique_items = []
    for a, href, title in headline_links:
        if href in seen:
            continue
        seen.add(href)
        unique_items.append({"anchor": a, "href": href, "title": title})
    return unique_items


def extract_article_content(news_url: str) -> str:
    """Return the article text inside element with classes 'newsct_article _article_body'.

    If the element is not found, return an empty string.
    """
    html = fetch_and_save(news_url)

    soup = BeautifulSoup(html, "html.parser")
    node = soup.select_one("div.newsct_article._article_body")
    if not node:
        return ""

    return node.get_text(separator=" ", strip=True)

# Extract fields from a single item
def extract_from_item(item):
    title = link = source = date = content = ''

    # extract title # 
    t = item.select_one('span.sds-comps-text-type-headline1')
    if t:
        title = t.get_text(strip=True)
        link = t.get('href', '')
    
    # extract source
    s = item.select_one('span.sds-comps-profile-info-title-text a')
    if s:
        source = s.get_text(strip=True)

    # extract date 
    d_list = item.select('span.sds-comps-profile-info-subtext .sds-comps-text')
    d = d_list[1] if len(d_list) > 1 else (d_list[0] if d_list else None)
    if d:
        date = d.get_text(strip=True)

    # c = item.select_one('span.sds-comps-text-type-body1')
    # if c:
    #     content = c.get_text(strip=True)

    # extract href from a tag
    news_url = ''
    u = item.select_one('a.DJwZySR1gWTQoLm3xvvD')
    if u:
        news_url = u.get('href', '').split('?', 1)[0]
        content = extract_article_content(news_url)

    # Given the news url, parse 

    return {
        'title': title,
        'link': news_url,
        'source': source,
        'date': date,
        'contents': content
    }


def crawler(maxpage, query, sort, s_date, e_date):
    """
    Crawls multiple pages of news articles and accumulates results.

    Args:
        maxpage (int or str): Number of pages to crawl (10 results per page).
        query (str): Search query.
        sort (str): Sort order (0: relevance, 1: latest, 2: oldest).
        s_date (str): Start date in "YYYY.MM.DD" format.
        e_date (str): End date in "YYYY.MM.DD" format.

    Returns:
        str: Path to the saved CSV file.
    """
    # TODO: sort option implementation
    data_rows = []
    page_start = 1
    maxpage_t = (int(maxpage) - 1) * 10 + 1
    
    # Calculate s_from and e_to for this query
    s_from = s_date.replace(".", "")
    e_to = e_date.replace(".", "")

    while page_start <= maxpage_t:
        url = build_url(page_start, query, s_date, e_date, s_from, e_to)
        html = fetch_and_save(url)
        items = parse_news_items(html)
        # print(items)
        for it in items:
            row = extract_from_item(it)
            data_rows.append(row)
        print('accumulated rows:', len(data_rows))
        page_start += 10

        # break if there are no more articles
        if len(items) == 0:
            break
        
        time.sleep(random.uniform(2, 5))
    # Build DataFrame and export to CSV
    df = pd.DataFrame(data_rows, columns=['date', 'title', 'source', 'contents', 'link'])
    print(df.shape)

    # Use "YYQnumber" format for output file name
    # Extract year and month from s_date to determine quarter
    year_short = s_date[2:4]
    month = int(s_date[5:7])
    if 1 <= month <= 3:
        quarter = 1
    elif 4 <= month <= 6:
        quarter = 2
    elif 7 <= month <= 9:
        quarter = 3
    else:
        quarter = 4
    # Use decoded query (keyword) for filename readability
    try:
        decoded_query = urllib.parse.unquote(query)
    except Exception:
        decoded_query = query
    outputFileName = f"{year_short}Q{quarter}_{decoded_query}.csv"
    output_path = os.path.join(RESULT_PATH, outputFileName)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    return output_path


# Helper to get start/end date for a given year and quarter
def get_quarter_dates(year: int, quarter: int) -> Tuple[str, str]:
    if quarter == 1:
        return f"{year}.01.01", f"{year}.03.31"
    elif quarter == 2:
        return f"{year}.04.01", f"{year}.06.30"
    elif quarter == 3:
        return f"{year}.07.01", f"{year}.09.30"
    elif quarter == 4:
        return f"{year}.10.01", f"{year}.12.31"
    else:
        raise ValueError("Quarter must be 1-4")


def parse_keywords_arg(keywords_arg: List[str]) -> List[str]:
    """Normalize keywords from CLI. Supports multiple --keyword flags or comma-separated list.
    """
    normalized: List[str] = []
    for part in keywords_arg:
        if not part:
            continue
        # split by comma and strip spaces/quotes
        splits = [p.strip().strip('"').strip("'") for p in part.split(',')]
        for s in splits:
            if s:
                normalized.append(s)
    # de-duplicate while preserving order
    seen = set()
    uniq: List[str] = []
    for k in normalized:
        if k not in seen:
            uniq.append(k)
            seen.add(k)
    return uniq


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Naver News Crawler (generalized CLI)")
    parser.add_argument("--keywords", "--keyword", dest="keywords", nargs='+', required=True,
                        help="검색 키워드(들). 공백으로 여러 개 지정하거나, 쉼표로 나열 가능")
    parser.add_argument("--maxpage", type=int, default=200, help="페이지 수(페이지당 10건). 기본 200")
    # parser.add_argument("--sort", type=str, choices=["0", "1", "2"], default="1",
    #                     help="정렬: 0=관련성, 1=최신순(기본), 2=오래된순")

    # 기간은 두 가지 방식 중 하나 선택: (시작/종료일) 또는 (연도/분기)
    parser.add_argument("--start-date", type=str, help="시작일 YYYY.MM.DD 형식")
    parser.add_argument("--end-date", type=str, help="종료일 YYYY.MM.DD 형식")
    parser.add_argument("--year", type=int, help="연도 (예: 2024)")
    parser.add_argument("--quarter", type=int, choices=[1, 2, 3, 4], help="분기 (1-4)")

    parser.add_argument("--result-path", type=str, default=RESULT_PATH,
                        help="결과 CSV 저장 경로 (기본: out/naver_news_crawling_result/)")
    parser.add_argument("--sleep-between", type=float, default=5.0,
                        help="키워드 간 대기(초). 기본 5초")

    args = parser.parse_args()

    # Override global RESULT_PATH if provided
    if args.result_path:
        RESULT_PATH = args.result_path
        os.makedirs(RESULT_PATH, exist_ok=True)

    # Validate date/quarter selection
    if args.start_date and args.end_date:
        periods: List[Tuple[str, str]] = [(args.start_date, args.end_date)]
    elif args.year and args.quarter:
        s_date, e_date = get_quarter_dates(args.year, args.quarter)
        periods = [(s_date, e_date)]
    else:
        raise SystemExit("기간을 지정하세요: --start-date/--end-date 또는 --year/--quarter 중 하나")

    # Normalize keywords
    keywords: List[str] = parse_keywords_arg(args.keywords)
    if not keywords:
        raise SystemExit("키워드를 하나 이상 지정하세요 (--keywords)")

    for (s_date, e_date) in periods:
        print(f"\n{'#'*60}")
        print(f"Processing: {s_date} ~ {e_date}")
        print(f"{'#'*60}")
        for keyword in keywords:
            print(f"\n{'='*50}")
            print(f"Processing keyword: {keyword}")
            print(f"{'='*50}")

            # Build query as-is from the keyword for general use
            query = urllib.parse.quote(f"{keyword}")
            print(f"Encoded query: {query}")

            result_path = crawler(args.maxpage, query, args.sort, s_date, e_date)
            print(f"Results saved to: {result_path}")
            time.sleep(max(0.0, args.sleep_between))
