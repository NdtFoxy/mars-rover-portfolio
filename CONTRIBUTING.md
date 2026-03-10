# 🛠 Правила работы с репозиторием (Git Flow)

---

## 📦 БЛОК 1: Правила именования (Ветки и Коммиты)

Все названия веток и коммитов пишем **на английском языке**.

### 1. Названия веток
Формат: `тип/краткое-описание-задачи`
* `feat/...` — для новой фичи (Пример: `feat/ue5-grid-setup`, `feat/agent-movement`)
* `fix/...` — для исправления бага (Пример: `fix/python-import-error`)
* `docs/...` — для документации/ридми (Пример: `docs/update-readme`)
* `refactor/...` — переписывание кода без добавления новых фич (Пример: `refactor/agent-class-structure`)

### 2. Сообщения коммитов (Conventional Commits)
Формат: `тип: описание того что сделано (с маленькой буквы)`
* `feat: add base agent class with coordinates`
* `fix: prevent agent from moving out of bounds`
* `chore: update gitignore for unreal engine`
* `docs: add contributing guidelines`

---


## 💻 Ежедневный рабочий процесс (Git)

Каждый раз, садясь за работу, выполняйте этот алгоритм в терминале:

```bash
# 1. Скачиваем последние обновления из главной ветки
git checkout main
git pull

# 2. Создаем СВОЮ ветку для работы
git checkout -b feat/название-моей-задачи

# ... ПИШИТЕ КОД ...

# 3. Сохраняем изменения
git add .
git commit -m "feat: краткое описание работы"

# 4. Отправляем ветку на сервер
git push origin feat/название-моей-задачи
```
*После этого зайдите на сайт Gitea, нажмите **New Pull Request** и попросите Тимлида (Никиту) проверить код.*

---

## 🗄️ Работа с тяжелой графикой (DVC Workflow)

Для Unreal Engine 5 мы используем **DVC (Data Version Control)**. Он хранит 3D-модели и текстуры на Google Drive, оставляя наш Git легким.

> 🛑 **КРИТИЧЕСКИ ВАЖНО ДЛЯ UNREAL ENGINE (АРТЕМ)**
> **ЗАПРЕЩЕНО** пушить временные папки UE5 (`Saved`, `Intermediate`, `DerivedDataCache`, `Binaries`). 
> **В Git идут:** `.uproject`, `Config`, `Source`.
> **В DVC идет:** Только папка `Content` (ассеты).

### 📥 Как СКАЧАТЬ ассеты (Всем)
Когда вы скачали код через `git pull`, тяжелых текстур там не будет. Чтобы их получить:
```bash
# Эта команда скачает все актуальные модели с Google Drive
dvc pull
```
*(Откроется браузер: выберите свой Google-аккаунт и нажмите "Разрешить").*

### 📤 Как ДОБАВИТЬ новые ассеты (Артему)
Если ты добавил новые модели в папку `Content`, делай так:
```bash
# 1. Добавляем папку в DVC (он сам спрячет файлы и добавит их в .gitignore)
dvc add frontend_ue/Content

# 2. Добавляем указатели DVC в Git
git add frontend_ue/Content.dvc .gitignore
git commit -m "feat: add new 3D models for mars surface"

# 3. Отправляем код Тимлиду, а графику — в Облако
git push origin feat/твоя-ветка
dvc push
```

---

## 🚑 Скорая помощь (Ошибки)

*   **Случайно начал писать в `main`:** Не делай commit! Напиши `git checkout -b feat/my-code` (изменения перенесутся).
*   **Git пишет CONFLICT при PR:** Вы с тиммейтом изменили одну строчку. Открой файл в VS Code