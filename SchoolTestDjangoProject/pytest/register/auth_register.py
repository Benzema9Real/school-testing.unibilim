import requests


def test_auth_register():
    url = 'https://school-testing.unibilim.kg/auth/register/'

    data = {
        "name": "Test User",
        "phone_number": "Введите номер",
        "school": 1,
        "class_number": 11,
        "class_letter": 'A',
    }

    response = requests.post(url, json=data)

    if response.status_code == 201:
        print("Пользователь успешно зарегистрирован.")
        print("Ответ сервера:", response.json())
    elif response.status_code == 400:
        print("Ошибка: Неверные данные регистрации.")
        print("Ответ сервера:", response.json())
    else:
        print(f"Произошла ошибка: {response.status_code}")


test_auth_register()
