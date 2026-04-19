import sqlite3
import os

DB_PATH = "finance.db"

def init_db():
    """Initializes the finance database with mock tables and data if not existent."""
    if os.path.exists(DB_PATH):
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create Clients table
    cursor.execute('''
    CREATE TABLE clients (
        client_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL,
        join_date DATE NOT NULL,
        risk_profile TEXT NOT NULL
    )
    ''')

    # Create Accounts table
    cursor.execute('''
    CREATE TABLE accounts (
        account_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        account_type TEXT NOT NULL,
        balance DECIMAL(15, 2) NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY(client_id) REFERENCES clients(client_id)
    )
    ''')

    # Create Transactions table
    cursor.execute('''
    CREATE TABLE transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER NOT NULL,
        amount DECIMAL(15, 2) NOT NULL,
        transaction_date DATETIME NOT NULL,
        description TEXT NOT NULL,
        FOREIGN KEY(account_id) REFERENCES accounts(account_id)
    )
    ''')

    # Create Loans table
    cursor.execute('''
    CREATE TABLE loans (
        loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        principal DECIMAL(15, 2) NOT NULL,
        interest_rate DECIMAL(5, 2) NOT NULL,
        status TEXT NOT NULL,
        term_months INTEGER NOT NULL,
        FOREIGN KEY(client_id) REFERENCES clients(client_id)
    )
    ''')

    # Insert mock Clients
    clients_data = [
        ('John', 'Doe', 'jdoe@example.com', '2020-01-15', 'Moderate'),
        ('Jane', 'Smith', 'jsmith@example.com', '2019-11-20', 'Aggressive'),
        ('Michael', 'Johnson', 'mjohnson@example.com', '2021-05-10', 'Conservative'),
        ('Emily', 'Davis', 'edavis@example.com', '2022-03-08', 'Moderate')
    ]
    cursor.executemany("INSERT INTO clients (first_name, last_name, email, join_date, risk_profile) VALUES (?, ?, ?, ?, ?)", clients_data)

    # Insert mock Accounts
    accounts_data = [
        (1, 'Checking', 5000.50, 'Active'),
        (1, 'Savings', 125000.00, 'Active'),
        (2, 'Checking', 1200.75, 'Active'),
        (2, 'Investment', 450000.00, 'Active'),
        (3, 'Savings', 85000.00, 'Active'),
        (4, 'Checking', 800.00, 'Active')
    ]
    cursor.executemany("INSERT INTO accounts (client_id, account_type, balance, status) VALUES (?, ?, ?, ?)", accounts_data)

    # Insert mock Transactions
    transactions_data = [
        (1, -150.00, '2023-10-01 09:30:00', 'Grocery Store'),
        (1, -50.00, '2023-10-02 12:15:00', 'Gas Station'),
        (2, 500.00, '2023-10-03 08:00:00', 'Interest Deposit'),
        (3, -1200.00, '2023-10-01 10:00:00', 'Rent Payment'),
        (4, 5000.00, '2023-10-05 15:00:00', 'Portfolio Dividends'),
        (1, 2000.00, '2023-10-15 08:00:00', 'Salary Deposit')
    ]
    cursor.executemany("INSERT INTO transactions (account_id, amount, transaction_date, description) VALUES (?, ?, ?, ?)", transactions_data)

    # Insert mock Loans
    loans_data = [
        (1, 25000.00, 5.5, 'Active', 60),
        (3, 150000.00, 3.2, 'Active', 360),
        (4, 10000.00, 7.0, 'Paid Off', 24)
    ]
    cursor.executemany("INSERT INTO loans (client_id, principal, interest_rate, status, term_months) VALUES (?, ?, ?, ?, ?)", loans_data)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    print("Initializing Finance Database...")
    init_db()
    print("Finance Database created successfully.")
