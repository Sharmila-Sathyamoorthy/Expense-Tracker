import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

conn = sqlite3.connect("expenses.db")
cur = conn.cursor()

# Category presets
INCOME_CATEGORIES = ["Salary", "Freelance", "Business", "Investment", "Gift", "Other"]
EXPENSE_CATEGORIES = ["Food", "Travel", "Rent", "Shopping", "Bills", "Health", "Education", "Entertainment", "Other"]

class TransactionsPage:
    def __init__(self, parent, username):
        self.parent = parent
        self.username = username
        self.build()

    def build(self):
        tk.Label(
            self.parent,
            text="Transactions",
            font=("Segoe UI", 22, "bold"),
            bg="#f5f6fa"
        ).pack(anchor="w", padx=30, pady=20)

        # ---------------- FORM CARD ---------------- #
        form = tk.Frame(self.parent, bg="white", bd=1, relief="solid")
        form.pack(fill="x", padx=30, pady=10)

        # Date
        tk.Label(form, text="Date", bg="white").grid(row=0, column=0, padx=10, pady=10)
        self.date = tk.Entry(form)
        self.date.insert(0, datetime.today().strftime("%Y-%m-%d"))
        self.date.grid(row=0, column=1)

        # Type
        tk.Label(form, text="Type", bg="white").grid(row=0, column=2, padx=10)
        self.type = ttk.Combobox(form, values=["Income", "Expense"], state="readonly", width=15)
        self.type.current(1)
        self.type.grid(row=0, column=3)
        self.type.bind("<<ComboboxSelected>>", self.update_categories)

        # Category
        tk.Label(form, text="Category", bg="white").grid(row=1, column=0, padx=10)
        self.category = ttk.Combobox(form, state="readonly", width=18)
        self.category.grid(row=1, column=1)
        self.update_categories()

        # Amount
        tk.Label(form, text="Amount", bg="white").grid(row=1, column=2, padx=10)
        self.amount = tk.Entry(form)
        self.amount.grid(row=1, column=3)

        # Note
        tk.Label(form, text="Note", bg="white").grid(row=2, column=0, padx=10, pady=10)
        self.note = tk.Entry(form, width=50)
        self.note.grid(row=2, column=1, columnspan=3, pady=10)

        # Buttons
        tk.Button(
            form,
            text="➕ Add Transaction",
            bg="#44bd32",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            command=self.add
        ).grid(row=3, column=3, sticky="e", pady=15, padx=10)

        # ---------------- TABLE ---------------- #
        self.table()

    def table(self):
        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        cols = ("Date", "Type", "Category", "Amount", "Note")
        self.tree = ttk.Treeview(self.parent, columns=cols, show="headings")

        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=30, pady=10)

        self.tree.tag_configure("income", background="#e8f8f5")
        self.tree.tag_configure("expense", background="#fdecea")

        # Delete button
        tk.Button(
            self.parent,
            text="🗑 Remove Selected Transaction",
            bg="#e84118",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            command=self.delete
        ).pack(anchor="e", padx=30, pady=10)

        self.refresh()

    # ---------------- FUNCTIONS ---------------- #
    def update_categories(self, event=None):
        if self.type.get() == "Income":
            self.category["values"] = INCOME_CATEGORIES
        else:
            self.category["values"] = EXPENSE_CATEGORIES
        self.category.current(0)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        cur.execute("""
        SELECT id, date, type, category, amount, note
        FROM transactions
        WHERE username=?
        ORDER BY date DESC
        """, (self.username,))

        for tid, date, t, cat, amt, note in cur.fetchall():
            tag = "income" if t == "Income" else "expense"
            self.tree.insert("", "end", iid=tid, values=(date, t, cat, amt, note), tags=(tag,))

    def add(self):
        try:
            amt = float(self.amount.get())
        except:
            messagebox.showerror("Error", "Enter valid amount")
            return

        cur.execute("""
        INSERT INTO transactions (username, date, type, category, amount, note)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            self.username,
            self.date.get(),
            self.type.get(),
            self.category.get(),
            amt,
            self.note.get()
        ))
        conn.commit()
        self.amount.delete(0, tk.END)
        self.note.delete(0, tk.END)
        self.refresh()

    def delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Select a transaction to delete")
            return

        if not messagebox.askyesno("Confirm", "Delete selected transaction?"):
            return

        cur.execute("DELETE FROM transactions WHERE id=?", (selected[0],))
        conn.commit()
        self.refresh()
