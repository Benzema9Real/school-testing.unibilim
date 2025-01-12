import requests


def test_users_all():
    url = 'https://school-testing.unibilim.kg/user/all/'

    response = requests.get(url)

    if response.status_code == 200:
        print("Успешно получен список Пользователей.")
        print("Ответ сервера:", response.json())
    else:
        print(f"Произошла ошибка: HTTP {response.status_code}")
        print("Ответ сервера:", response.text)


test_users_all()
