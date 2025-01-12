import requests


def test_school():
    url = 'https://school-testing.unibilim.kg/school/'

    response = requests.get(url)

    if response.status_code == 200:
        print("Успешно получен список школ.")
        print("Ответ сервера:", response.json())
    else:
        print(f"Произошла ошибка: HTTP {response.status_code}")
        print("Ответ сервера:", response.text)


test_school()
