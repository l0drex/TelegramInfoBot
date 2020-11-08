import unittest
from datetime import date
from main import urls
from src.modules import openmensa

openmensa.url_canteen = urls['mensa']


class TestCanteenApi(unittest.TestCase):
    def setUp(self) -> None:
        self.canteen = openmensa.get_canteens()[0]

    def test_send_request(self):
        self.assertEqual(openmensa.send_request(openmensa.url_canteen)['api'], 'OpenMensa API Version 2')

    def test_get_canteens(self):
        canteens_list = [
            openmensa.get_canteens(),
            openmensa.get_canteens(ids=[self.canteen.id]),
            openmensa.get_canteens(has_coordinates=True),
            openmensa.get_canteens(has_coordinates=False),
            openmensa.get_canteens(near=((51.0288, 13.72994), 4)),
        ]

        for canteens in canteens_list:
            with self.subTest(canteens=canteens):
                self.assertIsNotNone(canteens, 'get_canteens should return a list')
                for c in canteens:
                    self.assertIsInstance(c, openmensa.Canteen,
                                          'The List returned by get_canteens should only contain canteens')

        for c in canteens_list[2]:
            self.assertTrue(c.has_coordinates(),
                            'All canteens returned with param hasCoordinates set to true should have coordinates')

    def test_get_canteen(self):
        self.assertEqual(openmensa.get_canteen(self.canteen.id), self.canteen)

    def test_get_days(self):
        days = self.canteen.get_days()
        self.assertIsInstance(days, list)

        for i in range(len(days)):
            d = days[i]
            self.assertIsInstance(d['date'], date, 'Entry date should be of type datetime.date')
            self.assertIsInstance(d['closed'], bool, 'Entry closed should be of type bool')
            if i < len(days) - 1:
                self.assertTrue(d['date'] < days[i+1]['date'], 'The list should be sorted correctly')

        day = self.canteen.get_days(day=date.today())
        self.assertIsInstance(day['date'], date, 'Entry date should be of type datetime.date')
        self.assertIsInstance(day['closed'], bool, 'Entry closed should be of type bool')

    def test_get_day(self):
        self.assertEqual(self.canteen.get_day(date.today()), self.canteen.get_days(day=date.today()))

    def test_get_next_day_opened(self):
        day = self.canteen.get_next_day_opened()
        self.assertFalse(self.canteen.get_day(day)['closed'])
        self.assertTrue(day > date.today(), 'The next day opened should not be before today')

    def test_get_meals(self):
        meals = self.canteen.get_meals(self.canteen.get_days()[0]['date'])
        self.assertIsInstance(meals, list, 'get_meals should return a list')

        keys = ['id', 'name', 'notes', 'prices', 'category']
        prices = ['Studierende', 'Bedienstete']

        for m in meals:
            self.assertIsInstance(m, dict)

            for k in keys:
                self.assertTrue(k in m.keys(), f'Every meal should have a {k}')

            self.assertIsInstance(m['notes'], list, 'Notes should be a list')
            self.assertIsInstance(m['prices'], dict, 'Prices should be a dict')

            for p in prices:
                self.assertTrue(p in m['prices'], f'Prices should contain {p}')

            self.assertTrue(m['image'].startswith('https://'), 'The url of the image is malformed.')

    def test_get_meal(self):
        day = self.canteen.get_days()[0]['date']
        meal = self.canteen.get_meals(day)[0]
        self.assertEqual(self.canteen.get_meal(day, meal['id']), meal)


if __name__ == '__main__':
    unittest.main()
