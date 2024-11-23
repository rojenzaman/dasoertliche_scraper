#!/usr/bin/env python3

import re
import json
import httpx
import click
import logging
from lxml import html
from pathlib import Path
from fake_useragent import UserAgent
from time import sleep
from httpx import HTTPError
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(".crawler.log"),
        logging.StreamHandler()
    ]
)

EMAIL_REGEX = re.compile(r'[^@]+@[^@]+\.[^@]+')

def parse_entry_details(content):
    contact_data = {
        'website': '',
        'mailAddress': ''
    }

    doc = html.fromstring(content)
    contact_links = doc.xpath('//div[contains(@class, "lnks")]/a')

    for link in contact_links:
        classes = link.get('class', '').split()
        title = link.get('title', '').strip().lower()
        href = link.get('href', '').strip()
        if 'mail' in classes and EMAIL_REGEX.fullmatch(title):
            contact_data['mailAddress'] = title
            logging.debug(f"Found email address: {title}")
        elif 'www' in classes or href.startswith('http'):
            contact_data['website'] = href
            logging.debug(f"Found website: {href}")

    return contact_data

def parse_entries(content):
    doc = html.fromstring(content)
    entries = []
    hit_elements = doc.xpath('//div[contains(@class, "hit")]')
    logging.debug(f"Found {len(hit_elements)} hits on the page.")

    for idx, hit in enumerate(hit_elements, start=1):
        entry = {}
        # Extract the name
        name_element = hit.xpath('.//h2/a[contains(@class, "hitlnk_name")]')
        if name_element:
            name = name_element[0].text_content().strip()
            if name:
                entry['name'] = name
            else:
                logging.debug(f"Entry {idx}: Name is empty. Skipping entry.")
                continue  # Skip entries with empty names
            detail_url = name_element[0].get('href')
            if detail_url:
                entry['url'] = detail_url
            else:
                logging.debug(f"Entry {idx}: Detail URL is missing. Skipping entry.")
                continue  # Skip entries without detail URL
        else:
            logging.debug(f"Entry {idx}: No name element found. Skipping entry.")
            continue  # Skip entries without a name

        # Extract category
        category_element = hit.xpath('.//div[contains(@class, "category")]')
        if category_element:
            category = category_element[0].text_content().strip()
            if category:
                entry['category'] = category

        # Extract address
        address_element = hit.xpath('.//div[contains(@class, "left")]/address')
        if address_element:
            address_text = address_element[0].text_content().strip()
            # Replace multiple spaces and line breaks with a single space
            address_clean = ' '.join(address_text.split())
            entry['address'] = address_clean

        # Extract telephone
        phone_elements = hit.xpath('.//div[contains(@class, "phoneblock")]/span')
        telephone = ''
        for span in phone_elements:
            text = span.text_content().strip()
            if text.startswith('Tel.'):
                telephone = text.replace('Tel.', '').strip()
                break  # Prefer 'Tel.' over 'Fax.'
        if telephone:
            entry['telephone'] = telephone

        entries.append(entry)
        logging.debug(f"Entry {idx}: Parsed entry - {entry}")

    return entries

def parse_next_url(content):
    doc = html.fromstring(content)
    next_urls = doc.xpath('//a[@title="zur nächsten Seite"]/@href')

    if next_urls:
        next_url = next_urls[0]
        logging.debug(f"Next page URL found: {next_url}")
        return next_url
    else:
        logging.info("No next page URL found. Reached the last page.")
        return None

def download_document(url, headers, retries=3, delay=5):
    with httpx.Client(headers=headers, cookies={'CONSENT': 'YES+'}) as client:
        try:
            response = client.get(url, timeout=30)
            response.raise_for_status()
            logging.debug(f"Successfully downloaded content from {url}")
            return response.text
        except HTTPError as e:
            logging.error(f"HTTP error while downloading {url}: {e}")
            if retries > 0:
                logging.info(f"Retrying in {delay} seconds... ({retries} retries left)")
                sleep(delay)
                return download_document(url, headers, retries - 1, delay)
            else:
                logging.error(f"Failed to download {url} after multiple attempts.")
                return None
        except httpx.RequestError as e:
            logging.error(f"Request error while downloading {url}: {e}")
            if retries > 0:
                logging.info(f"Retrying in {delay} seconds... ({retries} retries left)")
                sleep(delay)
                return download_document(url, headers, retries - 1, delay)
            else:
                logging.error(f"Failed to download {url} after multiple attempts.")
                return None

def write_json_line(entry, file_name):
    try:
        with file_name.open('a', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')
            logging.debug(f"Appended entry to {file_name}")
    except Exception as e:
        logging.error(f"Unexpected error while writing to {file_name}: {e}")

def make_file_name_for_url_list():
    directory_path = Path.cwd() / 'data'
    directory_path.mkdir(parents=True, exist_ok=True)
    return directory_path / 'results.json'

def parse_entry(entry):
    # Normalize telephone number
    telephone = entry.get('telephone', '')
    if telephone:
        telephone = re.sub(r'\s+', '', telephone)
        entry['telephone'] = telephone
        logging.debug(f"Normalized telephone: {entry['telephone']}")

    # Clean up address
    address = entry.get('address', '')
    if address:
        # Further clean up if necessary
        entry['address'] = address.replace('\n', ', ').strip()
        logging.debug(f"Cleaned address: {entry['address']}")

    # Remove semicolons from 'name' and 'mailAddress' to prevent CSV issues
    if 'name' in entry:
        entry['name'] = entry['name'].replace(';', '')
    if 'mailAddress' in entry:
        entry['mailAddress'] = entry['mailAddress'].replace(';', '')

    return entry

def process_entry(entry, base_url, headers, file_path, file_lock):
    entry_parsed = parse_entry(entry)

    detail_url = entry.get('url')
    if detail_url:
        # Construct the absolute URL for the detail page
        if detail_url.startswith('/'):
            full_detail_url = f"{base_url}{detail_url}"
        else:
            full_detail_url = detail_url
        logging.info(f"Fetching details from: {full_detail_url}")
        entry_details_content = download_document(full_detail_url, headers)

        if entry_details_content:
            entry_details_parsed = parse_entry_details(entry_details_content)
            combined_entry = {**entry_parsed, **entry_details_parsed}
        else:
            logging.error(f"Failed to retrieve details from {full_detail_url}. Using basic entry data.")
            combined_entry = entry_parsed
    else:
        combined_entry = entry_parsed

    # Write combined_entry to the output
    with file_lock:
        write_json_line(combined_entry, file_path)

    # Reduce sleep time when data is not available
    sleep_duration = 1 if combined_entry else 0.1
    sleep(sleep_duration)  # Respectful delay between requests

def process_start_url(url, headers, workers, file_lock, file_path):
    base_url = 'https://www.dasoertliche.de'

    while True:
        logging.info(f"Processing URL: {url}")
        document_tree = download_document(url, headers)

        if not document_tree:
            logging.error(f"Failed to retrieve content from {url}. Skipping to next.")
            break

        entries = parse_entries(document_tree)

        if not entries:
            logging.info("No entries found on the current page.")
            # Reduce sleep time when no data is available
            sleep(0.1)
            break

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            for entry in entries:
                future = executor.submit(
                    process_entry, entry, base_url, headers, file_path, file_lock
                )
                futures.append(future)

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error processing entry: {e}")

        next_url = parse_next_url(document_tree)
        if not next_url:
            logging.info("No further pages to process for this URL. Moving to next.")
            break

        # Construct the absolute URL for the next page
        if next_url.startswith('/'):
            url = f"{base_url}{next_url}"
        else:
            url = next_url

        logging.info("--------------------------------------------------\n")

def process_url_list(url_list_file, workers, url_workers):
    with open(url_list_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    logging.info(f"Found {len(urls)} URLs to process.")

    # Initialize the lock for writing to files
    file_lock = threading.Lock()

    ua = UserAgent()
    headers = {'User-Agent': ua.random}

    # Generate a single output file name
    file_path = make_file_name_for_url_list()
    # Remove existing file if present to avoid appending to old data
    if file_path.exists():
        file_path.unlink()

    with ThreadPoolExecutor(max_workers=url_workers) as executor:
        futures = []
        for idx, url in enumerate(urls, start=1):
            logging.info(f"Scheduling URL {idx}/{len(urls)}: {url}")
            future = executor.submit(
                process_start_url, url, headers, workers, file_lock, file_path
            )
            futures.append(future)

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Error processing URL: {e}")

def aggregate(query, offset, postal_code, workers):
    file_path = make_file_name(query, postal_code)

    ua = UserAgent()
    headers = {'User-Agent': ua.random}

    params = {
        'kw': query,
        'form_name': 'search_nat'
    }

    if offset:
        params['recFrom'] = offset

    if postal_code:
        params['ci'] = postal_code

    base_url = 'https://www.dasoertliche.de'
    url = f"{base_url}/?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

    # Initialize the lock
    file_lock = threading.Lock()

    while True:
        logging.info(f"Processing URL: {url}")
        document_tree = download_document(url, headers)

        if not document_tree:
            logging.error(f"Failed to retrieve content from {url}. Skipping to next.")
            break

        entries = parse_entries(document_tree)

        if not entries:
            logging.info("No entries found on the current page.")
            break

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            for entry in entries:
                future = executor.submit(
                    process_entry, entry, base_url, headers, file_path, file_lock
                )
                futures.append(future)

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error processing entry: {e}")

        next_url = parse_next_url(document_tree)
        if not next_url:
            logging.info("No further pages to process. Exiting.")
            break

        # Construct the absolute URL for the next page
        if next_url.startswith('/'):
            url = f"{base_url}{next_url}"
        else:
            url = next_url

        logging.info("--------------------------------------------------\n")

def make_file_name(query, postal_code):
    directory_path = Path.cwd() / 'data'
    directory_path.mkdir(parents=True, exist_ok=True)

    if query and postal_code:
        file_name = f"{query.lower()}_{postal_code}"
    elif query:
        file_name = query.lower()
    elif postal_code:
        file_name = postal_code
    else:
        file_name = 'results'

    return directory_path / f"{file_name}.json"

@click.command()
@click.option('-o', '--offset', type=int, default=0, help='Starting offset for the search results.')
@click.option('-q', '--query', type=str, help='Search query term.')
@click.option('-p', '--postal-code', type=str, help='Postal code to filter the search results.')
@click.option('-w', '--workers', type=int, default=5, help='Number of parallel workers for data fetching.')
@click.option('-u', '--url-list', type=click.Path(exists=True), help='File containing list of URLs to process.')
@click.option('--url-workers', type=int, default=3, help='Number of parallel URL workers when processing URL list.')
def main(offset, query, postal_code, workers, url_list, url_workers):
    """
    Dasoertliche.de Scraper

    Fetches listings from dasoertliche.de based on the provided query and optional postal code,
    or processes a list of URLs provided in a file.
    """
    logging.info("Starting dasoertliche.de scraper.")

    if url_list:
        logging.info(f"Processing URLs from list: {url_list}")
        process_url_list(url_list, workers, url_workers)
    elif query:
        logging.info(f"Query: {query}, Offset: {offset}, Postal Code: {postal_code}, Workers: {workers}")
        aggregate(query, offset, postal_code, workers)
    else:
        logging.error("You must provide either a search query or a URL list file.")
        click.echo("Error: You must provide either a search query (-q) or a URL list file (-u).")
        return

    logging.info("Scraping completed.")

if __name__ == '__main__':
    main()
