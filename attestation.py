import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter")
        self.root.geometry("750x550")
        self.root.resizable(False, False)

        # Получение API-ключа из переменных окружения или настроек
        self.api_key = self.get_api_key()
        
        # Базовый URL для API (используем эндпоинт /pair/ для прямых конвертаций)
        self.base_url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/pair/"
        
        # Доступные валюты
        self.currencies = ["USD", "EUR", "RUB", "GBP", "JPY", "CNY", "TRY", "KZT", "UAH", "CHF", "CAD", "AUD"]

        # Загрузка истории
        self.history = self.load_history()

        # Создание GUI
        self.create_widgets()
        self.update_history_table()

    def get_api_key(self):
        """Получение API-ключа из различных источников"""
        # Приоритет: переменная окружения > файл .env > запрос у пользователя
        api_key = os.getenv('EXCHANGE_RATE_API_KEY')
        
        if not api_key:
            # Пытаемся прочитать из config.json
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                    api_key = config.get('api_key', '')
            except FileNotFoundError:
                pass
        
        if not api_key:
            # Запрашиваем у пользователя при первом запуске
            api_key = self.ask_for_api_key()
        
        return api_key

    def ask_for_api_key(self):
        """Диалог для ввода API-ключа"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Настройка API ключа")
        dialog.geometry("500x250")
        dialog.resizable(False, False)
        
        tk.Label(dialog, text="Для работы конвертера валют необходим API ключ", 
                font=("Arial", 10, "bold")).pack(pady=10)
        tk.Label(dialog, text="Получите бесплатный ключ на:\nhttps://www.exchangerate-api.com", 
                fg="blue", cursor="hand2").pack(pady=5)
        tk.Label(dialog, text="Введите ваш API ключ:").pack(pady=5)
        
        api_key_entry = tk.Entry(dialog, width=40, show="*")
        api_key_entry.pack(pady=5)
        
        result = []
        
        def save_key():
            key = api_key_entry.get().strip()
            if key:
                # Сохраняем в config.json
                with open('config.json', 'w') as f:
                    json.dump({'api_key': key}, f)
                result.append(key)
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", "API ключ не может быть пустым")
        
        tk.Button(dialog, text="Сохранить и продолжить", command=save_key, 
                 bg="#4CAF50", fg="white").pack(pady=10)
        
        self.root.wait_window(dialog)
        
        if result:
            return result[0]
        else:
            messagebox.showerror("Ошибка", "API ключ не был предоставлен")
            self.root.quit()
            return ""

    def create_widgets(self):
        # Рамка конвертации
        convert_frame = tk.LabelFrame(self.root, text="Конвертация", padx=10, pady=10)
        convert_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(convert_frame, text="Сумма:").grid(row=0, column=0, sticky="w")
        self.amount_entry = tk.Entry(convert_frame, width=15)
        self.amount_entry.grid(row=0, column=1, padx=5)

        tk.Label(convert_frame, text="Из валюты:").grid(row=0, column=2, sticky="w", padx=(20,0))
        self.from_currency = ttk.Combobox(convert_frame, values=self.currencies, width=7)
        self.from_currency.set("USD")
        self.from_currency.grid(row=0, column=3, padx=5)

        tk.Label(convert_frame, text="В валюту:").grid(row=0, column=4, sticky="w", padx=(20,0))
        self.to_currency = ttk.Combobox(convert_frame, values=self.currencies, width=7)
        self.to_currency.set("EUR")
        self.to_currency.grid(row=0, column=5, padx=5)

        self.convert_btn = tk.Button(convert_frame, text="Конвертировать", command=self.convert)
        self.convert_btn.grid(row=0, column=6, padx=20)

        self.result_label = tk.Label(convert_frame, text="", fg="blue", font=("Arial", 10, "bold"))
        self.result_label.grid(row=1, column=0, columnspan=7, pady=10)
        
        # Статус бар для отображения ошибок
        self.status_bar = tk.Label(self.root, text="Готов к работе", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Рамка истории
        history_frame = tk.LabelFrame(self.root, text="История конвертаций", padx=10, pady=10)
        history_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("Дата", "Сумма", "Из", "В", "Результат", "Курс")
        self.tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=12)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100 if col != "Дата" else 140)

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Кнопки управления
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=(0,10))

        tk.Button(btn_frame, text="Очистить историю", command=self.clear_history, bg="#ffcccc").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Проверить API ключ", command=self.check_api_key, bg="#ffffcc").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Сохранить и выйти", command=self.save_and_exit, bg="#ccffcc").pack(side="right", padx=5)

    def get_exchange_rate(self, from_curr, to_curr):
        """Получение курса из API с использованием эндпоинта /pair/"""
        try:
            # Используем прямой эндпоинт для конвертации
            url = f"{self.base_url}{from_curr}/{to_curr}"
            
            response = requests.get(url, timeout=10)
            data = response.json()
            
            # Проверка ответа API
            if data.get("result") == "success":
                rate = data.get("conversion_rate")
                if rate:
                    self.status_bar.config(text=f"Курс получен: 1 {from_curr} = {rate:.4f} {to_curr}")
                    return rate
                else:
                    self.status_bar.config(text="Ошибка: курс не найден в ответе API")
                    return None
            else:
                # Обработка различных ошибок API
                error_type = data.get("error-type", "unknown")
                error_messages = {
                    "invalid-key": "Неверный API ключ. Проверьте ключ в config.json",
                    "inactive-account": "API аккаунт неактивен",
                    "quota-reached": "Превышен лимит запросов (1500/месяц)",
                    "unsupported-code": f"Валюта {from_curr} или {to_curr} не поддерживается"
                }
                error_msg = error_messages.get(error_type, f"Ошибка API: {error_type}")
                messagebox.showerror("Ошибка API", error_msg)
                self.status_bar.config(text=error_msg)
                return None
                
        except requests.exceptions.Timeout:
            messagebox.showerror("Ошибка", "Превышено время ожидания ответа от API")
            self.status_bar.config(text="Таймаут соединения")
            return None
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Ошибка", "Нет соединения с интернетом")
            self.status_bar.config(text="Нет интернет соединения")
            return None
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {str(e)}")
            self.status_bar.config(text=f"Ошибка: {str(e)[:50]}")
            return None

    def check_api_key(self):
        """Проверка валидности API ключа"""
        self.status_bar.config(text="Проверка API ключа...")
        
        # Простая проверка: запрос к API
        test_url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest/USD"
        try:
            response = requests.get(test_url, timeout=10)
            data = response.json()
            
            if data.get("result") == "success":
                messagebox.showinfo("Успех", "API ключ работает корректно!")
                self.status_bar.config(text="API ключ валиден")
            else:
                error_type = data.get("error-type", "unknown")
                messagebox.showerror("Ошибка", f"API ключ недействителен. Причина: {error_type}")
                self.status_bar.config(text="API ключ недействителен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось проверить ключ: {str(e)}")
            self.status_bar.config(text="Ошибка проверки ключа")

    def convert(self):
        """Основная логика конвертации"""
        amount_str = self.amount_entry.get().strip()

        # Проверка ввода
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Сумма должна быть положительным числом")
            self.status_bar.config(text="Ошибка: некорректная сумма")
            return

        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()

        self.status_bar.config(text=f"Конвертация {amount} {from_curr} → {to_curr}...")

        if from_curr == to_curr:
            result = amount
            rate = 1.0
            self.status_bar.config(text="Валюты совпадают, курс = 1.0000")
        else:
            rate = self.get_exchange_rate(from_curr, to_curr)
            if rate is None:
                return
            result = amount * rate

        # Отображение результата
        result_text = f"{amount:.2f} {from_curr} = {result:.2f} {to_curr} (курс: {rate:.4f})"
        self.result_label.config(text=result_text)
        self.status_bar.config(text=f"✓ Конвертация завершена: {result_text[:60]}")

        # Сохранение в историю
        self.add_to_history(
            amount=amount,
            from_curr=from_curr,
            to_curr=to_curr,
            result=result,
            rate=rate
        )

    def add_to_history(self, amount, from_curr, to_curr, result, rate):
        """Добавление записи в историю"""
        record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "from": from_curr,
            "to": to_curr,
            "result": round(result, 2),
            "rate": round(rate, 4)
        }
        self.history.append(record)
        self.save_history()
        self.update_history_table()

    def update_history_table(self):
        """Обновление таблицы истории"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for record in reversed(self.history[-20:]):
            self.tree.insert("", "end", values=(
                record["date"],
                f"{record['amount']:.2f}",
                record["from"],
                record["to"],
                f"{record['result']:.2f}",
                f"{record['rate']:.4f}"
            ))

    def load_history(self):
        """Загрузка истории из JSON"""
        try:
            with open("history.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_history(self):
        """Сохранение истории в JSON"""
        with open("history.json", "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=4, ensure_ascii=False)

    def clear_history(self):
        """Очистка всей истории"""
        if messagebox.askyesno("Подтверждение", "Очистить всю историю?"):
            self.history = []
            self.save_history()
            self.update_history_table()
            self.status_bar.config(text="История очищена")
            messagebox.showinfo("Готово", "История очищена")

    def save_and_exit(self):
        """Сохранение и выход"""
        self.save_history()
        self.status_bar.config(text="Данные сохранены, выход...")
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()
