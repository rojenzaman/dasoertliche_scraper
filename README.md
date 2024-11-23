# dasoertliche.de Scraper

A simple scraper to fetch listings from [dasoertliche.de](https://www.dasoertliche.de) based on your search criteria.

## Why?

I created this scraper to gather local landlord information from specific cities, helping me connect with them for housing opportunities. It worked well for me, and I hope it can be useful to others too. The scraped data is stored locally in a JSON file within the `data` directory, which is excluded from version control.

## Setup

1. **Clone the repository:**
    ```sh
    git clone https://github.com/p3t3r67x0/dasoertliche_scraper.git
    cd dasoertliche_scraper
    ```

2. **Create and activate a virtual environment:**
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install the dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

## Usage

Before running the scraper, ensure your virtual environment is activated.

### Search with Query

Fetch listings based on a search term, optional offset, and postal code.

```sh
python crawler.py --query Hausverwaltung --offset 5 --postal-code 10963
````

If you don't need an offset:

```sh
python crawler.py --query Hausverwaltung --postal-code 10963
```

If you want to omit the postal code:

```sh
python crawler.py --query Hausverwaltung
```

### Process a List of URLs

Provide a file containing a list of URLs to scrape.

```sh
python crawler.py --url-list urls.txt
```

## Logging

The scraper logs its activities to both the console and a `.crawler.log` file. You can monitor the progress and check for any issues there.

Example log output:

```
Processing URL: https://www.dasoertliche.de/?kw=Ferienwohnung&ci=&form_name=search_nat&recFrom=5
Fetching details from: https://www.dasoertliche.de/Themen/Astra-Hotel-Kaiserslautern-Inh-Ingeborg-Weismantel-Kaiserslautern-Innenstadt-Rudolf-Breitscheid-Str
...
```

## Issues

Feel free to open an issue if you encounter any problems or have suggestions for improvements.

## TODO

- Improve command-line options
- Add more storage options
- Implement export to contact books

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
