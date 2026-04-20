import argparse
import json
from src.crawler import Crawler


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_input", required=True)

    args = parser.parse_args()
    try:
        with open(args.json_input, "r", encoding="utf-8") as file:
            movie_to_look_for = json.load(file)
    except Exception as e:
        raise e
    crawler_object = Crawler(movie_to_look_for)
    crawler_object.main()
