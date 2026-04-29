import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from datetime import datetime

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter")
        self.root.geometry("700x500")
        self.root.resizable(False, False)

        
        # Доступные валюты (основные)
        self.currencies = ["USD", "EUR", "RUB", "GBP", "JPY", "CNY", "TRY", "KZT", "UAH"]

        # Загрузка истории
        self.history = self.load_history()

        # Создание GUI
        self.create_widgets()
        self.update_history_table()

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

        # Кнопки управления историей
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=(0,10))

        tk.Button(btn_frame, text="Очистить историю", command=self.clear_history, bg="#ffcccc").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Сохранить и выйти", command=self.save_and_exit, bg="#ccffcc").pack(side="right", padx=5)

    def get_exchange_rate(self, from_curr, to_curr):
        """Получение курса из API"""
        try:
            url = self.base_url + from_curr
            response = requests.get(url, timeout=10)
            data = response.json()

            if data["result"] == "success":
                return data["conversion_rates"].get(to_curr)
            else:
                messagebox.showerror("Ошибка API", "Не удалось получить курс")
                return None
        except Exception as e:
            messagebox.showerror("Ошибка соединения", f"Проверьте интернет: {str(e)}")
            return None

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
            return

        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()

        if from_curr == to_curr:
            result = amount
            rate = 1.0
        else:
            rate = self.get_exchange_rate(from_curr, to_curr)
            if rate is None:
                return
            result = amount * rate

        # Отображение результата
        result_text = f"{amount:.2f} {from_curr} = {result:.2f} {to_curr} (курс: {rate:.4f})"
        self.result_label.config(text=result_text)

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

        for record in reversed(self.history[-20:]):  # Показываем последние 20 записей
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
            messagebox.showinfo("Готово", "История очищена")

    def save_and_exit(self):
        """Сохранение и выход"""
        self.save_history()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()