#!/usr/bin/env python3

import re
import json
import httpx
import click

from lxml import html
from pathlib import Path
from fake_useragent import UserAgent
from time import sleep

EMAIL_REGEX = re.compile(r'[^@]+@[^@]+\.[^@]+')



def parse_entry_details(content):
    contact_data = {}
    contact_data['website'] = ''
    contact_data['mailAddress'] = ''

    doc = html.fromstring(content)
    contact = doc.xpath('//div[@class="lnks"]')

    if len(contact) == 0:
        return contact_data

    mail = contact[0].xpath('./a[@class="mail"]')
    web = contact[0].xpath('./a[@class="www"]')

    for m in mail:
        if len(m.xpath('./@title')) > 0:
            mail_address = m.xpath('./@title')[0].lower()

            if not EMAIL_REGEX.fullmatch(mail_address):
                continue

            contact_data['mailAddress'] = mail_address

            break

    for w in web:
        if len(w.xpath('./@title')) > 0:
            contact_data['website'] = w.xpath('./@title')[0].lower()

            break

    return contact_data


def parse_entries(content):
    doc = html.fromstring(content)
    d = doc.xpath('//script[@type="application/ld+json"]/text()')

    if len(d) == 0:
        return None

    j = json.loads(d[0])

    return j['@graph']


def parse_hits(content):
    doc = lxml.html.fromstring(content)
    h = doc.xpath('//span[@class="sttrefferanz"]/text()')

    if len(h) > 0:
        l = int(h[0])
    else:
        l = 0

    return l


def parse_next_url(content):
    doc = html.fromstring(content)
    n = doc.xpath('//a[@title="zur nächsten Seite"]/@href')

    if len(n) > 0:
        url = n[0]
    else:
        url = None

    return url


def download_document(url, headers):
    try:
        r = httpx.get(url, headers=headers, cookies={'CONSENT': 'YES+'})

        return r.content
    except ConnectionError as e:
        sleep(15)
        download_document(url, headers)
    except Exception as e:
        print(e)
        return None


def write_json(entry, file_name):
    try:
        with open(file_name, 'r+', encoding='utf-8') as f:
            d = json.load(f)

            d['entries'].append(entry)
            f.seek(0)

            json.dump(d, f, ensure_ascii=False)
    except FileNotFoundError as e:
        d = {
            'entries': [entry]
        }

        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False)


def make_file_name(query, postal_code):
    directory_path = Path.cwd() / 'data'
    directory_path.mkdir(parents=True, exist_ok=True)

    if postal_code:
        file_name = '{}_{}'.format(query.lower(), postal_code)
    else:
        file_name = '{}'.format(query.lower())

    return f'data/{file_name}.json'


def parse_entry(item):
    item.pop('aggregateRating') if 'aggregateRating' in item else item

    item['coordinates'] = []

    if 'geo' in item:
        item['coordinates'].append(float(item['geo']['latitude']))
        item['coordinates'].append(float(item['geo']['longitude']))

    try:
        listing_postal_code = f'{item["address"]["postalCode"]:05d}'
        item['address']['postalCode'] = listing_postal_code
    except:
        pass

    try:
        item['telephone'] = item['telephone'].replace(' ', '')
    except:
        pass

    item.pop('url')
    item.pop('@type')
    item['address'].pop('@type')

    if 'geo' in item:
        item.pop('geo')

    return item


def aggregate(query, offset, postal_code):
    file_name = make_file_name(query, postal_code)

    ua = UserAgent()
    headers = { 'User-Agent': ua.random }

    param = 'kw={}&form_name=search_nat'.format(query)
    url = 'https://www.dasoertliche.de?{}'.format(param)

    if offset:
        url = '{}&recFrom={}'.format(url, offset)

    if postal_code:
        url = '{}&ci={}'.format(url, postal_code)

    while True:
        print('Next url {}\n'.format(url))
        document_tree = download_document(url, headers)
        entries = parse_entries(document_tree)

        if not entries:
            continue

        for entry in entries:
            keys = ['url', 'geo', 'address']

            if all(i not in entry for i in keys):
                continue

            print('Detail url {}'.format(entry['url']))
            entry_details = download_document(entry['url'], headers)
            entry_details_parsed = parse_entry_details(entry_details)
            entry_parsed = parse_entry(entry)

            write_json({**entry_parsed, **entry_details_parsed}, file_name)
            sleep(1)

        url = parse_next_url(document_tree)
        print('\n\n')

        if url is None:
            break


@click.command()
@click.option('-o', '--offset', type=int)
@click.option('-q', '--query', required=True, type=str)
@click.option('-p', '--postal-code', type=str)
def main(offset, query, postal_code):
    aggregate(query, offset, postal_code)


if __name__ == '__main__':
    main()
