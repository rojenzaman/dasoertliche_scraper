#!/usr/bin/env python3

import json
import requests
from time import sleep

from fake_useragent import UserAgent
import lxml.html


def parse_details(content):
    doc = lxml.html.fromstring(content)
    contact = doc.xpath('//div[@class="lnks"]')

    mail = contact[0].xpath('./a[@class="mail"]')
    web = contact[0].xpath('./a[@class="www"]')

    contact_data = {}

    for m in mail:
        if len(m.xpath('./@title')) > 0:
            contact_data['mailAddress'] = m.xpath('./@title')[0]
            break

    for w in web:
        if len(w.xpath('./@title')) > 0:
            contact_data['website'] = w.xpath('./@title')[0]
            break

    if 'mailAddress' not in contact_data:
        contact_data['mailAddress'] = ''

    if 'website' not in contact_data:
        contact_data['website'] = ''

    print(contact_data)
    return contact_data


def parse_listings(content):
    doc = lxml.html.fromstring(content)
    d = doc.xpath('//script[@type="application/ld+json"]/text()')
    j = json.loads(d[0])

    return j['@graph']


def parse_hits(content):
    doc = lxml.html.fromstring(content)
    h = doc.xpath('//span[@class="sttrefferanz"]/text()')

    return int(h[0])


def parse_iteration(content):
    doc = lxml.html.fromstring(content)
    n = doc.xpath('//a[@title="zur nächsten Seite"]/@href')

    if len(n) > 0:
        url = n[0]
    else:
        url = None

    return url


def download_site(url, headers):
    try:
        r = requests.get(url, headers=headers, cookies={'CONSENT': 'YES+'})

        return r.content
    except Exception as e:
        print(e)


def main():
    ua = UserAgent()
    headers = { 'User-Agent': ua.random }

    results = []

    url = 'https://www.dasoertliche.de/Themen/Hausverwaltungen/Hamburg.html'
    site_listings = download_site(url, headers)
    total_hists = parse_hits(site_listings)

    while True:
        listings = parse_listings(site_listings)

        for item in listings:
            site_details = download_site(item['url'], headers)
            details = parse_details(site_details)

            item.pop('url')
            item.pop('@type')
            item['geo'].pop('@type')
            item['address'].pop('@type')

            item.pop('aggregateRating') if 'aggregateRating' in item else item

            item['geo']['latitude'] = float(item['geo']['latitude'])
            item['geo']['longitude'] = float(item['geo']['longitude'])

            item['telephone'] = item['telephone'].replace(' ', '')

            results.append({**item, **details})

            sleep(1)


        with open('query_results_new02.json', 'a', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False)

        url = parse_iteration(site_listings)

        if len(results) <= total_hists and url is not None:
            site_listings = download_site(url, headers)
        else:
            break


if __name__ == '__main__':
    main()
