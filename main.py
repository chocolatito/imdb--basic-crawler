from src.crawler import Crawler

movie_to_look_for = [
    {"title": "primal fear", "year": 1996},
    {"title": "Raging Bull", "year": 1980},
]
if __name__ == "__main__":
    crawler_object = Crawler(movie_to_look_for)
    crawler_object.main()
