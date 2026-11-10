import requests
from bs4 import BeautifulSoup
import re


def search_google(query):

    results = []

    url = f"https://www.google.com/search?q={query}"

    headers = {
        "User-Agent":
        "Mozilla/5.0"
    }


    response = requests.get(
        url,
        headers=headers
    )


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    links = soup.find_all(
        "a"
    )


    for link in links:

        href = link.get("href")


        if href and href.startswith("http"):

            results.append(
                href
            )


    return results[:10]





def extract_email(text):

    emails = re.findall(

        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",

        text

    )


    if emails:

        return emails[0]


    return None