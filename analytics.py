import tkinter as tk
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime, timedelta
from matplotlib import cm

# Color palette for a modern, vibrant look
COLORS = {
    'bg': '#f8f9fa',
    'card_bg': '#ffffff',
    'primary': '#4361ee',
    'secondary': '#3a0ca3',
    'accent': '#7209b7',
    'success': '#4cc9f0',
    'danger': '#f72585',
    'warning': '#f8961e',
    'info': '#43aa8b',
    'text': '#2b2d42',
    'light_text': '#8d99ae'
}

# Modern matplotlib style
plt.style.use('seaborn-v0_8')

class AnalyticsPage:
    def __init__(self, parent, username):
        self.parent = parent
        self.username = username
        self.conn = sqlite3.connect("expenses.db")
        self.cur = self.conn.cursor()
        self.build()

    def build(self):
        # Header
        header_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        header_frame.pack(fill=tk.X, padx=30, pady=(20, 10))
        
        tk.Label(
            header_frame,
            text="📊 Analytics Dashboard",
            font=("Segoe UI", 28, "bold"),
            bg=COLORS['bg'],
            fg=COLORS['primary']
        ).pack(side=tk.LEFT)
        
        # Refresh button
        tk.Button(
            header_frame,
            text="🔄 Refresh",
            font=("Segoe UI", 11),
            bg=COLORS['accent'],
            fg='white',
            padx=15,
            pady=5,
            command=self.refresh_analytics,
            cursor='hand2'
        ).pack(side=tk.RIGHT)
        
        # Main container with scrollbar
        canvas = tk.Canvas(self.parent, bg=COLORS['bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create analytics cards
        self.create_summary_cards(scrollable_frame)
        self.monthly_trend(scrollable_frame)
        self.category_pie_chart(scrollable_frame)
        self.income_vs_expense(scrollable_frame)
        self.category_bar_chart(scrollable_frame)
        
    def create_summary_cards(self, parent):
        """Create summary cards at the top"""
        summary_frame = tk.Frame(parent, bg=COLORS['bg'])
        summary_frame.pack(fill=tk.X, padx=30, pady=20)
        
        # Get summary data
        self.cur.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN type='Income' THEN amount ELSE 0 END), 0) as total_income,
                COALESCE(SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END), 0) as total_expense,
                COUNT(CASE WHEN type='Income' THEN 1 END) as income_count,
                COUNT(CASE WHEN type='Expense' THEN 1 END) as expense_count
            FROM transactions 
            WHERE username=?
        """, (self.username,))
        
        income, expense, income_count, expense_count = self.cur.fetchone()
        balance = income - expense
        
        # Summary metrics
        metrics = [
            {
                'title': 'Total Income',
                'value': f'${income:,.2f}',
                'icon': '💰',
                'color': COLORS['success'],
                'subtext': f'{income_count} transactions'
            },
            {
                'title': 'Total Expenses',
                'value': f'${expense:,.2f}',
                'icon': '💸',
                'color': COLORS['danger'],
                'subtext': f'{expense_count} transactions'
            },
            {
                'title': 'Balance',
                'value': f'${balance:,.2f}',
                'icon': '⚖️',
                'color': COLORS['primary'] if balance >= 0 else COLORS['danger'],
                'subtext': 'Income - Expenses'
            },
            {
                'title': 'Savings Rate',
                'value': f'{income and ((income - expense) / income * 100):.1f}%',
                'icon': '📈',
                'color': COLORS['info'],
                'subtext': 'of income saved'
            }
        ]
        
        for i, metric in enumerate(metrics):
            card = tk.Frame(
                summary_frame,
                bg=COLORS['card_bg'],
                relief=tk.RAISED,
                borderwidth=0,
                highlightbackground='#e0e0e0',
                highlightthickness=1
            )
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0 if i == 0 else 10, 0))
            
            # Card content
            tk.Label(
                card,
                text=metric['icon'],
                font=("Segoe UI", 24),
                bg=COLORS['card_bg'],
                fg=metric['color']
            ).pack(anchor="w", padx=15, pady=(15, 5))
            
            tk.Label(
                card,
                text=metric['title'],
                font=("Segoe UI", 12),
                bg=COLORS['card_bg'],
                fg=COLORS['light_text']
            ).pack(anchor="w", padx=15)
            
            tk.Label(
                card,
                text=metric['value'],
                font=("Segoe UI", 22, "bold"),
                bg=COLORS['card_bg'],
                fg=metric['color']
            ).pack(anchor="w", padx=15, pady=(5, 0))
            
            tk.Label(
                card,
                text=metric['subtext'],
                font=("Segoe UI", 10),
                bg=COLORS['card_bg'],
                fg=COLORS['light_text']
            ).pack(anchor="w", padx=15, pady=(0, 15))
    
    def monthly_trend(self, parent):
        """Create monthly expense trend line chart"""
        card_frame = self.create_card(parent, "📅 Monthly Expense Trend")
        
        fig = plt.Figure(figsize=(10, 4), facecolor='none')
        ax = fig.add_subplot(111)
        
        # Get last 6 months of data
        self.cur.execute("""
            SELECT SUBSTR(date,1,7) as month, 
                   SUM(CASE WHEN type='Income' THEN amount ELSE 0 END) as income,
                   SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END) as expense
            FROM transactions
            WHERE username=? 
            GROUP BY SUBSTR(date,1,7)
            ORDER BY month DESC
            LIMIT 6
        """, (self.username,))
        
        data = self.cur.fetchall()
        
        if data:
            months = [d[0] for d in data][::-1]
            income = [d[1] for d in data][::-1]
            expenses = [d[2] for d in data][::-1]
            
            # Create line chart
            ax.plot(months, income, marker='o', linewidth=2.5, 
                   color=COLORS['success'], label='Income', markersize=8)
            ax.plot(months, expenses, marker='s', linewidth=2.5,
                   color=COLORS['danger'], label='Expenses', markersize=8)
            
            # Fill between lines
            ax.fill_between(months, income, expenses, where=[i>=e for i,e in zip(income, expenses)], 
                           alpha=0.2, color=COLORS['success'])
            ax.fill_between(months, income, expenses, where=[i<e for i,e in zip(income, expenses)], 
                           alpha=0.2, color=COLORS['danger'])
            
            # Style
            ax.set_facecolor('#f8f9fa')
            ax.grid(True, alpha=0.3)
            ax.set_xlabel('Month', fontsize=11, color=COLORS['text'])
            ax.set_ylabel('Amount ($)', fontsize=11, color=COLORS['text'])
            ax.set_title('Monthly Income vs Expenses', fontsize=13, fontweight='bold', color=COLORS['text'])
            ax.legend(loc='upper left', fontsize=10)
            ax.tick_params(axis='x', rotation=45, colors=COLORS['text'])
            ax.tick_params(axis='y', colors=COLORS['text'])
            
            # Add value annotations
            for i, (inc, exp) in enumerate(zip(income, expenses)):
                ax.annotate(f'${inc:,.0f}', (months[i], inc), 
                           textcoords="offset points", xytext=(0,10), 
                           ha='center', fontsize=9, color=COLORS['success'])
                ax.annotate(f'${exp:,.0f}', (months[i], exp), 
                           textcoords="offset points", xytext=(0,-15), 
                           ha='center', fontsize=9, color=COLORS['danger'])
        
        else:
            ax.text(0.5, 0.5, 'No data available', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14, color=COLORS['light_text'])
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, card_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    def category_pie_chart(self, parent):
        """Create category distribution pie chart"""
        card_frame = self.create_card(parent, "🥧 Expense Categories Distribution")
        
        fig = plt.Figure(figsize=(6, 5), facecolor='none')
        ax = fig.add_subplot(111)
        
        self.cur.execute("""
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE username=? AND type='Expense'
            GROUP BY category
            ORDER BY total DESC
        """, (self.username,))
        
        data = self.cur.fetchall()
        
        if data:
            categories = [d[0] for d in data]
            amounts = [d[1] for d in data]
            
            # Create vibrant color palette
            colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
            
            # Create pie chart
            wedges, texts, autotexts = ax.pie(
                amounts, 
                labels=categories,
                colors=colors,
                autopct='%1.1f%%',
                startangle=90,
                pctdistance=0.85,
                textprops={'fontsize': 10, 'color': COLORS['text']},
                wedgeprops={'edgecolor': 'white', 'linewidth': 2}
            )
            
            # Style
            ax.set_title('Expense Breakdown by Category', fontsize=13, 
                        fontweight='bold', color=COLORS['text'], pad=20)
            
            # Add amounts in dollars
            for i, (wedge, amount) in enumerate(zip(wedges, amounts)):
                ang = (wedge.theta2 - wedge.theta1)/2. + wedge.theta1
                y = np.sin(np.deg2rad(ang))
                x = np.cos(np.deg2rad(ang))
                horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
                ax.text(1.35*x, 1.35*y, f'${amount:,.2f}', 
                       horizontalalignment=horizontalalignment, 
                       verticalalignment='center',
                       fontsize=9, color=COLORS['text'])
        else:
            ax.text(0.5, 0.5, 'No expense data available', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14, color=COLORS['light_text'])
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, card_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    def income_vs_expense(self, parent):
        """Create income vs expense comparison chart"""
        card_frame = self.create_card(parent, "⚖️ Income vs Expenses Comparison")
        
        fig = plt.Figure(figsize=(8, 4), facecolor='none')
        ax = fig.add_subplot(111)
        
        self.cur.execute("""
            SELECT 
                SUBSTR(date,1,7) as month,
                SUM(CASE WHEN type='Income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type='Expense' THEN amount ELSE 0 END) as expense
            FROM transactions
            WHERE username=? 
            GROUP BY SUBSTR(date,1,7)
            ORDER BY month
            LIMIT 12
        """, (self.username,))
        
        data = self.cur.fetchall()
        
        if data:
            months = [d[0] for d in data]
            income = [d[1] for d in data]
            expenses = [d[2] for d in data]
            
            x = np.arange(len(months))
            width = 0.35
            
            # Create grouped bar chart
            bars1 = ax.bar(x - width/2, income, width, 
                          label='Income', color=COLORS['success'], 
                          edgecolor='white', linewidth=1.5)
            bars2 = ax.bar(x + width/2, expenses, width, 
                          label='Expenses', color=COLORS['danger'],
                          edgecolor='white', linewidth=1.5)
            
            # Style
            ax.set_facecolor('#f8f9fa')
            ax.set_xlabel('Month', fontsize=11, color=COLORS['text'])
            ax.set_ylabel('Amount ($)', fontsize=11, color=COLORS['text'])
            ax.set_title('Monthly Comparison', fontsize=13, fontweight='bold', color=COLORS['text'])
            ax.set_xticks(x)
            ax.set_xticklabels([m[5:] for m in months], rotation=45, color=COLORS['text'])
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            def autolabel(bars):
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.annotate(f'${height:,.0f}',
                                   xy=(bar.get_x() + bar.get_width() / 2, height),
                                   xytext=(0, 3),
                                   textcoords="offset points",
                                   ha='center', va='bottom',
                                   fontsize=8, fontweight='bold')
            
            autolabel(bars1)
            autolabel(bars2)
            
            # Add net savings line
            net_savings = [i - e for i, e in zip(income, expenses)]
            ax.plot(x, net_savings, color=COLORS['primary'], marker='D', 
                   linewidth=2, label='Net Savings', markersize=6)
            
            ax.legend(loc='upper left', fontsize=10)
        else:
            ax.text(0.5, 0.5, 'No data available', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14, color=COLORS['light_text'])
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, card_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    def category_bar_chart(self, parent):
        """Create horizontal bar chart for top categories"""
        card_frame = self.create_card(parent, "🏆 Top Spending Categories")
        
        fig = plt.Figure(figsize=(8, 5), facecolor='none')
        ax = fig.add_subplot(111)
        
        self.cur.execute("""
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE username=? AND type='Expense'
            GROUP BY category
            ORDER BY total DESC
            LIMIT 8
        """, (self.username,))
        
        data = self.cur.fetchall()
        
        if data:
            categories = [d[0] for d in data][::-1]
            amounts = [d[1] for d in data][::-1]
            
            # Create gradient colors
            colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(categories)))
            
            # Create horizontal bar chart
            bars = ax.barh(categories, amounts, color=colors, 
                          edgecolor='white', linewidth=1.5)
            
            # Style
            ax.set_facecolor('#f8f9fa')
            ax.set_xlabel('Amount ($)', fontsize=11, color=COLORS['text'])
            ax.set_title('Top Spending Categories', fontsize=13, 
                        fontweight='bold', color=COLORS['text'], pad=15)
            ax.grid(True, alpha=0.3, axis='x')
            
            # Add value labels
            for i, (bar, amount) in enumerate(zip(bars, amounts)):
                width = bar.get_width()
                ax.text(width + max(amounts)*0.01, bar.get_y() + bar.get_height()/2,
                       f'${amount:,.2f}', va='center', fontsize=10, 
                       fontweight='bold', color=COLORS['text'])
                
                # Add percentage of total
                percentage = (amount / sum(amounts)) * 100
                ax.text(bar.get_width()/2, bar.get_y() + bar.get_height()/2,
                       f'{percentage:.1f}%', va='center', ha='center',
                       fontsize=9, color='white', fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'No expense data available', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14, color=COLORS['light_text'])
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, card_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    def create_card(self, parent, title):
        """Create a styled card container for charts"""
        card = tk.Frame(
            parent,
            bg=COLORS['card_bg'],
            relief=tk.RAISED,
            borderwidth=0,
            highlightbackground='#e0e0e0',
            highlightthickness=1
        )
        card.pack(fill=tk.BOTH, expand=True, padx=30, pady=15)
        
        # Card header
        header = tk.Frame(card, bg=COLORS['card_bg'])
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        tk.Label(
            header,
            text=title,
            font=("Segoe UI", 16, "bold"),
            bg=COLORS['card_bg'],
            fg=COLORS['primary']
        ).pack(side=tk.LEFT)
        
        return card
    
    def refresh_analytics(self):
        """Refresh all analytics charts"""
        # Destroy all widgets in parent
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Rebuild the page
        self.build()
    
    def __del__(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()

# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Expense Tracker Analytics")
    root.geometry("1400x900")
    root.configure(bg=COLORS['bg'])
    
    # For testing - create sample database
    conn = sqlite3.connect("expenses.db")
    cur = conn.cursor()
    
    # Create sample table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            type TEXT,
            category TEXT,
            amount REAL,
            date TEXT,
            description TEXT
        )
    """)
    
    # Add some sample data for testing
    import random
    categories = ['Food', 'Transport', 'Shopping', 'Entertainment', 'Bills', 'Healthcare']
    for i in range(30):
        month = f"2024-{random.randint(1, 12):02d}"
        day = f"{random.randint(1, 28):02d}"
        date = f"{month}-{day}"
        cur.execute("""
            INSERT INTO transactions (username, type, category, amount, date, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "test_user",
            random.choice(['Income', 'Expense']),
            random.choice(categories),
            round(random.uniform(10, 500), 2),
            date,
            f"Sample transaction {i+1}"
        ))
    
    conn.commit()
    conn.close()
    
    # Create analytics page
    analytics = AnalyticsPage(root, "test_user")
    root.mainloop()