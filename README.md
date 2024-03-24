[![Update Rooster Teeth Data](https://github.com/shiruken/rt-archive/actions/workflows/update_rt.yml/badge.svg)](https://github.com/shiruken/rt-archive/actions/workflows/update_rt.yml) [![Update Internet Archive Data](https://github.com/shiruken/rt-archive/actions/workflows/update_archive.yml/badge.svg)](https://github.com/shiruken/rt-archive/actions/workflows/update_archive.yml)

# Rooster Teeth Archive

## Rooster Teeth API

Comprehensive mirror of the Rooster Teeth API. Each endpoint is stored as a single JSON file for easy parsing.

_Updated every 4 hours on the hour_

### `/watch`: https://svod-be.roosterteeth.com/api/v1/watch

* [`watch.json`](https://github.com/shiruken/rt-archive/blob/main/data/watch.json) (**Warning: Large File**)

## Derived Files

Listings derived from the Rooster Teeth API. Predominantly for use with the [`rooster`](https://github.com/i3p9/rooster) archival script.

_Updated every hour at minute 30_

* [`rt_urls.txt`](https://raw.githubusercontent.com/shiruken/rt-archive/main/data/rt_urls.txt): Rooster Teeth URLs for every video on the website.
* [`archive_urls.txt`](https://raw.githubusercontent.com/shiruken/rt-archive/main/data/archive_urls.txt): Internet Archive URLs (expected) for every video from the Rooster Teeth website.
* [`missing.txt`](https://raw.githubusercontent.com/shiruken/rt-archive/main/data/missing.txt): Rooster Teeth URLs for every video *missing* from Internet Archive.
* [`incomplete_rt.txt`](https://raw.githubusercontent.com/shiruken/rt-archive/main/data/incomplete_rt.txt): Rooster Teeth URLs for every video with an *incomplete* upload to Internet Archive.
* [`incomplete_archive.txt`](https://raw.githubusercontent.com/shiruken/rt-archive/main/data/incomplete_archive.txt): Internet Archive URLs for every video with an *incomplete* upload.
