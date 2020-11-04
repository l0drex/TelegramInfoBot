from datetime import date
from typing import Optional, List, Tuple, Union, Dict
import requests

Coordinates = Tuple[float, float]
Radius = Tuple[Coordinates, float]


class Canteen:
    def __init__(self,
                 canteen_id: str,
                 name: str,
                 city: Optional[str] = None,
                 address: Optional[str] = None,
                 coordinates: Optional[Coordinates] = None):

        if not (canteen_id and name) or city == '' or address == '' or coordinates == []:
            raise ValueError('args must not be empty')

        self.id = canteen_id
        self.name = name
        self.city = city
        self.address = address
        self.coordinates = coordinates

    def get_days(self,
                 day: Optional[date] = None,
                 start: str = date.today().isoformat()) -> Union[list, dict]:
        """ List days of a canteen. Useful to determine if a canteen is open or not.

        :param day: Return only a single day of the date provided.
        :param start: Start day. Defaults to today
        :return:
        """

        url = url_canteen + f'/canteens/{self.id}/days'
        if day is None:
            return send_request(url, {'start': start})
        else:
            return send_request(url + f'/{day.isoformat()}')

    def get_day(self,
                day: date) -> dict:
        """ Return a single day.
        Shortcut for get_days(canteen_id, days=[day])
        """
        return self.get_days(day=day)

    def get_meals(self, day: date, id_meal: Optional[str] = None) -> Union[list, dict]:
        """ Returns the available meals on a certain day in a canteen.

        :param day: the day to be searched for meals
        :param id_meal: ID of a meal to be returned
        """

        url = url_canteen + f'/canteens/{self.id}/days/{day.isoformat()}/meals'

        if id_meal is None:
            return send_request(url)
        else:
            return send_request(url + f'/{id_meal}')

    def get_meal(self, day: date, id_meal: str) -> dict:
        """ Returns a meal
        Shortcut for get_meals(canteen_id, day, id_meal=id_meal)
        """
        return self.get_meals(day, id_meal=id_meal)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, Canteen):
            return self.id == other.id
        else:
            return False


url_canteen = 'https://api.studentenwerk-dresden.de/openmensa/v2'


def send_request(url: str, params: Optional[dict] = None):
    """ Sends requests to the url with parameters and returns the response."""

    if not url.isprintable():
        raise ValueError('Url must not be null or empty')

    print(f'Sending request to {url}')
    response = requests.get(url, params)
    response.encoding = 'UTF-8'
    return response.json()


def get_canteens(near: Optional[Radius] = None,
                 ids: Optional[List[str]] = None,
                 has_coordinates: Optional[bool] = None) -> List[Canteen]:
    """ Returns a list of canteens

    :param near: Radius Used to list only canteens within a distance from a point.
    :param ids: Return only canteens with these ids.
    :param has_coordinates: Return only canteens with or without coordinates

    :return: A dict with all canteens
    """

    params = {}
    # add arguments to the params
    if near is not None:
        coord: Coordinates = near[0]
        radius = near[1]

        if not (-90 < coord[0] < 90 and -180 < coord[1] < 180):
            raise ValueError('Coordinates out of range')

        if not (0 < radius < 50):
            raise ValueError('Distance out of range')

        params.update({
                'near[lat]': near[0][0],
                'near[long]': near[0][1],
                'near[dist]': near[1]
            })
    if ids is not None:
        if len(ids) <= 0 or '' in ids:
            raise ValueError('ids and id must not be empty!')

        params.update({
            'ids': ids
        })
    if has_coordinates is not None:
        params['hasCoordinates'] = has_coordinates

    # send request and return answer
    response: list = send_request(url_canteen + '/canteens', params)
    canteens = []

    for c in response:
        response.pop(response.index(c))
        canteens.append(Canteen(c['id'], c['name'], c['city'], c['address'], c['coordinates']))

    return canteens


def get_canteen(id_canteen: str) -> Canteen:
    """ Returns a canteen
    """

    c = send_request(url_canteen + f'/canteens/{id_canteen}')
    return Canteen(c['id'], c['name'], c['city'], c['address'], c['coordinates'])
