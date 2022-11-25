#!/usr/bin/env python3

import re
import json
import requests
import lxml.html
import argparse

from time import sleep
from requests.exceptions import ConnectionError
from fake_useragent import UserAgent

EMAIL_REGEX = re.compile(r'[^@]+@[^@]+\.[^@]+')


def german_postalcodes():
    postal_codes = []

    with open('data/german_postalcodes.geojson', 'r') as f:
        d = json.load(f)

        for feature in d['features']:
            postal_codes.append(feature['properties']['postcode'])

    return postal_codes


def parse_entry_details(content):
    doc = lxml.html.fromstring(content)
    contact = doc.xpath('//div[@class="lnks"]')

    mail = contact[0].xpath('./a[@class="mail"]')
    web = contact[0].xpath('./a[@class="www"]')

    contact_data = {}

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

    if 'mailAddress' not in contact_data:
        contact_data['mailAddress'] = ''

    if 'website' not in contact_data:
        contact_data['website'] = ''

    return contact_data


def parse_entries(content):
    doc = lxml.html.fromstring(content)
    d = doc.xpath('//script[@type="application/ld+json"]/text()')
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
    doc = lxml.html.fromstring(content)
    n = doc.xpath('//a[@title="zur nächsten Seite"]/@href')

    if len(n) > 0:
        url = n[0]
    else:
        url = None

    return url


def download_document(url, headers):
    try:
        r = requests.get(url, headers=headers, cookies={'CONSENT': 'YES+'})

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
    if postal_code.isnumeric():
        file_name = '{}_{}'.format(query.lower(), postal_code)
    else:
        file_name = '{}'.format(query.lower())

    return 'data/{}.json'.format(file_name)


def parse_entry(item):
    item.pop('aggregateRating') if 'aggregateRating' in item else item

    item['coordinates'] = []
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
    item.pop('geo')
    item.pop('@type')
    item['address'].pop('@type')

    return item


def aggregate(query, offset_value, postal_code):
    file_name = make_file_name(query, postal_code)

    ua = UserAgent()
    headers = { 'User-Agent': ua.random }

    param = 'kw={}&ci={}&form_name=search_nat'.format(query, postal_code)
    url = 'https://www.dasoertliche.de?{}'.format(param)

    if offset_value:
        url = '{}&recFrom={}'.format(url, offset_value)

    while True:
        print('Next url {}\n'.format(url))
        document_tree = download_document(url, headers)
        entries = parse_entries(document_tree)

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


def main():
    parser = argparse.ArgumentParser(description='Simple scraper')
    parser.add_argument('--offset', dest='offset', type=int)
    parser.add_argument('--query', dest='query', required=True)
    parser.add_argument('--use-postal-codes', dest='use_postal_codes', action='store_true')

    args = parser.parse_args()

    if args.use_postal_codes:
        postal_codes = german_postalcodes()

        for postal_code in postal_codes:
            aggregate(args.query, -1, postal_code)
    else:
        if 'offset' in args:
            offset_value = args.offset
        else:
            offset_value = -1

        aggregate(args.query, offset_value, '')


if __name__ == '__main__':
    main()
