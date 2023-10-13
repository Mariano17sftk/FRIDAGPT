import logging
import json
from playwright.sync_api import sync_playwright
import azure.functions as func
import re


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")
    x = json.loads(req.get_body())
    url_p = x["Goto"]
    epochs = x["Epochs"]
    list_of_chars = [">", "<", ":", "!", '"', "|", "\\", "?", "¿", "¡", "*", "/"]
    pattern = "[" + "".join(list_of_chars) + "]"
    if epochs > 3:
        epochs = 3
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()
        url = url_p
        page.goto(url)
        title = page.evaluate("() => document.title")
        links = page.evaluate(
            "var links = [];const refs = document.getElementsByTagName('a');const regex = new RegExp('^(http|https):\/\/.+');for (const c of refs) {if(regex.test(c.href)){links.push(c.href);}} uniq = [...new Set(links)]; uniq.shift(); uniq;"
        )
        content = page.evaluate(
            "const tags = document.getElementsByTagName('*');const text = [];for (const c of tags) {if(c.innerText){text.push(c.innerText.replace(/(\\r\\n|\\n|\\r|\\t)/gm, ''));}}uniq = [...new Set(text)];uniq;"
        )
        obj = {"title_main_page": title, "links": links, "content": "{title}.txt"}
        file_title = re.sub(pattern, "", title)
        with open("{}.txt".format(file_title), "w", encoding="utf-8") as f:
            f.writelines(content)

        for link in links:
            page.goto(link)
            title_level = page.evaluate("() => document.title")
            content = page.evaluate(
                "const tags = document.getElementsByTagName('*');const text = [];for (const c of tags) {if(c.innerText){text.push(c.innerText.replace(/(\\r\\n|\\n|\\r|\\t)/gm, ''));}}uniq = [...new Set(text)];uniq;"
            )
            obj.update({"title": title_level, "content": "{title_level}.txt"})
            file_title_level = re.sub(pattern, "", title_level)
            with open("{}.txt".format(file_title_level), "w", encoding="utf-8") as f:
                f.writelines(content)
        browser.close()

        return func.HttpResponse(json.dumps(obj), mimetype="application/json")
