import csv
import os

# Функция для записи конфигурации в файл
def write_to_file(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.writelines(data)
    except IOError as e:
        print(f"Ошибка при записи в файл {filename}: {e}")

# Функция для чтения CSV-файла и генерации конфигурации
def generate_configuration(csv_filename):
    users_configs = ["""
#include users_template.conf

"""]
    operator_members = []  # Список операторов для добавления в queue_operators.conf
    extension_configs = []  # Новый список для хранения конфигураций расширения для каждого пользователя

    try:
        with open(csv_filename, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)

            for row in reader:
                department = row['department']
                full_name = row['fio']
                phone_number = row['phone']
                username = row['user']
                password = row['password']

                # Формируем конфигурацию для каждого пользователя
                config = f"""
; Пользователь: {full_name}, Отдел: {department}, Телефон: {phone_number}

[{username}](internal-endpoint)
auth={username}
aors={username}

[{username}](internal-auth)
username={username}
password={password}

[{username}](internal-aor)
"""

                users_configs.append(config)

                if department == 'operators':
                    operator_members.append(f"member => PJSIP/{username}\n")

                # Генерируем конфигурацию для extensions.conf
                # Добавление комментария перед строками конфигурации
                extension_config = f"""
; Пользователь: {full_name}, Отдел: {department}, Телефон: {phone_number}
exten => {phone_number},1,Dial(PJSIP/{username})
same => n,Hangup()
"""
                extension_configs.append(extension_config)

    except IOError as e:
        print(f"Ошибка при чтении файла {csv_filename}: {e}")

    return users_configs, operator_members, extension_configs

# Основная программа
if __name__ == '__main__':
    # Убедимся, что выходные файлы существуют
    output_files = ['users.conf', 'members_operators.conf', 'users_extensions.conf']
    for filename in output_files:
        if not os.path.exists(filename):
            with open(filename, 'w'):
                pass  # Создаем пустой файл

    # Генерация конфигурации
    users_configs, operator_members, extension_configs = generate_configuration('users.csv')

    # Запись в файлы
    write_to_file('users.conf', users_configs)
    write_to_file('members_operators.conf', operator_members)
    write_to_file('users_extensions.conf', extension_configs)