"""
Generate realistic CSV transaction data for ProfitAI testing
Run: python generate_test_data.py
Output: test_transactions.csv
"""

import csv
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Configuration
START_DATE = datetime(2026, 1, 1)
END_DATE = datetime(2026, 12, 31)
BUSINESS_NAME = "Kedai Kopi Nusantara Sejahtera"

# Categories
INCOME_CATEGORIES = {
    "Penjualan Produk": ["Penjualan Kopi & Snack", "Penjualan Retail Biji Kopi", "Penjualan Merchandise"],
    "Penjualan Jasa": ["Catering Event Kantor", "Workshop Barista"],
    "Pendapatan Lain-lain": ["Cashback GoPay", "Bunga Bank"]
}

EXPENSE_CATEGORIES = {
    "Bahan Baku": [
        "Supplier Kopi Arabica - Toraja", 
        "Supplier Kopi Robusta - Lampung",
        "Supplier Susu & Krimer",
        "Supplier Gula & Sirup",
        "Supplier Snack & Pastry"
    ],
    "Gaji Karyawan": ["Gaji Barista", "Gaji Kasir", "Gaji Kitchen Staff", "Gaji Manager"],
    "Sewa Tempat": ["Sewa Kios Bulanan"],
    "Utilitas (Listrik, Air, Internet)": ["Listrik PLN", "Air PDAM", "Internet Indihome"],
    "Marketing & Promosi": [
        "Iklan Instagram Ads", 
        "Cetak Flyer & Banner",
        "Promo Diskon 50%",
        "Giveaway Event"
    ],
    "Perlengkapan & Peralatan": [
        "Beli Mesin Espresso",
        "Beli Grinder Kopi",
        "Gelas & Peralatan Makan",
        "Seragam Karyawan"
    ],
    "Transportasi & Pengiriman": ["Bensin Motor", "Kurir GoSend", "Grab Instant"],
    "Biaya Operasional Lain": ["Kebersihan & Sanitasi", "Perbaikan AC", "Maintenance Peralatan"],
    "Pajak & Admin Bank": ["Pajak Restoran", "Biaya Admin Transfer", "Biaya EDC"]
}

def random_date(start, end, exclude_weekday_weight=False):
    """Generate random date, with weekend having more transactions"""
    delta = end - start
    random_days = random.randint(0, delta.days)
    date = start + timedelta(days=random_days)
    return date

def generate_income_transactions():
    """Generate realistic income transactions"""
    transactions = []
    current_date = START_DATE
    
    while current_date <= END_DATE:
        # Daily sales (80% of days have sales)
        if random.random() < 0.8:
            # Weekend = higher sales
            is_weekend = current_date.weekday() >= 5
            base_amount = random.randint(5_000_000, 8_000_000) if is_weekend else random.randint(2_000_000, 5_000_000)
            
    # Seasonal multipliers
            month = current_date.month
            if month in [3, 4]:  # Ramadan spike (adjust for 2026)
                base_amount = int(base_amount * 1.4)
            elif month == 12:  # Year-end spike
                base_amount = int(base_amount * 1.3)
            elif month in [1, 2]:  # Slow start
                base_amount = int(base_amount * 0.7)
            
            shift = random.choice(["Pagi", "Siang", "Sore"])
            transactions.append({
                "transaction_date": current_date.strftime("%Y-%m-%d"),
                "description": f"Penjualan Kopi & Snack - Shift {shift}",
                "amount": base_amount,
                "type": "income",
                "category": "Penjualan Produk",
                "notes": f"Transaksi {current_date.strftime('%A')}"
            })
        
        current_date += timedelta(days=1)
    
    # Add sporadic large sales (events, catering, wholesale)
    for _ in range(12):  # ~1 per month
        date = random_date(START_DATE, END_DATE)
        event_type = random.choice(["Catering Event Kantor", "Penjualan Grosir Biji Kopi", "Workshop Barista"])
        amount = random.randint(8_000_000, 15_000_000)
        transactions.append({
            "transaction_date": date.strftime("%Y-%m-%d"),
            "description": event_type,
            "amount": amount,
            "type": "income",
            "category": "Penjualan Jasa" if "Workshop" in event_type or "Catering" in event_type else "Penjualan Produk",
            "notes": "Event khusus"
        })
    
    return transactions

def generate_expense_transactions():
    """Generate realistic expense transactions"""
    transactions = []
    
    # Fixed monthly expenses
    for month in range(1, 13):
        # Rent (every month, early month)
        rent_date = datetime(2026, month, random.randint(1, 5))
        transactions.append({
            "transaction_date": rent_date.strftime("%Y-%m-%d"),
            "description": "Sewa Kios Bulanan",
            "amount": 15_000_000,
            "type": "expense",
            "category": "Sewa Tempat",
            "notes": f"Bulan {rent_date.strftime('%B')}"
        })
        
        # Salaries (every month, end of month)
        salary_date = datetime(2026, month, random.randint(25, 28))
        salary_components = [
            ("Gaji Barista (3 orang)", 15_000_000),
            ("Gaji Kasir (2 orang)", 8_000_000),
            ("Gaji Kitchen Staff (2 orang)", 7_000_000),
            ("Gaji Manager", 6_000_000),
        ]
        
        for job_title, base_salary in salary_components:
            # THR di bulan Mei (lebaran)
            amount = base_salary * 2 if month == 5 else base_salary
            transactions.append({
                "transaction_date": salary_date.strftime("%Y-%m-%d"),
                "description": f"{job_title} - {rent_date.strftime('%B')}",
                "amount": amount,
                "type": "expense",
                "category": "Gaji Karyawan",
                "notes": "THR Lebaran" if month == 5 else ""
            })
        
        # Utilities (every month, mid month)
        util_date = datetime(2026, month, random.randint(10, 15))
        transactions.append({
            "transaction_date": util_date.strftime("%Y-%m-%d"),
            "description": "Listrik PLN",
            "amount": random.randint(2_000_000, 3_000_000),
            "type": "expense",
            "category": "Utilitas (Listrik, Air, Internet)",
            "notes": ""
        })
        transactions.append({
            "transaction_date": util_date.strftime("%Y-%m-%d"),
            "description": "Air PDAM + Internet",
            "amount": random.randint(500_000, 800_000),
            "type": "expense",
            "category": "Utilitas (Listrik, Air, Internet)",
            "notes": ""
        })
        
        # Raw materials (3-4x per month)
        for _ in range(random.randint(3, 4)):
            raw_date = datetime(2026, month, random.randint(1, 28))
            supplier = random.choice(EXPENSE_CATEGORIES["Bahan Baku"])
            transactions.append({
                "transaction_date": raw_date.strftime("%Y-%m-%d"),
                "description": f"Bayar {supplier}",
                "amount": random.randint(5_000_000, 8_000_000),
                "type": "expense",
                "category": "Bahan Baku",
                "notes": ""
            })
    
    # Variable expenses
    # Marketing campaigns (sporadic)
    marketing_months = [2, 4, 7, 10, 12]  # Strategic months
    for month in marketing_months:
        campaign_date = datetime(2026, month, random.randint(1, 28))
        campaigns = [
            ("Iklan Instagram Ads - 1 Bulan", random.randint(2_000_000, 4_000_000)),
            ("Cetak Flyer & Banner Promo", random.randint(1_000_000, 2_000_000)),
            ("Giveaway Event Ulang Tahun", random.randint(3_000_000, 5_000_000)),
        ]
        campaign = random.choice(campaigns)
        transactions.append({
            "transaction_date": campaign_date.strftime("%Y-%m-%d"),
            "description": campaign[0],
            "amount": campaign[1],
            "type": "expense",
            "category": "Marketing & Promosi",
            "notes": ""
        })
    
    # Equipment purchases (big ticket items)
    special_purchases = [
        (datetime(2026, 3, 15), "Beli Mesin Espresso Baru", 25_000_000, "Upgrade peralatan"),
        (datetime(2026, 8, 10), "Beli Grinder Kopi Premium", 8_000_000, "Investasi kualitas"),
        (datetime(2026, 11, 5), "Renovasi Interior & Furniture", 12_000_000, "Refresh tampilan"),
    ]
    
    for date, desc, amount, note in special_purchases:
        transactions.append({
            "transaction_date": date.strftime("%Y-%m-%d"),
            "description": desc,
            "amount": amount,
            "type": "expense",
            "category": "Perlengkapan & Peralatan",
            "notes": note
        })
    
    # Operational expenses (random throughout year)
    for _ in range(30):
        date = random_date(START_DATE, END_DATE)
        ops_expenses = [
            ("Kebersihan & Sanitasi", random.randint(500_000, 1_000_000)),
            ("Bensin Motor Delivery", random.randint(300_000, 600_000)),
            ("Perbaikan AC", random.randint(1_500_000, 3_000_000)),
            ("Biaya Admin Bank", random.randint(50_000, 150_000)),
            ("Pajak Restoran", random.randint(1_000_000, 2_000_000)),
        ]
        expense = random.choice(ops_expenses)
        category = "Biaya Operasional Lain"
        if "Bensin" in expense[0]:
            category = "Transportasi & Pengiriman"
        elif "Pajak" in expense[0] or "Admin" in expense[0]:
            category = "Pajak & Admin Bank"
        
        transactions.append({
            "transaction_date": date.strftime("%Y-%m-%d"),
            "description": expense[0],
            "amount": expense[1],
            "type": "expense",
            "category": category,
            "notes": ""
        })
    
    return transactions

def generate_csv():
    """Generate complete CSV file"""
    print("🔄 Generating test transaction data...")
    
    # Generate transactions
    income = generate_income_transactions()
    expenses = generate_expense_transactions()
    
    # Combine and sort by date
    all_transactions = income + expenses
    all_transactions.sort(key=lambda x: x["transaction_date"])
    
    # Write to CSV
    output_file = "test_transactions.csv"
    # Backend expects 'transaction_date' not 'date'
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["transaction_date", "description", "amount", "type", "category", "notes"])
        writer.writeheader()
        writer.writerows(all_transactions)
    
    # Statistics
    total_income = sum(t["amount"] for t in income)
    total_expense = sum(t["amount"] for t in expenses)
    net_profit = total_income - total_expense
    profit_margin = (net_profit / total_income * 100) if total_income > 0 else 0
    
    print(f"\n✅ Generated {len(all_transactions)} transactions")
    print(f"📊 Statistics:")
    print(f"   Total Income:   Rp {total_income:,}")
    print(f"   Total Expense:  Rp {total_expense:,}")
    print(f"   Net Profit:     Rp {net_profit:,}")
    print(f"   Profit Margin:  {profit_margin:.2f}%")
    print(f"\n💾 Saved to: {output_file}")
    print(f"\n🚀 Upload file ini ke ProfitAI untuk testing!")

if __name__ == "__main__":
    generate_csv()
