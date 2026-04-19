from concurrent.futures import ThreadPoolExecutor
import os
import json
import random
from string import Template
import time

from src.parser_mixin import ParserMixin
from src import constants
from src import utils


class Crawler(ParserMixin):
    BASE_URL = "https://www.imdb.com"
    FIND_URL = "https://www.imdb.com/find/?s=tt&q=%s"
    TITLE_URL = "https://www.imdb.com/title/%s"
    SUCCESS_XPATH = '//script[@id="__NEXT_DATA__"]'
    CRAWLER_NAME = os.path.basename(__file__).replace(".py", "")
    # TEMPLATE_ERROR
    COOKIE_ERROR = Template("Error while getting cookies: $e").substitute
    PARSING_ERROR = Template("Error while parsing __NEXT_DATA__ JSON: $e").substitute
    YEAR_INPUT_ERROR = Template('INPUT_ERROR: "year" ($year) must be a int').substitute
    TITLE_INPUT_ERROR = Template('INPUT_ERROR: "title" key is not in <{$input}>').substitute
    SCRAPE_ERROR = Template("Error occurred while scraping $id: $e").substitute
    ACCESS_ERROR = Template("Error occurred while accessing $url: $e").substitute
    SESSION_ERROR = Template("Error occurred while starting the r-session: $e").substitute
    TYPE_INPUT_ERROR = Template("INPUT_ERROR: expected list but received $i_type").substitute
    SAVE_ERROR = Template("Error occurred while saving results: $e").substitute

    def __init__(self, movie_to_look_for: list[dict]) -> None:
        """
        """
        self.logger = utils.init__logger(f"{self.CRAWLER_NAME}.log")
        self.movie_to_look_for = movie_to_look_for
        self.title_result = []
        if constants.PROXY is None:
            self.proxies = {}
        else:
            self.proxies = {"http": constants.PROXY, "https": constants.PROXY}

    def clean_item(self, item: dict) -> dict:
        """
        """
        fist_level_keys = [
            "certificate", "genres", "metascore", "originalTitleText", "plot",
            "primaryImage", "ratingSummary", "releaseYear"
            "productionStatus", "runtime", "titleId", "titleType"
        ]
        item = {key: item[key] for key in fist_level_keys if key in item}
        item["genres"] = " | ".join(item.get("genres", []))
        item["primaryImage"] = item.get("primaryImage", {}).get("url", None)
        rating_summary = item.pop("ratingSummary", {})
        item["aggregateRating"] = rating_summary.get("aggregateRating", None)
        item["voteCountRating"] = rating_summary.get("voteCount", None)
        item["releaseDate"] = item.get("releaseDate", {}).get("year", None)
        item["productionStatus"] = item.get("productionStatus", {}).get("id", None)
        item["titleType"] = item.get("titleType", {}).get("id", None)
        item["url"] = self.TITLE_URL % item["titleId"]
        return item

    def scrape(self, iteration_id: str, input_dict: dict) -> None:
        """
        """
        def f_year(item, year): return item.get("releaseYear", 0) == year
        def f_title(item, title): return title in item["originalTitleText"].lower()
        self.logger.info(f"Processing {iteration_id}: {input_dict}")
        time.sleep(random.uniform(3, 7))
        title = input_dict["title"].strip().lower()
        year = input_dict["year"]
        qry = title
        if year:
            qry += f" ({year})"
        url = self.FIND_URL % qry
        self.logger.info(f"Getting tree for url: {url}")
        try:
            tree = self.get_tree_from_session(url)
            json_text = tree.xpath(
                '//script[@id="__NEXT_DATA__"]/text()')[0]
            data = json.loads(json_text)
            data = data["props"]["pageProps"]["titleResults"]["results"]
            data = [item["listItem"] for item in data]
        except Exception as e:
            raise Exception(self.PARSING_ERROR(e=e))
        if year:
            data = list(filter(lambda item: f_year(item, year), data))
        data = list(filter(lambda item: f_title(item, title), data))
        data = list(map(lambda item: self.clean_item(item), data))
        assert data != [], f'NOT RESULTS FOR "{title}"'
        self.title_result.append({iteration_id: {"data": data, "input": input_dict}})
        self.logger.info(f"{iteration_id} - {input_dict} processed")

    def paralell_coller(self, iteration_id: str, input_dict: dict) -> None:
        """
        """
        time.sleep(random.uniform(3, 7))
        try:
            self.scrape(iteration_id, input_dict)
        except Exception as e:
            self.logger.error(self.SCRAPE_ERROR(id=iteration_id, e=e))

    def sanitise_input(self) -> None:
        """
        """
        if not isinstance(self.movie_to_look_for, list):
            input_type = type(self.movie_to_look_for)
            raise Exception(self.TYPE_INPUT_ERROR(i_type=input_type))
        assert self.movie_to_look_for != [], "The INPUT is empty"
        input_dict_list = self.movie_to_look_for
        for input_dict in input_dict_list:
            assert "title" in input_dict, self.TITLE_INPUT_ERROR(input=input_dict)
            year = input_dict.get("year", None)
            if year is None:
                continue
            if not isinstance(year, int):
                raise Exception(self.YEAR_INPUT_ERROR(year=year))

    def crawl(self) -> None:
        """
        """
        self.logger.info(f"Start {self.CRAWLER_NAME}")
        if not os.path.exists(constants.CHROME_DRIVER_PATH):
            self.logger.critical("CHROME_DRIVER_PATH DOES NOT EXIST")
            return
        if not os.path.exists(constants.OUTPUT_DIR):
            self.logger.critical("OUTPUT_DIR DOES NOT EXIST")
            return

        self.logger.info("Sanitizing the INPUT ...")
        try:
            self.sanitise_input()
        except Exception as e:
            self.logger.critical(e)
            return
        self.logger.info("INPUT sanitized")

        try:
            self.logger.info("Starting the driver")
            self.start_driver(chrome_driver_path=constants.CHROME_DRIVER_PATH)
            self.logger.info(f"Accessing {self.BASE_URL}")
            self.driver.get(self.BASE_URL)
            self.wait_for_xpath(self.SUCCESS_XPATH)
        except Exception as e:
            self.logger.critical(self.ACCESS_ERROR(url=self.BASE_URL, e=e))
            self.quit_driver()
            return

        self.logger.info("Getting cookies ...")
        try:
            cookies = self.get_cookies(cookie_names=["aws-waf-token"])
        except Exception as e:
            self.logger.critical(self.COOKIE_ERROR(e=e))
            return
        finally:
            self.quit_driver()
        self.logger.info("Cookies obtained")

        try:
            self.logger.info("Starting requests-session ... ")
            self.start_session(headers=constants.HEADERS,
                               cookies=cookies,
                               proxies=self.proxies)
        except Exception as e:
            self.logger.critical(self.SESSION_ERROR(e=e))
            return

        total_titles = len(self.movie_to_look_for)
        self.logger.info(f"Starting the scraping of {total_titles} titles")
        with ThreadPoolExecutor(max_workers=constants.MAX_WORKERS) as executor:
            for index, input_dict in enumerate(self.movie_to_look_for, 1):
                iteration_id = f"{index}/{total_titles}"
                executor.submit(self.paralell_coller, iteration_id, input_dict)
        if self.title_result == []:
            self.logger.critical("NO_RESULTS")
            return
        total_results = len(self.title_result)
        if total_results == total_titles:
            self.logger.info("ALL TITLES OBTAINED RESULTS !!!")
        else:
            missing = total_titles-total_results
            self.logger.info(f"OBTAINED RESULTS: {total_results}/{total_titles}")
            self.logger.warning(f"MISSING TITLES:   {missing}")
        self.logger.info("Saving results ... ")
        try:
            file_path = os.path.join(constants.OUTPUT_DIR, "title_result.json")
            utils.save_json(file_path, self.title_result)
            self.logger.info(f"Results saved: {file_path}")
        except Exception as e:
            self.logger.critical(self.SAVE_ERROR(e=e))
        else:
            self.logger.info(f"End {self.CRAWLER_NAME}")
