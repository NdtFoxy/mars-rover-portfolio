import os
import subprocess

def run_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка при выполнении: {command}")
        print("Убедитесь, что вы установили плагин S3: pip install dvc[s3]")
        exit(1)

print("🚀 Настройка DVC (Backblaze S3) для команды")
print("-" * 40)

# Проверяем плагин S3
print("1. Проверка установки dvc[s3]...")
try:
    import dvc_s3
    print("✅ Плагин dvc-s3 установлен.")
except ImportError:
    print("⏳ Установка плагина dvc-s3...")
    run_command("pip install dvc[s3]")

# Запрашиваем секретный ключ
print("\n2. Настройка доступа...")
secret_key = input("🔑 Вставьте секретный ключ (applicationKey), который скинул Никита: ").strip()

if not secret_key:
    print("❌ Вы не ввели ключ! Настройка прервана.")
    exit(1)

# Применяем настройки локально (ID открыт, это безопасно)
print("⏳ Применяю ключи...")
run_command(f"dvc remote modify --local s3remote access_key_id '003877efa29c5110000000001'")
run_command(f"dvc remote modify --local s3remote secret_access_key '{secret_key}'")

print("\n🎉 ГОТОВО! DVC успешно подключен к Backblaze S3.")
print("👉 Теперь просто напишите в терминале: dvc pull")