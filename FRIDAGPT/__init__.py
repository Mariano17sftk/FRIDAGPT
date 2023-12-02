import logging
import json
from playwright.sync_api import sync_playwright
import azure.functions as func
import re 
import os
import subprocess
from firebase_admin import credentials, initialize_app, storage

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")
    x = json.loads(req.get_body())
    url_p = x["url"]
    epochs = x["levels"]
    share = x["document_id"]
    sess_id = x["session_id"]
    doc_name = x["document_name"]

    route = "{}/Scrapes/{}".format(sess_id,doc_name)
    cred = credentials.Certificate("fridagpt-bb68d-firebase-adminsdk-76f8x-dedd049a45.json")
    initialize_app(cred, {'storageBucket' : 'fridagpt-bb68d.appspot.com'})

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
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True, slow_mo=50)
        page = browser.new_page()
        url = url_p
        page.goto(url)
        title = page.evaluate("() => document.title")
        links = page.evaluate(
            "var links = [];const refs = document.getElementsByTagName('a');const regex = new RegExp('^(http|https):\/\/.+');for (const c of refs) {if(regex.test(c.href)){links.push(c.href);}} uniq = [...new Set(links)]; uniq.shift(); uniq;"
        )
        content = page.evaluate(
            "var el = document.body; var text = el.innerText || el.textContent; var tt = text; tt;"
        )
        title_encoded = str(title.encode('utf-8', 'strict'), encoding='utf-8')
        file_title = re.sub(pattern, "", title_encoded)
        firebase(str(content),"{}.txt".format(file_title),route)
        levels = []
        if epochs > 1:
            for link in links:
                try: 
                    page.goto(link)
                    title_level = page.evaluate("() => document.title")
                    content = page.evaluate(
                        "var el = document.body; var text = el.innerText || el.textContent; var tt = text; tt;"
                    )
                    title_encoded = title_level.encode('utf-8', 'strict')
                    file_title_level = re.sub(pattern, "", str(title_encoded, encoding='utf-8'))
                    dict = {
                        "title": title_level,
                        "content": "{}/{}.txt".format(route, file_title_level),
                        "url": link,
                    }
                    levels.append(dict)
                    firebase(str(content),"{}.txt".format(file_title_level),route)
                except:
                    continue
        browser.close()

        obj = {
            "webpage" : {
                "title_main_page": title,
                "levels": levels,
                "content": "{}/{}.txt".format(route, file_title),
            },
            "session_id" : sess_id,
            "document_id" : share,
            "document_name" : doc_name
        }
    
        return func.HttpResponse(json.dumps(obj), mimetype="application/json")


def firebase(data,file,dir): 
    fileName = file
    bucket = storage.bucket()
    blob = bucket.blob("{}/{}".format(dir,fileName))
    blob.upload_from_string(data)
    blob.make_public()

