# 福生无量天尊
from openai import OpenAI
import feedparser
import requests
from newspaper import Article
from datetime import datetime
import time
import pytz
import os

# --- Получение API-ключа DeepSeek (нужен только для инициализации клиента, но мы не будем его использовать) ---
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not set in environment variables")

# Инициализация клиента (он не будет вызываться, но нужен для совместимости)
openai_client = OpenAI(api_key=openai_api_key, base_url="https://api.deepseek.com/v1")

# --- Получение ключей Server酱 (если есть) ---
server_chan_keys_env = os.getenv("SERVER_CHAN_KEYS")
if server_chan_keys_env:
    server_chan_keys = server_chan_keys_env.split(",")
else:
    server_chan_keys = []   # пустой список, если ключа нет

# --- RSS-источники (можно редактировать) ---
rss_feeds = {
    " 华尔街见闻":{
        "华尔街见闻":"https://dedicated.wallstreetcn.com/rss.xml",
    },
    " 36氪":{
        "36氪":"https://36kr.com/feed",
    },
    " 中国经济": {
        "香港經濟日報":"https://www.hket.com/rss/china",
        "东方财富":"http://rss.eastmoney.com/rss_partener.xml",
        "百度股票焦点":"http://news.baidu.com/n?cmd=1&class=stock&tn=rss&sub=0",
        "中新网":"https://www.chinanews.com.cn/rss/finance.xml",
        "国家统计局-最新发布":"https://www.stats.gov.cn/sj/zxfb/rss.xml",
    },
    " 美国经济": {
        "华尔街日报 - 经济":"https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness",
        "华尔街日报 - 市场":"https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
        "MarketWatch美股": "https://www.marketwatch.com/rss/topstories",
        "ZeroHedge华尔街新闻": "https://feeds.feedburner.com/zerohedge/feed",
        "ETF Trends": "https://www.etftrends.com/feed/",
    },
    " 世界经济": {
        "华尔街日报 - 经济":"https://feeds.content.dowjones.io/public/rss/socialeconomyfeed",
        "BBC全球经济": "http://feeds.bbci.co.uk/news/business/rss.xml",
    },
}

# --- Вспомогательные функции ---
def today_date():
    return datetime.now(pytz.timezone("Asia/Shanghai")).date()

def fetch_article_text(url):
    try:
        print(f" 正在爬取文章内容: {url}")
        article = Article(url)
        article.download()
        article.parse()
        text = article.text[:1500]
        if not text:
            print(f"⚠️ 文章内容为空: {url}")
        return text
    except Exception as e:
        print(f"❌ 文章爬取失败: {url}，错误: {e}")
        return "（未能获取文章正文）"

def fetch_feed_with_headers(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    return feedparser.parse(url, request_headers=headers)

def fetch_feed_with_retry(url, retries=3, delay=5):
    for i in range(retries):
        try:
            feed = fetch_feed_with_headers(url)
            if feed and hasattr(feed, 'entries') and len(feed.entries) > 0:
                return feed
        except Exception as e:
            print(f"⚠️ 第 {i+1} 次请求 {url} 失败: {e}")
            time.sleep(delay)
    print(f"❌ 跳过 {url}, 尝试 {retries} 次后仍失败。")
    return None

def fetch_rss_articles(rss_feeds, max_articles=10):
    news_data = {}
    analysis_text = ""
    for category, sources in rss_feeds.items():
        category_content = ""
        for source, url in sources.items():
            print(f" 正在获取 {source} 的 RSS 源: {url}")
            feed = fetch_feed_with_retry(url)
            if not feed:
                print(f"⚠️ 无法获取 {source} 的 RSS 数据")
                continue
            print(f"✅ {source} RSS 获取成功，共 {len(feed.entries)} 条新闻")
            articles = []
            for entry in feed.entries[:5]:
                title = entry.get('title', '无标题')
                link = entry.get('link', '') or entry.get('guid', '')
                if not link:
                    print(f"⚠️ {source} 的新闻 '{title}' 没有链接，跳过")
                    continue
                article_text = fetch_article_text(link)
                analysis_text += f"〖{title}〗\n{article_text}\n\n"
                print(f" {source} - {title} 获取成功")
                articles.append(f"- [{title}]({link})")
            if articles:
                category_content += f"### {source}\n" + "\n".join(articles) + "\n\n"
        news_data[category] = category_content
    return news_data, analysis_text

# --- Функция отправки уведомлений (безопасная) ---
def send_to_wechat(title, content):
    if not server_chan_keys:
        print("ℹ️ Server酱 ключи не заданы, пропускаем отправку.")
        return
    for key in server_chan_keys:
        url = f"https://sctapi.ftqq.com/{key}.send"
        data = {"title": title, "desp": content}
        try:
            response = requests.post(url, data=data, timeout=10)
            if response.ok:
                print(f"✅ 推送成功: {key}")
            else:
                print(f"❌ 推送失败: {key}, 响应：{response.text}")
        except Exception as e:
            print(f"❌ 推送异常: {key}, 错误: {e}")

# --- Основной блок ---
if __name__ == "__main__":
    today_str = today_date().strftime("%Y-%m-%d")
    articles_data, analysis_text = fetch_rss_articles(rss_feeds, max_articles=5)
    
    # Вместо AI-анализа вставляем заглушку
    summary = "（AI分析已跳过，仅显示新闻标题）"
    
    final_summary = f"**{today_str} 财经新闻摘要**\n\n✍️ **今日分析总结：**\n{summary}\n\n---\n\n"
    for category, content in articles_data.items():
        if content.strip():
            final_summary += f"## {category}\n{content}\n\n"
    
    # Отправка (если ключи есть)
    send_to_wechat(title=f"{today_str} 财经新闻摘要", content=final_summary)
    
    # Также выводим в консоль для просмотра в логах
    print("\n" + "="*50)
    print("ДАЙДЖЕСТ НОВОСТЕЙ (вывод в логи):")
    print(final_summary)
    print("="*50)
