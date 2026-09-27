from googlesearch import search
import requests
from bs4 import BeautifulSoup
import openai
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from time import time

class SearchContext:
    def __init__(self, search_term: str, openai_key: str, num_results: int) -> None:
        self.search_term = search_term
        self.openai_key = openai_key
        self.num_results = num_results

def html_to_md(html: str) -> str:
    """
    convert html to LLM-readable markdown
    """
    soup = BeautifulSoup(html, "html.parser")

    # remove irrelevant tags
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        if not tag.decomposed: # avoid undefined behaviour of decomposed tags
            tag.decompose()
    
    text_parts = []

    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "p", "li"]):
        content = tag.get_text(strip=True)
        if content:
            # add to markdown
            if not hasattr(tag, "name"):
                continue
            if tag.name == None: # type: ignore pylance is stupid
                continue

            match tag.name: # type: ignore pylance is still stupid
                case "h1":
                    text_parts.append("# " + content)
                case "h2":
                    text_parts.append("## " + content)
                case "h3":
                    text_parts.append("### " + content)
                case "h4":
                    text_parts.append("#### " + content)
                case "h5":
                    text_parts.append("##### " + content)
                case "h6":
                    text_parts.append("###### " + content)
                case "li":
                    text_parts.append("- " + content)
                case _:
                    text_parts.append(content)
    
    formatted = "\n".join(text_parts)

    # remove double newlines
    while "\n\n" in formatted:
        formatted = formatted.replace("\n\n", "\n")
    
    return formatted

def scrape_url(url: str) -> dict:
    try:
        res = requests.get(str(url), timeout=5, headers={
            "Accept":"text/html,application/xhtml",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        })
        res.raise_for_status()
        md = html_to_md(res.text)
        return {"success": True, "url": str(url), "content": md}
    
    except requests.exceptions.Timeout:
        return {"success": False, "url": url, "error": "Request timed out."}
    except requests.exceptions.HTTPError as http_err:
        return {"success": False, "url": url, "error": f"HTTP error: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        return {"success": False, "url": url, "error": f"Request failed: {req_err}"}
    except Exception as e:
        return {"success": False, "url": url, "error": f"Unknown scrape error: {e}"}
    
def summarise_results(results: str, context: SearchContext) -> dict:
    openai.api_key = context.openai_key
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4.1-nano",
            messages=[
                {"role":"system", "content":f"Collate the content of these web pages (formatted in markdown) into a single informational piece. Make sure to keep all detail from all pages, the original search term was '{context.search_term}'. Include nummbers and statistics relevant to the search term."},
                {"role":"system", "content":results}
            ]
        ) # get response from gpt

        if not (hasattr(response, "choices") and type(response.choices) == list): # type: ignore shut up pylance it works blame openai library
            return {"success": False, "error": "Summary failed to generate"}

        summary = response.choices[0].message['content'] # type: ignore shut up pylance it works blame openai library
        return {"success": True, "summary": summary}
    except openai.error.RateLimitError as e: # type: ignore shut up pylance it works blame openai library
        return {"success": False, "error": "Summary AI rate limited. Try again later."}
    except openai.error.InvalidRequestError as e: # type: ignore shut up pylance it works blame openai library, if this runs it means too many tokens
        return {"success": False, "error": "Token length of results too long for summary AI model"}

def search_web(context: SearchContext) -> str:
    t1 = time()
    links = list(search(context.search_term, region="gb", num_results=context.num_results))
    pages_content: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(scrape_url, str(url)) for url in links]
        for future in as_completed(futures):
            result = future.result()
            url: str = result["url"]
            pages_content[url] = result
    
    pages_format_for_gpt = ""
    
    for url, result in pages_content.items():
        if result["success"]:
            pages_format_for_gpt += f"===START OF PAGE '{url}'===\n\n"
            pages_format_for_gpt += result["content"]
            pages_format_for_gpt += f"\n\n===END OF PAGE===\n"
        else:
            pages_format_for_gpt += f"===PAGE '{url}' RETURNED ERROR '{result["error"]}'==="
    
    gpt_summary = summarise_results(pages_format_for_gpt, context)

    t2 = time()

    gpt_summary["time_taken"] = f"time taken: {t2 - t1}s"

    return json.dumps(gpt_summary)

    