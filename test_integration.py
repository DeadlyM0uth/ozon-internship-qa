import os
import unittest

from main import get_tallest_hero


@unittest.skipUnless(
    os.getenv("RUN_INTEGRATION_TESTS") == "1",
    "Integration tests are disabled",
)
class GetTallestHeroIntegrationTests(unittest.TestCase):
    # Проверяет работу функции с настоящим API
    def test_gets_tallest_employed_male_from_real_api(self):
        hero = get_tallest_hero("Male", True)

        self.assertIsNotNone(hero)
        self.assertIsInstance(hero, dict)

        self.assertIn("name", hero)
        self.assertIn("appearance", hero)
        self.assertIn("work", hero)

        self.assertEqual(hero["appearance"]["gender"].lower(), "male")
        self.assertNotEqual(hero["work"]["occupation"], "-")

        height = hero["appearance"]["height"][1]
        self.assertTrue(height.endswith("cm"))
        self.assertGreater(int(height.removesuffix("cm").strip()), 0)


if __name__ == "__main__":
    unittest.main()
