import unittest
from unittest.mock import Mock, patch

import requests

from main import get_tallest_hero


API_URL = "https://akabab.github.io/superhero-api/api/all.json"


def make_hero(name="Hero", *, gender="Male", occupation="Developer", height="180 cm"):
    # Создаёт минимальные данные героя для тестов
    return {
        "name": name,
        "appearance": {"gender": gender, "height": ["5'11", height]},
        "work": {"occupation": occupation},
    }


class GetTallestHeroTests(unittest.TestCase):
    def setUp(self):
        self.response = Mock()
        get_patcher = patch("main.requests.get", return_value=self.response)
        self.mocked_get = get_patcher.start()
        self.addCleanup(get_patcher.stop)

    def set_heroes(self, *heroes):
        self.response.json.return_value = list(heroes)

    # Проверяет адрес API и таймаут запроса
    def test_requests_expected_url_and_timeout(self):
        self.set_heroes()
        get_tallest_hero("Male", True)
        self.mocked_get.assert_called_once_with(API_URL, timeout=10)

    # Проверяет обработку HTTP-статуса
    def test_checks_http_status(self):
        self.set_heroes()
        get_tallest_hero("Male", True)
        self.response.raise_for_status.assert_called_once_with()

    # Проверяет ошибку HTTP
    def test_propagates_http_error_and_does_not_read_json(self):
        error = requests.HTTPError("500 Server Error")
        self.response.raise_for_status.side_effect = error
        with self.assertRaises(requests.HTTPError) as raised:
            get_tallest_hero("Male", True)
        self.assertIs(raised.exception, error)
        self.response.json.assert_not_called()

    # Проверяет ошибку сети
    def test_propagates_network_error(self):
        error = requests.Timeout("request timed out")
        self.mocked_get.side_effect = error
        with self.assertRaises(requests.Timeout) as raised:
            get_tallest_hero("Male", True)
        self.assertIs(raised.exception, error)

    # Проверяет выбор самого высокого героя
    def test_returns_tallest_matching_hero(self):
        heroes = [
            make_hero("Short", height="170 cm"),
            make_hero("Tall", height="205 cm"),
            make_hero("Medium", height="190 cm"),
        ]
        self.set_heroes(*heroes)
        self.assertIs(get_tallest_hero("Male", True), heroes[1])

    # Проверяет, что регистр пола не важен
    def test_gender_comparison_is_case_insensitive(self):
        cases = [("male", "Male"), ("MALE", "male"), ("Female", "FEMALE")]
        for requested_gender, stored_gender in cases:
            with self.subTest(requested_gender=requested_gender, stored_gender=stored_gender):
                hero = make_hero(gender=stored_gender)
                self.set_heroes(hero)
                self.assertIs(get_tallest_hero(requested_gender, True), hero)

    # Проверяет исключение героев другого пола
    def test_ignores_heroes_of_other_gender(self):
        matching = make_hero("Matching", gender="Female", height="170 cm")
        self.set_heroes(
            make_hero("Wrong gender", gender="Male", height="250 cm"), matching
        )
        self.assertIs(get_tallest_hero("Female", True), matching)

    # Проверяет фильтр по наличию работы
    def test_filters_by_work_using_dash_as_no_work_marker(self):
        cases = [
            ("Developer", True, True),
            ("", True, True),
            ("-", True, False),
            ("-", False, True),
            ("Developer", False, False),
            ("", False, False),
        ]
        for occupation, has_work, expected in cases:
            with self.subTest(occupation=occupation, has_work=has_work):
                hero = make_hero(occupation=occupation)
                self.set_heroes(hero)
                self.assertEqual(get_tallest_hero(
                    "Male", has_work) is hero, expected)

    # Проверяет пропуск неподдерживаемого роста
    def test_ignores_unsupported_height_values(self):
        for height in ["6 ft", "unknown", "180 CM", "180cm "]:
            with self.subTest(height=height):
                self.set_heroes(make_hero(height=height))
                self.assertIsNone(get_tallest_hero("Male", True))

    # Проверяет допустимые форматы роста в сантиметрах
    def test_accepts_integer_centimeter_formats(self):
        for height in ["180 cm", "180cm", " 180 cm", "+180 cm", "00180 cm"]:
            with self.subTest(height=height):
                hero = make_hero(height=height)
                self.set_heroes(hero)
                self.assertIs(get_tallest_hero("Male", True), hero)

    # Проверяет пустой ответ API
    def test_returns_none_for_empty_response(self):
        self.set_heroes()
        self.assertIsNone(get_tallest_hero("Male", True))

    # Проверяет случай, когда подходящего героя нет
    def test_returns_none_when_nothing_matches(self):
        self.set_heroes(
            make_hero(gender="Female"),
            make_hero(occupation="-"),
            make_hero(height="unknown"),
        )
        self.assertIsNone(get_tallest_hero("Male", True))

    # Проверяет выбор первого героя при одинаковом росте
    def test_keeps_first_hero_when_maximum_heights_are_equal(self):
        first = make_hero("First", height="200 cm")
        second = make_hero("Second", height="200 cm")
        self.set_heroes(first, second)
        self.assertIs(get_tallest_hero("Male", True), first)

    # Проверяет нулевой и отрицательный рост
    def test_non_positive_height_cannot_replace_initial_maximum(self):
        for height in ["0 cm", "-10 cm"]:
            with self.subTest(height=height):
                self.set_heroes(make_hero(height=height))
                self.assertIsNone(get_tallest_hero("Male", True))

    # Проверяет ошибку при некорректном числе в росте
    def test_invalid_centimeter_number_raises_value_error(self):
        for height in ["tall cm", "180.5 cm", " cm", "cm"]:
            with self.subTest(height=height):
                self.set_heroes(make_hero(height=height))
                with self.assertRaises(ValueError):
                    get_tallest_hero("Male", True)

    # Проверяет ошибку при отсутствии нужных полей
    def test_malformed_hero_data_raises_key_error(self):
        malformed_heroes = [
            {},
            {"appearance": {}},
            {"appearance": {"gender": "Male"}, "work": {}},
        ]
        for hero in malformed_heroes:
            with self.subTest(hero=hero):
                self.set_heroes(hero)
                with self.assertRaises(KeyError):
                    get_tallest_hero("Male", True)


if __name__ == "__main__":
    unittest.main()
