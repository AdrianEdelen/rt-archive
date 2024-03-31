import requests
from urllib.parse import urlencode
import re
import csv
import pandas as pd
import json
from pathlib import Path
from string import Template


def identify_missing_incomplete():
    """Identify missing and incomplete Rooster Teeth videos from the Internet Archive
    - Missing video URLs: `data/missing.txt`
    - Incomplete Upload URLs (`data/incomplete.csv`)
      - Rooster Teeth URLs only: `data/incomplete_rt.txt`
      - Internet Archive URLs only: `data/incomplete_archive.txt`
    """
    url = "https://archive.org/services/search/v1/scrape"
    query = {
        'q': 'scanner:"Roosterteeth Website Mirror"',
        'fields': 'identifier,addeddate,item_size,format',
        'count': 10000
    }

    archive_items = []
    incomplete = []

    count = 1
    while True:
        response = requests.get(f"{url}?{urlencode(query)}")
        json = response.json()

        for item in json['items']:
            if (
                "roosterteeth-" in item["identifier"] and
                "roosterteeth-test" not in item["identifier"] and
                "-bonus-bonus" not in item["identifier"]
            ):
                archive_items.append(item["identifier"])

                if not (
                    "MPEG4" in item['format'] and
                    "JSON" in item['format'] and # .info.json file
                    "Unknown" in item['format'] and # .description file
                    (
                        "JPEG" in item['format'] or
                        "PNG" in item['format'] or
                        "Animated GIF" in item['format'] or
                        "JPEG 2000" in item['format']
                    )
                ):
                    incomplete.append(item['identifier'])

        if 'cursor' in json:
            query['cursor'] = json['cursor']
        else:
            break

        count += 1

    print(f"Identified {len(archive_items):,} items from the Internet Archive Scrape API across {count:,} requests")

    with open("data/archive_urls.txt", "r") as fp:
        archive_ids = [line.rstrip().replace("https://archive.org/details/", "") for line in fp]

    with open("data/rt_urls.txt", "r") as fp:
        rt_urls = [line.rstrip() for line in fp]

    archive_items = set(archive_items)
    missing = [x for x in archive_ids if x not in archive_items]
    print(f"Found {len(missing):,} items missing from Internet Archive")
    with open("data/missing.txt", "w") as fp:
        for item in missing:
            fp.write(f"{rt_urls[archive_ids.index(item)]}\n")

    print(f"Found {len(incomplete):,} incomplete items on Internet Archive")
    with open("data/incomplete_urls.csv", "w") as fp:
        writer = csv.writer(fp)
        writer.writerow(['archive_url', 'rt_url'])
        for item in incomplete:
            writer.writerow([
                f"https://archive.org/details/{item}",
                f"{rt_urls[archive_ids.index(item)]}"
            ])
    with open("data/incomplete_rt_urls.txt", "w") as fp:
        for item in incomplete:
            fp.write(f"{rt_urls[archive_ids.index(item)]}\n")
    with open("data/incomplete_archive_urls.txt", "w") as fp:
        for item in incomplete:
            fp.write(f"https://archive.org/details/{item}\n")

    # Update README metrics
    with open("README.md", "r") as fp:
        readme = fp.read()
    readme = re.sub(r"(?<=\* Items on Internet Archive: )([\d, \(.\%\)]+)", f"{len(archive_items):,} ({len(archive_items) / len(rt_urls):.2%})", readme)
    readme = re.sub(r"(?<=\* Items Missing from Internet Archive: )([\d, \(.\%\)]+)", f"{len(missing):,} ({len(missing) / len(rt_urls):.2%})", readme)
    readme = re.sub(r"(?<=\* Incomplete Items on Internet Archive: )([\d,]+)", f"{len(incomplete):,}", readme)
    with open("README.md", "w") as f:
        f.write(readme)

    return missing, incomplete


def generate_checklist(missing, incomplete):
    """Generates CSV file for RT Archival Checklist
    * Requires intermediary file (`data/.temp.csv`) generated by `update_rt.py`
    * Writes output to `data/checklist.csv`

    Columns: title, rt_id, rt_url, show, date, is_first, is_uploaded, is_complete_upload, is_removed
    """
    dark = []  # Removed Archive IDs (Updated daily by update_archive_dark.py)
    with open("data/dark.csv", "r") as fp:
        reader = csv.reader(fp)
        next(reader)  # Skip header
        for row in reader:
            dark.append(row[0].replace("https://archive.org/details/", ""))

    with open("data/.temp.csv", "r") as input, open("data/checklist.csv", "w") as output:
        reader = csv.reader(input)
        writer = csv.writer(output)

        checklist = []
        header = next(reader)
        header.extend(['is_uploaded', 'is_complete_upload', 'is_removed'])
        checklist.append(header)

        for row in reader:
            identifier = f"roosterteeth-{row[1]}"
            is_uploaded = identifier not in missing
            is_complete_upload = is_uploaded and identifier not in incomplete
            is_removed = identifier in dark
            row.extend([is_uploaded, is_complete_upload, is_removed])
            checklist.append(row)

        writer.writerows(checklist)


def generate_website():
    """Generates Archive Progress website"""

    df = pd.read_csv("data/checklist.csv")
    df_show_slugs = pd.read_csv("data/shows.csv", index_col="title")

    with open("docs/_template.html", "r") as fp:
        html = fp.read()
    html_template = MyTemplate(html)

    def process_shows(df):
        slug = df_show_slugs.loc[df.name].values[0]
        summary = generate_summary(df)
        show = pd.concat([pd.Series(slug, index=["slug"]), summary])
        process_episodes(df, slug)
        return show

    def process_episodes(df, show_slug):
        summary = generate_summary(df)
        df['rt_url'] = df['rt_url'].str.replace(r'https://roosterteeth.com/watch/', "")
        df.rename(columns={'rt_id': 'id', 'rt_url': 'slug'}, inplace=True)

        output = {
            "show": df.name,
            "slug": show_slug,
            "summary": summary.to_dict(),
            "data": df.to_dict(orient="records"),
        }
        Path(f"docs/{show_slug}/").mkdir(parents=True, exist_ok=True)
        with open(f"docs/{show_slug}/data.json", "w") as fp:
            json.dump(output, fp, indent=4)

        query = {
            'query': f'scanner:"Roosterteeth Website Mirror" AND show_title:"{df.name}"',
            'sort': '-date'
        }
        show_search_url = f"https://archive.org/search?{urlencode(query)}"
        html_new = html_template.substitute({
            "show": df.name,
            "show_slug": show_slug,
            "show_search_url": show_search_url,
        })
        with open(f"docs/{show_slug}/index.html", "w") as fp:
            fp.write(html_new)

    def generate_summary(df):
        output = {}
        output['count'] = df['rt_id'].count()
        output['uploaded'] = df['is_uploaded'].sum() + df['is_removed'].sum()
        output['missing'] = output['count'] - output['uploaded']
        output['incomplete'] = output['uploaded'] - df['is_complete_upload'].sum() - df['is_removed'].sum()
        output['removed'] = df['is_removed'].sum()
        return pd.Series(output)

    df_shows = df.groupby("show").apply(process_shows, include_groups=False)
    df_shows.sort_index(key=lambda x: x.str.lower(), inplace=True)
    summary = generate_summary(df)

    output = {
        "summary": summary.to_dict(),
        "data": df_shows.reset_index().to_dict(orient="records"),
    }
    with open("docs/data.json", "w") as fp:
        json.dump(output, fp, indent=4)

    # Generate data for missing page
    df_missing = df[~df['is_uploaded'] & ~df['is_removed']].copy()
    df_missing['rt_url'].to_csv("docs/missing/missing.txt", index=False, header=False)
    df_missing['rt_url'] = df_missing['rt_url'].str.replace(r'https://roosterteeth.com/watch/', "")
    df_missing = df_missing.merge(df_show_slugs, left_on="show", right_index=True)
    df_missing.rename(columns={'rt_id': 'id', 'rt_url': 'slug', 'slug': 'show_slug'}, inplace=True)
    df_missing = df_missing[['title', 'slug', 'date', 'is_first', 'show', 'show_slug']]
    output = {
        "count": df_missing.shape[0],
        "data": df_missing.to_dict(orient="records"),
    }
    with open("docs/missing/data.json", "w") as fp:
        json.dump(output, fp, indent=4)


class MyTemplate(Template):
    delimiter = '$$'


if __name__ == "__main__":
    missing, incomplete = identify_missing_incomplete()
    generate_checklist(missing, incomplete)
    generate_website()
