from datetime import date
from typing import Optional, List, Tuple, Union
import requests

url_canteens_dresden = 'https://api.studentenwerk-dresden.de/openmensa/v2'
Coordinate = Tuple[float, float]
Radius = Tuple[Coordinate, float]


def send_request(url: str, params: Optional[dict] = None) -> dict:
    """Sends requests to the url with parameters and returns the response."""
    print(f'Sending request to {url}')
    response = requests.get(url, params)
    response.encoding = 'UTF-8'
    return response.json()


def get_canteens(near: Optional[Radius] = None,
                 ids: Optional[List[str]] = None,
                 has_coordinates: Optional[bool] = None) -> dict:
    """
    Returns a list of canteens

    :param near: ((lat, long), dist) Used to list only canteens within a distance from a point.
    :param ids: [id1, id2, ...] Return only canteens with these ids.
    :param has_coordinates: Return only canteens with coordinates

    :return: A dict with all canteens [{id: str, name: str, city: str, address: str, coordinates: [lat, long]}]
    """

    # TODO check arguments
    params = {}
    # add arguments to the params
    if near is not None and near[0] is not None and near[1] is not None and None not in near[0]:
        params.update({
                'near[lat]': near[0][0],
                'near[long]': near[0][1],
                'near[dist]': near[1]
            })
    if ids is not None and None not in ids:
        params.update({
            'ids': ids
        })
    if has_coordinates is not None:
        params['hasCoordinates'] = has_coordinates

    # send request and return answer
    return send_request(url_canteens_dresden + '/canteens', params)


def get_days(id_canteen: str,
             day: Optional[str] = None,
             start: str = date.today().isoformat()) -> Union[list, dict]:
    """
    List days of a canteen. Useful to determine if a canteen is open or not.

    :param id_canteen: ID of the canteen
    :param day: Return only a single day of the date provided.
    :param start: Start day. Defaults to today
    :return:
    """

    # TODO check arguments
    # TODO allow canteen name and datetime objects

    url = url_canteens_dresden + f'/canteens/{id_canteen}/days'
    if day is None:
        return send_request(url, {'start': start})
    else:
        return send_request(url + f'/{day}')


def get_meals(id_canteen: str, day: str, id_meal: Optional[str] = None):
    """
    Returns the available meals on a certain day in a canteen.

    :param id_canteen: ID of the canteen
    :param day: the day to be searched for meals
    :param id_meal: ID of a meal to be returned
    """

    # TODO check arguments

    url = url_canteens_dresden + f'/canteens/{id_canteen}/days/{day}/meals'

    if id_meal is None:
        return send_request(url)
    else:
        return send_request(url + f'/{id_meal}')

# TODO maybe add a class for canteens?

