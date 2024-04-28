import datetime
import dataclasses
import json
import numpy as np
import pandas as pd
import re

KEYWORDS_GRADE_3_6 = ["授業",  "テスト",  "模試", "講習", "保護者会", "再開", "休講", "休校"]
KEYWORDS_GRADE_1_2 = ["ふむふむ",  "わくわく"]
IGNORE_KEYWORDS = ["口座振替日", "授業は", "次回 「"]
THRESHOLD = {
    "WORD_DATE_DISTANCE": 0.15,
    "WORD_MAX_HEIGHT": 0.1,
    "WORD_MAX_WIDTH": 0.25,
    "WORD_GRADE_DISTANCE": 0.1,
}


@dataclasses.dataclass
class OcrWord:
    text: str
    cx: float
    cy: float
    width: float
    height: float


@dataclasses.dataclass
class Event:
    date: datetime.date
    name: str


class Nichinoken:
    def __init__(self, school_year, debug=False):
        assert school_year in (1, 2, 3, 4, 5, 6)
        self.school_year = school_year
        self.debug = debug

    def get_schedule_list(self, filename: str):
        response = json.load(open(filename, 'r'))
        words = self.__read_response(response)
        if self.debug:
            for word in words:
                print(word)

        year, month = self.__get_info_from_filename(filename)

        if year == -1:
            year = datetime.datetime.today().year
            print(f"Target year is set to {year}")

        if month == -1:
            month = self.__extract_month(words)
            if month == -1:
                raise ValueError("Target month is unknown")

        date_col_x_coord = self.__calc_date_column_Xcoord(words)
        if self.debug:
            print('date_col_x_coord', date_col_x_coord)
        date_y_coord_dict = self.__extract_dates_row_Ycoords(words, year,
                                                             month, date_col_x_coord)

        # 日付順にキーをソート
        date_y_coord_dict = dict(sorted(date_y_coord_dict.items()))

        # 欠損値補間
        date_y_coord_dict = self.__interpolate_missing_dates(date_y_coord_dict)
        date_y_coord_dict = dict(sorted(date_y_coord_dict.items()))
        if self.debug:
            for key, val in date_y_coord_dict.items():
                print(key, val)

        school_year_x_coord = self.__extract_school_year_column_Xcoord(words, self.school_year)
        if school_year_x_coord < 0:
            raise ValueError(f"Cannot find {self.school_year}年生 in words")
        if self.debug:
            print('school_year_x_coord', school_year_x_coord)

        event_list = self.__extract_schedule(words, date_y_coord_dict,
                                             school_year_x_coord,
                                             self.school_year, year)
        if self.debug:
            for event in event_list:
                print(event)
        return event_list

    def __read_response(self, response: dict, pageNo: int = 0) -> list[OcrWord]:
        words = []

        for i, data in enumerate(response["pages"][pageNo]["blocks"]):
            segments = data["layout"]["textAnchor"]["textSegments"][pageNo]
            if "startIndex" in segments:
                startIndex = int(segments["startIndex"])
            else:
                startIndex = 0
            endIndex = int(segments["endIndex"])

            normalizedVertices = data["layout"]["boundingPoly"]["normalizedVertices"]
            norm_min_x = min([float(v["x"]) for v in normalizedVertices])
            norm_max_x = max([float(v["x"]) for v in normalizedVertices])
            norm_min_y = min([float(v["y"]) for v in normalizedVertices])
            norm_max_y = max([float(v["y"]) for v in normalizedVertices])

            cx = (norm_min_x + norm_max_x) / 2
            cy = (norm_min_y + norm_max_y) / 2
            width = norm_max_x - norm_min_x
            height = norm_max_y - norm_min_y
            text = response["text"][startIndex:endIndex].strip()
            word = OcrWord(text, cx, cy, width, height)
            words.append(word)

        return words

    def __get_info_from_filename(self, filename: str) -> tuple[int, int]:
        year = -1
        month = -1

        m = re.search(r'(\d\d)(\d\d).json$', filename)
        if m:
            year = int(m.groups()[0]) + 2000
            month = int(m.groups()[1])

        return year, month

    def __extract_month(self, words: list[OcrWord]) -> int:
        month = -1
        for word in words:
            m = re.search(r'(\d+)月号', word.text)
            if m:
                month = m.groups()[0]
                break

        return month

    def __calc_date_column_Xcoord(self, words: list[OcrWord]) -> float:
        cx_list = []

        for word in words:
            if re.match(r'^[\d]{1,2}$', word.text):
                cx_list.append(word.cx)

        return np.median(cx_list)

    def __extract_dates_row_Ycoords(self,
                                    words: list[OcrWord],
                                    year: int,
                                    month: int,
                                    date_col_x_coord: float) -> dict[datetime.date, float]:
        date_y_dict = {}

        for word in words:
            text = word.text
            text = text.replace("||", "11")
            text = text.split(" ")[0]

            if abs(word.cx - date_col_x_coord) <= 0.15 and word.height < THRESHOLD["WORD_MAX_HEIGHT"]:
                if re.match(r'\d{1,2}$', text):
                    date = f"{month}/{text}"
                else:
                    date = text

                # 日付のフォーマットに合わないものは除外
                if not re.match(r'^\d{1,2}/\d{1,2}$', date):
                    continue

                _month, _day = map(int, date.split("/"))
                try:
                    key = datetime.date(year, _month, _day)
                except ValueError:
                    continue

                if key not in date_y_dict:
                    date_y_dict[key] = word.cy

        return date_y_dict

    def __interpolate_missing_dates(self, date_cy_dict: dict[datetime.date, str]) -> dict[datetime.date, str]:
        date_list = []
        y_list = []
        prev_date = None

        for date, cy in date_cy_dict.items():
            if prev_date is None:
                date_list.append(date)
                y_list.append(cy)
                prev_date = date
                continue

            delta = (date - prev_date).days
            if delta > 1:
                for i in range(1, delta):
                    missing_date = prev_date + datetime.timedelta(days=i)
                    date_list.append(missing_date)
                    y_list.append(np.nan)

            date_list.append(date)
            y_list.append(cy)
            prev_date = date

        # 欠損した座標を補間
        y_list = pd.Series(y_list).interpolate().tolist()

        return {date: cy for date, cy in zip(date_list, y_list)}

    def __extract_school_year_column_Xcoord(self, words: list[OcrWord],
                                            school_year: int) -> float:
        for word in words:
            if school_year in (1, 2):
                if "1・2年生" in word.text:
                    return word.cx
            else:
                if f"{school_year}年生" in word.text:
                    return word.cx
        return -1

    def __search_date(self, date_y_coord_dict: dict[datetime.date, float], cy: float) -> datetime.date:
        pos = np.argmin(np.absolute(np.array(list(date_y_coord_dict.values())) - cy))
        return list(date_y_coord_dict.keys())[pos]

    def __extract_schedule(self,
                           words: list[OcrWord],
                           date_y_coord_dict: dict[str, float],
                           school_year_x_coord: float,
                           school_year: int,
                           year: int) -> list[Event]:
        event_list = []

        if school_year in (1, 2):
            TARGET_KEYWORDS = KEYWORDS_GRADE_1_2
        else:
            TARGET_KEYWORDS = KEYWORDS_GRADE_3_6

        for word in words:
            text = word.text
            if abs(word.cx - school_year_x_coord) <= THRESHOLD["WORD_GRADE_DISTANCE"] and word.width < THRESHOLD["WORD_MAX_WIDTH"]:
                if any(keyword in text for keyword in IGNORE_KEYWORDS):
                    continue
                if any(keyword in text for keyword in TARGET_KEYWORDS):
                    date = self.__search_date(date_y_coord_dict, word.cy)
                    event = Event(date, text.replace("\n", " "))
                    event_list.append(event)

        return event_list

