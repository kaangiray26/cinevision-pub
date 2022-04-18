import secrets
from bs4 import BeautifulSoup
import requests
import re
from imdb import IMDb, IMDbError


class MovieDB:
    def __init__(self):
        self.ia = IMDb()
        self.movies = []
        self.fetch_movies()

    def has_recommendation(self, tag):
        return tag.has_attr('href') and tag['href'].startswith('/title/tt')

    def has_actor(self, tag):
        return tag.has_attr('data-testid') and tag['data-testid'] == "title-cast-item__actor"

    def get_recommendations(self, seen):
        if len(seen) > 0:
            id = seen[secrets.randbelow(len(seen))]
        else:
            id = self.movies[secrets.randbelow(len(self.movies))]

        html = requests.get(f'https://www.imdb.com/title/tt{id}/').content
        soup = BeautifulSoup(html, 'html.parser')
        recs = soup.find("section", attrs={"data-testid": "MoreLikeThis"})
        rec_ids = [re.findall("title/tt(.......)", obj['href'])[0] for obj in recs.find_all(self.has_recommendation)]
        return self.get_movie(rec_ids[secrets.randbelow(len(rec_ids))])
        

    def get_top_cast(self, id):
        html = requests.get(f'https://www.imdb.com/title/tt{id}/').content
        soup = BeautifulSoup(html, 'html.parser')
        top_cast = soup.find("section", attrs={"data-testid": "title-cast"})
        return [obj.get_text() for obj in top_cast.find_all(self.has_actor, limit=5)]

    def fetch_movies(self):
        pop_100 = set(self.ia.get_popular100_movies())
        top_100 = set(self.ia.get_top250_movies())
        self.movies = [movie.movieID for movie in list(pop_100.union(top_100))]

    def random_selection(self):
        movie = self.movies[secrets.randbelow(len(self.movies))]
        recs = self.get_recommendations(movie.movieID)
        rand = recs[secrets.randbelow(len(recs))]

        selected = self.ia.get_movie(rand)
        print(selected)
        print(selected.items())
        print(f'https://www.imdb.com/title/tt{selected.movieID}/')

    def get_movie(self, id):
        movie = self.ia.get_movie(id)
        title = movie.get('long imdb title')
        cast = [actor.get('name') for actor in movie.get('cast')[:5]]
        plot = movie.get('plot')[0]
        link = f'https://www.imdb.com/title/tt{movie.movieID}/'
        rating = movie.get('rating')
        cover = movie.get('full-size cover url')
        return (id, title, cast, plot, rating, link, cover)

    def get_movie_basic(self, id):
        movie = self.ia.get_movie(id)
        title = movie.get('long imdb title')
        link = f'https://www.imdb.com/title/tt{movie.movieID}/'
        return (title, link)

    def get_random_movie(self, marked):
        combined = marked[0] + marked[1] + marked[2]
        movielist = list(set(self.movies) - set(combined))
        if len(movielist) > 0:
            return self.get_movie(movielist[secrets.randbelow(len(movielist))])
        return self.get_recommendations(marked[1])

    def count(self):
        return len(self.movies)