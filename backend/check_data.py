import sqlite3

conn = sqlite3.connect('profitai_new.db')
cursor = conn.cursor()

# Count transactions
cursor.execute('SELECT COUNT(*) FROM transactions')
total = cursor.fetchone()[0]
print(f'Total transactions: {total}')

# Show last 5
cursor.execute('SELECT transaction_date, description, amount, tx_type FROM transactions ORDER BY id DESC LIMIT 5')
print('\nLast 5 transactions:')
for row in cursor.fetchall():
    print(f'  {row[0]} | {row[1][:40]} | Rp {int(row[2]):,} | {row[3]}')

# Count by type
cursor.execute('SELECT tx_type, COUNT(*) FROM transactions GROUP BY tx_type')
print('\nTransactions by type:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

conn.close()
