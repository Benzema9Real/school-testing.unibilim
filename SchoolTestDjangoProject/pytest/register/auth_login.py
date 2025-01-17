import requests


def test_auth_login():
    url = 'https://school-testing.unibilim.kg/auth/login/'

    data = {
        "phone_number": "+996704444501"
    }

    response = requests.post(url, json=data)


    if response.status_code == 200:
        print("Успешный вход.")
        print("Ответ сервера:", response.json())
    elif response.status_code == 400:
        print("Ошибка: Неверные данные для входа.")
        print("Ответ сервера:", response.json())
    elif response.status_code == 401:
        print("Ошибка аутентификации: Неверное имя или номер телефона.")
    else:
        print(f"Произошла ошибка: HTTP {response.status_code}")
        print("Ответ сервера:", response.text)


test_auth_login()
