import logging
import json
from playwright.sync_api import sync_playwright
import azure.functions as func
import re
from azure.storage.blob import BlobClient
from azure.storage.fileshare import ShareFileClient
import os
import subprocess


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")
    x = json.loads(req.get_body())

    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)

    # Run the commands after your code
    ##subprocess.run(["pip", "install", "playwright"])
    subprocess.run(["playwright", "install", "chromium"])

    url_p = x["url"]
    epochs = x["levels"]
    share = x["share"]
    list_of_chars = [
        ">",
        "<",
        ":",
        "!",
        '"',
        "|",
        "\\",
        "?",
        "¿",
        "¡",
        "*",
        "/",
        " ",
        "ö",
        "ü",
        "’",
        ",",
    ]
    files = []
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
        file_title = re.sub(pattern, "", title)

        with open("{}.txt".format(file_title), "w", encoding="utf-8") as f:
            f.writelines(content)
        files.append("{}.txt".format(file_title))
        levels = []

        for link in links:
            page.goto(link)
            title_level = page.evaluate("() => document.title")
            content = page.evaluate(
                "const tags = document.getElementsByTagName('*');const text = [];for (const c of tags) {if(c.innerText){text.push(c.innerText.replace(/(\\r\\n|\\n|\\r|\\t)/gm, ''));}}uniq = [...new Set(text)];uniq;"
            )
            file_title_level = re.sub(pattern, "", title_level)
            dict = {
                "title": title_level,
                "content": "{}.txt".format(file_title_level),
                "url": link,
            }
            files.append("{}.txt".format(file_title_level))
            levels.append(dict)
            with open("{}.txt".format(file_title_level), "w", encoding="utf-8") as f:
                f.writelines(line + "\n" for line in content)
        browser.close()

        obj = {
            "title_main_page": title,
            "links": links,
            "content": "{}.txt".format(file_title),
            "levels": levels,
        }
        json_output = json.dumps(obj)

        with open(
            "output{}.json".format(file_title), "w", encoding="utf-8"
        ) as json_file:
            json_file.write(json_output)

        upload_blob("output{}.json".format(file_title))

        for file in files:
            upload_file_share(file, "scrape-kb-file-share-001/{}".format(share))

        return func.HttpResponse(json_output, mimetype="application/json")


def upload_blob(file):
    blob_client = BlobClient.from_connection_string(
        conn_str="DefaultEndpointsProtocol=https;AccountName=knowledgebasestksa;AccountKey=PncqrZlOUg+1ciAzWat8V4MzPUbIzi12jnEgiMdhs9QLananjm5AVaFQxYKFRpydjyBkNXLLU4yC+ASteDl8Mw==;EndpointSuffix=core.windows.net",
        container_name="scraping-kb",
        blob_name=file,
    )
    with open(file, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)


def upload_file_share(file, share):
    file_client = ShareFileClient.from_connection_string(
        conn_str="DefaultEndpointsProtocol=https;AccountName=knowledgebasestksa;AccountKey=PncqrZlOUg+1ciAzWat8V4MzPUbIzi12jnEgiMdhs9QLananjm5AVaFQxYKFRpydjyBkNXLLU4yC+ASteDl8Mw==;EndpointSuffix=core.windows.net",
        share_name=share,
        file_path=file,
    )
    with open(file, "rb") as source_file:
        file_client.upload_file(source_file)
