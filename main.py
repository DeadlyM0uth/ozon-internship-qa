import requests


def get_tallest_hero(gender, has_work):
    response = requests.get(
        "https://akabab.github.io/superhero-api/api/all.json",
        timeout=10,
    )
    response.raise_for_status()
    heroes = response.json()

    tallest_hero = None
    max_height = 0

    for hero in heroes:
        if hero["appearance"]["gender"].lower() != gender.lower():
            continue

        occupation = hero["work"]["occupation"]
        hero_has_work = occupation != "-"

        if hero_has_work != has_work:
            continue

        height_text = hero["appearance"]["height"][1]
        if not height_text.endswith("cm"):
            continue

        height = int(height_text.replace("cm", "").strip())

        if height > max_height:
            max_height = height
            tallest_hero = hero

    return tallest_hero


if __name__ == "__main__":
    hero = get_tallest_hero("Male", True)
    print(hero["name"])
