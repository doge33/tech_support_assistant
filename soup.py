#using beautiful soup to scan for Content Hub documentation
from bs4 import BeautifulSoup
import requests
from pathlib import Path
from markdownify import markdownify

def download_site(url):
    """use requests to download documentation sites"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)

    # print("Status:", response.status_code)
    # print("Final URL:", response.url)
    # print("Contains main-content:", "main-content" in response.text)

    # # Save the downloaded HTML for inspection
    # Path("downloaded-page.html").write_bytes(response.content)


    soup = BeautifulSoup(response.content, "html.parser" )
    title = soup.title.string if soup.title else "No title found"
    #links = soup.find_all("a") 
    article = soup.select_one("#main-content .article-layout section")

    if article is None:
        raise ValueError("Could not find the article container")

    for irrelevant in article(["script", "style", "img", "input"]):
        irrelevant.decompose()

    text = markdownify(str(article), heading_style="ATX")

    return title,text


def write_to_md(url, title, text):
    output_dir = Path("knowledge-base")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir/f"{title}.md"
    output_file.write_text(
        f"Source: {url}\n\n{text}",
        encoding="utf-8",
    )


if __name__== "__main__":

    urls = Path("urls.txt").read_text(encoding="utf-8").splitlines()

    for index, url in enumerate(urls):
        url = url.strip()
        title, text = download_site(url)
        write_to_md(url, title, text)
        print(f"{index+1}: {title}.md saved to knowledge base")




    