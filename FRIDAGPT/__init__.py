import logging
import json
from playwright.sync_api import sync_playwright
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        url = "https://tigyog.app/d/H7XOvXvC_x/r/goedel-s-first-incompleteness-theorem"
        page.goto(url)

        title = page.evaluate("() => document.title")
        links = page.evaluate(
            "var links = [];const refs = document.getElementsByTagName('a');for (const c of refs) {links.push(c.href);} uniq = [...new Set(links)]; uniq;"
        )
        content = page.evaluate(
            "const tags = document.getElementsByTagName('*');const text = [];for (const c of tags) {if(c.innerText){text.push(c.innerText.replace(/(\\r\\n|\\n|\\r)/gm, ''));}}uniq = [...new Set(text)];uniq;"
        )
        obj = {"title": title, "links": links, "content": content}

        browser.close()

        return func.HttpResponse(json.dumps(obj), mimetype="application/json")
