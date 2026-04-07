import os
import shutil
import subprocess

def run_command(command, ignore_errors=False):
    """Выполняет команду в консоли."""
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            print(f"\n❌ Ошибка при выполнении: {command}")
            print(e)
            return False
    return True

def fix_invalid_grant():
    """Исправляет Ошибку 2 (invalid_grant) удаляя сломанный кэш токенов."""
    print("\n🛠 Лечим ошибку 'invalid_grant' (Протухший токен)...")
    
    # DVC хранит кэш авторизации Google Drive в этой папке
    gdrive_cache_dir = os.path.join(".dvc", "tmp", "gdrive")
    
    if os.path.exists(gdrive_cache_dir):
        try:
            shutil.rmtree(gdrive_cache_dir)
            print("✅ Сломанный кэш авторизации удален.")
            print("👉 Теперь запустите 'dvc pull'. Откроется браузер для новой авторизации в Google.")
        except Exception as e:
            print(f"❌ Не удалось удалить папку кэша: {e}")
    else:
        print("✅ Кэш авторизации чист (папка не найдена).")
        print("Попробуйте сделать 'dvc pull' еще раз.")

def fix_folder_id():
    """Исправляет Ошибку 1 (404 File Not Found) меняя ID папки."""
    print("\n🛠 Лечим ошибку '404 File not found' (Смена ID папки)...")
    
    # Пытаемся получить имя remote (обычно 'storage')
    try:
        result = subprocess.run("dvc remote list", shell=True, capture_output=True, text=True)
        remotes = result.stdout.strip().split('\n')
        if not remotes or not remotes[0]:
            print("❌ DVC remotes не найдены в проекте.")
            return
        
        # Берем первый remote (обычно он один)
        remote_name = remotes[0].split()[0]
        current_url = remotes[0].split()[1]
        
        print(f"Текущий удаленный репозиторий: [{remote_name}]")
        print(f"Текущий URL (ID папки): {current_url}")
        
    except Exception:
        remote_name = "storage"
        print("Не удалось автоматически определить remote, используем 'storage'.")

    new_id = input("\nВведите новый ID папки Google Drive (или нажмите Enter для отмены): ").strip()
    
    if new_id:
        # Меняем URL в основном конфиге
        command = f"dvc remote modify {remote_name} url gdrive://{new_id}"
        if run_command(command):
            print(f"✅ ID папки успешно обновлен!")
            print(f"⚠️ Не забудьте закоммитить изменения в файле .dvc/config: git add .dvc/config && git commit -m 'Update DVC gdrive folder ID'")
    else:
        print("Отмена.")

def check_gdrive_extension():
    """Проверяет, установлена ли библиотека для работы DVC с Google Drive."""
    print("\n🔍 Проверка зависимостей DVC...")
    try:
        import dvc_gdrive
        print("✅ Плагин dvc-gdrive установлен.")
    except ImportError:
        print("❌ Плагин dvc-gdrive НЕ установлен!")
        choice = input("Установить сейчас? (y/n): ")
        if choice.lower() == 'y':
            run_command("pip install dvc[gdrive]")
            print("✅ Установка завершена.")

def main_menu():
    while True:
        print("\n" + "="*40)
        print("🚀 DVC Fixer - Помощник для Google Drive")
        print("="*40)
        print("1. Исправить ошибку авторизации (invalid_grant / Зависший токен)")
        print("2. Изменить ID папки Google Drive (Ошибка 404 File not found)")
        print("3. Проверить/Установить зависимости (dvc-gdrive)")
        print("4. Проверить статус DVC (dvc status)")
        print("0. Выход")
        print("="*40)
        
        choice = input("Выберите действие: ").strip()
        
        if choice == '1':
            fix_invalid_grant()
        elif choice == '2':
            fix_folder_id()
        elif choice == '3':
            check_gdrive_extension()
        elif choice == '4':
            print("\nВыполняю 'dvc status'...")
            run_command("dvc status", ignore_errors=True)
        elif choice == '0':
            print("Выход...")
            break
        else:
            print("❌ Неверный выбор.")

if __name__ == "__main__":
    # Проверка, что скрипт запущен в корне проекта с DVC
    if not os.path.exists(".dvc"):
        print("❌ Ошибка: Папка .dvc не найдена!")
        print("Пожалуйста, запустите этот скрипт из корня вашего проекта.")
    else:
        main_menu()