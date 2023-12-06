import requests
import re
import os
import argparse
import logging
import pathlib

LITEROTICA_STORY_URL_REGEX = r"https://www\.literotica\.com/s/(?P<title_id>.+)"
LITEROTICA_AUTHORS_API_URL_FORMAT = "https://www.literotica.com/api/3/authors/{uid}"
LITEROTICA_STORIES_API_URL_FORMAT = "https://www.literotica.com/api/3/stories/{title_id}"
USER_AGENT = "Mozilla/5.0"
OUTPUT_FORMAT = "[{author}]/{title}.txt"

logger = logging.getLogger(__name__)
argparse = argparse.ArgumentParser()
argparse.add_argument("url", help="Story URL")
argparse.add_argument("-d", "--debug", help="Debug mode", action="store_true")
argparse.add_argument("-o", "--output", help="Output directory", default="output")
argparse.add_argument("-s", "--series", help="Download entire series", action="store_true")
argparse.add_argument("-f", "--format", help="Output format", default=OUTPUT_FORMAT)
args = argparse.parse_args()


def get_page_text(title_id: str | int, page: int) -> str:
    url = LITEROTICA_STORIES_API_URL_FORMAT.format(title_id=title_id)
    url += '?params={"contentPage":' + str(page) + '}'
    logger.debug(f"Fetching page {page} from {url}")
    response = requests.get(url, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.json()["pageText"]


def get_story(title_id: str | int) -> [str]:
    pages = get_story_info(title_id)["pages"]
    story = []
    for page in range(1, pages + 1):
        story.append(get_page_text(title_id, page))
    return story


def get_story_info(title_id: str | int):
    url = LITEROTICA_STORIES_API_URL_FORMAT.format(title_id=title_id)
    logger.debug(f"Fetching story info from {url}")
    response = requests.get(url, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    story_info = response.json()["submission"]
    story_info["pages"] = response.json()["meta"]["pages_count"]
    return story_info


def main():
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    if not os.path.exists(args.output):
        logging.debug(f"Creating output directory {args.output}")
        os.makedirs(args.output)

    match = re.match(LITEROTICA_STORY_URL_REGEX, args.url)
    if not match:
        raise ValueError("Invalid URL")
    title_id = match.group("title_id")
    story_info = get_story_info(title_id)
    author = story_info["author"]["username"]
    title = story_info["title"]
    if args.series:
        series = story_info["series"]["items"]
        for item in series:
            title_id = item["id"]
            story = get_story(title_id)
            title = item["title"]
            with open(os.path.join(args.output, args.format.format(author=author, title=title)), "w") as file:
                file.writelines(story)
    else:
        logging.debug(f"Downloading {title} by {author}")
        story = get_story(title_id)
        with open(os.path.join(args.output, args.format.format(author=author, title=title)), "w") as file:
            file.writelines(story)


if __name__ == '__main__':
    main()
