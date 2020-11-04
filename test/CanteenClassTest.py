from datetime import date
import unittest
from src.modules import openmensa


class TestCanteenClass(unittest.TestCase):
    def setUp(self) -> None:
        self.params = {
            'id': '1',
            'name': 'Mentastisch',
            'city': 'Musterhausen',
            'address': 'Am Musterweg 1',
            'coordinates': (15.4212, 30.32435)
        }

    def test_constructor(self):
        c0 = openmensa.Canteen(self.params['id'], self.params['name'])
        c1 = openmensa.Canteen(self.params['id'], self.params['name'],
                               city=self.params['city'], address=self.params['address'])
        c2 = openmensa.Canteen(self.params['id'], self.params['name'],
                               coordinates=self.params['coordinates'])

        canteens = [c0, c1, c2]

        for ci in canteens:
            with self.subTest(ci=ci):
                self.assertEqual(ci.id, self.params['id'], 'ID is not set correctly')
                self.assertEqual(ci.name, self.params['name'], 'Name is not set correctly')
                self.assertEqual(ci, c0, 'Canteens must be equal if the id is equal')

        self.assertEqual(c1.city, self.params['city'])
        self.assertEqual(c1.address, self.params['address'])
        self.assertEqual(c2.coordinates, self.params['coordinates'])

    def test_constructor_illegal_args(self):
        for key in self.params.keys():
            params = self.params.copy()
            params[key] = ''
            if key == 'coordinates':
                break
            with self.subTest(params=params):
                self.assertRaises(ValueError, openmensa.Canteen,
                                  params['id'], params['name'],
                                  params['city'], params['address'], params['coordinates'])


if __name__ == '__main__':
    unittest.main()
