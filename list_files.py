import os

# Запрашиваем адрес папки у пользователя
folder_path = input("Введите адрес папки: ")

# Проверяем, существует ли папка
if not os.path.isdir(folder_path):
    print("Указанная папка не существует.")
else:
    # Список для хранения имен файлов
    files_list = []

    # Рекурсивный обход папки и сбор всех файлов
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # Получаем полный путь к файлу
            full_path = os.path.join(root, file)
            files_list.append(full_path)

    # Сохраняем список файлов в verzeichnis.txt
    with open("verzeichnis.txt", "w", encoding="utf-8") as f:
        for file_path in files_list:
            f.write(file_path + "\n")

    print(f"Список файлов сохранен в verzeichnis.txt. Всего найдено файлов: {len(files_list)}")
