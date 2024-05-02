from argparse import ArgumentParser
import numpy as np
import os
import urllib.parse
import yaml
from lib.ocr import Ocr
from lib.nichinoken import Nichinoken, Event
from lib.line_notify import LineNotify


WEEK_OF_DAY_MAPPING = {
    0: "月",
    1: "火",
    2: "水",
    3: "木",
    4: "金",
    5: "土",
    6: "日",
}
EVENTS_PER_MESSAGE = 3


def build_urls(event_list: list[Event]) -> tuple[list[str], list[str]]:
    BASE_URL = "https://www.google.com/calendar/render?action=TEMPLATE"
    labels = []
    urls = []

    for event in event_list:
        encoded_text = urllib.parse.quote(event.name)
        date_digits = str(event.date).replace("-", "")
        url = f"{BASE_URL}&text={encoded_text}&details=&dates={date_digits}/{date_digits}&sf=true&output=xml"
        week_of_day = WEEK_OF_DAY_MAPPING[event.date.weekday()]
        labels.append(f"{event.date}（{week_of_day}） {event.name}")
        urls.append(url)

    return labels, urls


def build_messages(labels: list[str], urls: list[str], events_per_message: int) -> str:
    _messages = [f"\n■ {label}\n{url}" for label, url in zip(labels, urls)]

    n_sublist = int(np.ceil(len(_messages) / events_per_message))
    messages = []

    for msgs in np.array_split(_messages, n_sublist):
        msg = "\n".join(msgs)
        messages.append(msg)
    return messages


def main():
    parser = ArgumentParser()
    parser.add_argument("content_filename", type=str, help="Filename of schedule")
    parser.add_argument("school_year", type=int, choices=[1, 2, 3, 4, 5, 6], help="Target school year")
    parser.add_argument("--no-cache", action="store_true", help="Don't use cached file")
    parser.add_argument("--debug", action="store_true", help="Print debug messages")
    args = parser.parse_args()

    with open("config.yml", "r") as f:
        config = yaml.safe_load(f)

    project_id = config["ocr"]["project_id"]
    location = config["ocr"]["location"]
    processor_id = config["ocr"]["processor_id"]
    token = config["line"]["token"]

    school_year = args.school_year
    filename = args.content_filename
    debug_mode = args.debug
    output_filename = os.path.basename(filename).split(".")[0] + ".json"

    if (not os.path.exists(output_filename)) or args.no_cache:
        print(f"OCR {filename}...")
        ocr = Ocr(project_id, location, processor_id)
        response = ocr.process_document(filename)
        ocr.save_response_to_jsonfile(response, output_filename)
        print("Done.")

    nichinoken = Nichinoken(school_year, debug=debug_mode)
    events = nichinoken.get_schedule_list(output_filename)

    labels, urls = build_urls(events)
    messages = build_messages(labels, urls, events_per_message=EVENTS_PER_MESSAGE)

    for msg in messages:
        print(msg)

    if token and not debug_mode:
        line_notifier = LineNotify(token)
        for msg in messages:
            line_notifier.send_message(msg)


if __name__ == "__main__":
    main()
