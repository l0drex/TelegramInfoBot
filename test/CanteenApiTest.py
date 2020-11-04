import unittest
from datetime import date
from src.modules import openmensa


class TestCanteenApi(unittest.TestCase):
    def setUp(self) -> None:
        self.canteen = openmensa.get_canteens()[0]

    def test_send_request(self):
        self.assertEqual(openmensa.send_request(openmensa.url_canteen)['api'], 'OpenMensa API Version 2')

    def test_get_canteens(self):
        # no arguments
        canteens = openmensa.get_canteens()
        self.assertIsNotNone(canteens)

        for c in canteens:
            self.assertIsInstance(c, openmensa.Canteen)

    def test_get_canteen(self):
        self.assertEqual(openmensa.get_canteen(self.canteen.id), openmensa.get_canteens(ids=[self.canteen.id])[0])

    def test_get_days(self):
        self.assertIsInstance(self.canteen.get_days(), list)
        self.assertIsInstance(self.canteen.get_days(day=date.today()), dict)

    def test_get_day(self):
        self.assertEqual(self.canteen.get_day(date.today()), self.canteen.get_days(day=date.today()))

    def test_get_meals(self):
        self.assertIsInstance(self.canteen.get_meals(date.fromisoformat(self.canteen.get_days()[0]['date'])), list)

    def test_get_meal(self):
        day = date.fromisoformat(self.canteen.get_days()[0]['date'])
        meal = self.canteen.get_meals(day)[0]
        self.assertEqual(self.canteen.get_meal(day, meal['id']), meal)


if __name__ == '__main__':
    unittest.main()
