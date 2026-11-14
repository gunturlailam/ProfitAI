import sqlite3

conn = sqlite3.connect('profitai_new.db')
cursor = conn.cursor()

# Check organizations
cursor.execute('SELECT id, name FROM organizations')
print('Organizations:')
for row in cursor.fetchall():
    print(f'  ID={row[0]}: {row[1]}')

# Check users
cursor.execute('SELECT id, email FROM users LIMIT 5')
print('\nUsers:')
for row in cursor.fetchall():
    print(f'  ID={row[0]}, Email={row[1]}')

# Check transactions by org_id
cursor.execute('SELECT organization_id, status, COUNT(*) FROM transactions GROUP BY organization_id, status')
print('\nTransactions by org_id and status:')
for row in cursor.fetchall():
    print(f'  OrgID={row[0]}, Status={row[1]}, Count={row[2]}')

# Check transaction date range
cursor.execute('SELECT MIN(transaction_date), MAX(transaction_date) FROM transactions')
date_range = cursor.fetchone()
print(f'\nTransaction date range: {date_range[0]} to {date_range[1]}')

# Check latest import batch
cursor.execute('SELECT id, organization_id, filename, total_rows, committed_rows, status FROM import_batches ORDER BY id DESC LIMIT 1')
print('\nLatest import batch:')
batch = cursor.fetchone()
if batch:
    print(f'  BatchID={batch[0]}, OrgID={batch[1]}, File={batch[2]}')
    print(f'  Total={batch[3]}, Committed={batch[4]}, Status={batch[5]}')

conn.close()
