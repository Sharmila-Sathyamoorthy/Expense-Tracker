import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
from datetime import datetime
import csv

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# import other pages
from analytics import AnalyticsPage
from transactions import TransactionsPage

# ---------------- DATABASE ---------------- #
conn = sqlite3.connect("expenses.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    date TEXT,
    type TEXT,
    category TEXT,
    amount REAL,
    note TEXT
)
""")
conn.commit()

# ---------------- LOGIN ---------------- #
class Login:
    def __init__(self, root):
        self.root = root
        self.root.title("Login")
        self.root.geometry("300x200")

        tk.Label(root, text="Expense Tracker", font=("Segoe UI", 16, "bold")).pack(pady=20)
        tk.Label(root, text="Username").pack()

        self.entry = tk.Entry(root)
        self.entry.pack(pady=5)

        tk.Button(root, text="Login", command=self.login).pack(pady=10)

    def login(self):
        username = self.entry.get().strip()
        if not username:
            return
        self.root.destroy()
        root = tk.Tk()
        App(root, username)
        root.mainloop()

# ---------------- MAIN APP ---------------- #
class App:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.root.title("Expense Tracker Pro")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f5f6fa")

        self.create_layout()
        self.show_dashboard()

    def create_layout(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, bg="#2f3640", width=220)
        self.sidebar.pack(side="left", fill="y")

        tk.Label(
            self.sidebar,
            text="Expense Pro",
            fg="white",
            bg="#2f3640",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=30)

        ttk.Button(self.sidebar, text="Dashboard",
                   command=self.show_dashboard).pack(fill="x", padx=20, pady=5)

        ttk.Button(self.sidebar, text="Transactions",
                   command=self.show_transactions).pack(fill="x", padx=20, pady=5)

        ttk.Button(self.sidebar, text="Analytics",
                   command=self.show_analytics).pack(fill="x", padx=20, pady=5)

        # Page container
        self.container = tk.Frame(self.root, bg="#f5f6fa")
        self.container.pack(side="right", fill="both", expand=True)

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    # -------- Navigation -------- #
    def show_dashboard(self):
        self.clear_container()
        DashboardPage(self.container, self.username)

    def show_transactions(self):
        self.clear_container()
        TransactionsPage(self.container, self.username)

    def show_analytics(self):
        self.clear_container()
        AnalyticsPage(self.container, self.username)

# ---------------- DASHBOARD PAGE ---------------- #
class DashboardPage:
    def __init__(self, parent, username):
        self.parent = parent
        self.username = username
        self.build()

    def build(self):
        # Header
        tk.Label(
            self.parent,
            text="Dashboard",
            font=("Segoe UI", 22, "bold"),
            bg="#f5f6fa"
        ).pack(anchor="w", padx=30, pady=20)

        # KPI CARDS
        cards = tk.Frame(self.parent, bg="#f5f6fa")
        cards.pack(fill="x", padx=30)

        income, expense, balance, top_category = self.get_metrics()

        self.card(cards, "Total Income", f"₹ {income:.2f}", "#4cd137", 0)
        self.card(cards, "Total Expense", f"₹ {expense:.2f}", "#e84118", 1)
        self.card(cards, "Balance", f"₹ {balance:.2f}", "#273c75", 2)
        self.card(cards, "Top Category", top_category, "#8c7ae6", 3)

        # ACTION BAR
        action = tk.Frame(self.parent, bg="#f5f6fa")
        action.pack(fill="x", padx=30, pady=20)

        ttk.Button(
            action,
            text="Export Transactions (CSV)",
            command=self.export_csv
        ).pack(side="left")

        # PIE CHART BELOW CARDS
        chart_container = tk.Frame(self.parent, bg="white", bd=1, relief="solid")
        chart_container.pack(fill="both", expand=True, padx=30, pady=(10, 30))

        tk.Label(
            chart_container,
            text="Income vs Expense",
            font=("Segoe UI", 14, "bold"),
            bg="white"
        ).pack(anchor="w", padx=20, pady=10)

        self.draw_pie_chart(chart_container)

    # ---------- COMPONENTS ---------- #
    def card(self, parent, title, value, color, col):
        frame = tk.Frame(parent, bg=color, width=220, height=110)
        frame.grid(row=0, column=col, padx=10)
        frame.pack_propagate(False)

        tk.Label(frame, text=title, fg="white", bg=color,
                 font=("Segoe UI", 12)).pack(anchor="w", padx=12, pady=(18, 0))

        tk.Label(frame, text=value, fg="white", bg=color,
                 font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=12)

    # ---------- DATA ---------- #
    def get_metrics(self):
        month = datetime.today().strftime("%Y-%m")

        cur.execute("""
        SELECT type, category, SUM(amount)
        FROM transactions
        WHERE username=? AND date LIKE ?
        GROUP BY type, category
        """, (self.username, month + "%"))

        income = expense = 0
        categories = {}

        for t, cat, amt in cur.fetchall():
            if t == "Income":
                income += amt
            else:
                expense += amt
                categories[cat] = categories.get(cat, 0) + amt

        top_category = max(categories, key=categories.get) if categories else "—"
        return income, expense, income - expense, top_category

    # ---------- CSV EXPORT ---------- #
    def export_csv(self):
        file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )
        if not file:
            return

        cur.execute("""
        SELECT date, type, category, amount, note
        FROM transactions
        WHERE username=?
        """, (self.username,))

        with open(file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Type", "Category", "Amount", "Note"])
            writer.writerows(cur.fetchall())

        messagebox.showinfo("Success", "CSV exported successfully ✔")

    # ---------- PIE CHART ---------- #
    def draw_pie_chart(self, parent):
        cur.execute("""
        SELECT type, SUM(amount)
        FROM transactions
        WHERE username=?
        GROUP BY type
        """, (self.username,))

        data = cur.fetchall()
        if not data:
            tk.Label(parent, text="No data to display",
                     bg="white").pack(pady=20)
            return

        labels = [d[0] for d in data]
        values = [d[1] for d in data]

        fig = plt.Figure(figsize=(4, 4), dpi=100)
        ax = fig.add_subplot(111)

        ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90
        )
        ax.axis("equal")

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.get_tk_widget().pack(padx=20, pady=10)
        canvas.draw()

# ---------------- RUN ---------------- #
root = tk.Tk()
Login(root)
root.mainloop()
