import logging
import json
from playwright.sync_api import sync_playwright
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")
    x = json.loads(req.get_body())
    url_p = x["Goto"]
    epochs = x["Epochs"]
    if epochs > 3:
        epochs = 3
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()
        url = url_p
        page.goto(url)
        title = page.evaluate("() => document.title")
        links = page.evaluate(
            "var links = [];const refs = document.getElementsByTagName('a');for (const c of refs) {links.push(c.href);} uniq = [...new Set(links)]; uniq;"
        )
        content = page.evaluate(
            "const tags = document.getElementsByTagName('*');const text = [];for (const c of tags) {if(c.innerText){text.push(c.innerText.replace(/(\\r\\n|\\n|\\r|\\t)/gm, ''));}}uniq = [...new Set(text)];uniq;"
        )
        obj = {"title": title, "links": links, "content": content}
        for link in links:
            page.goto(link)
            title_level = page.evaluate("() => document.title")
            links_level = page.evaluate(
                "var links = [];const refs = document.getElementsByTagName('a');for (const c of refs) {links.push(c.href);} uniq = [...new Set(links)]; uniq;"
            )
            content = page.evaluate(
                "const tags = document.getElementsByTagName('*');const text = [];for (const c of tags) {if(c.innerText){text.push(c.innerText.replace(/(\\r\\n|\\n|\\r|\\t)/gm, ''));}}uniq = [...new Set(text)];uniq;"
            )
        browser.close()

        return func.HttpResponse(json.dumps(obj), mimetype="application/json")
