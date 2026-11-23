#!/usr/bin/env python3
"""
Re-implementation of the COBOL BOOKFORUM program.
Reads input from src/INPUT.DAT and updates data/*.DAT files accordingly.
Run from the cobol/ directory, or paths are relative to this script's location.
"""

import os
import sys

# Determine base directory (directory of this script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ACCOUNTS_PATH = os.path.join(BASE_DIR, "data", "ACCOUNTS.DAT")
BOOKS_PATH = os.path.join(BASE_DIR, "data", "BOOKS.DAT")
TRANSACTIONS_PATH = os.path.join(BASE_DIR, "data", "TRANSACTIONS.DAT")
INPUT_PATH = os.path.join(BASE_DIR, "src", "INPUT.DAT")

ACCOUNT_REC_LEN = 4 + 20 + 10  # 34
BOOK_REC_LEN = 4 + 20 + 4      # 28
TRANS_REC_LEN = 4 + 10 + 4 + 4 # 22
INPUT_REC_LEN = 4 + 4 + 4 + 10 # 22

def read_records(path, rec_len):
    """Read fixed-length records from a binary file."""
    if not os.path.exists(path):
        return []
    with open(path, "rb") as f:
        data = f.read()
    records = []
    for i in range(0, len(data) - rec_len + 1, rec_len):
        records.append(data[i:i+rec_len])
    # If leftover bytes less than rec_len, ignore (like EOF)
    return records

def write_records(path, records):
    """Write list of fixed-length record bytes to file."""
    with open(path, "wb") as f:
        for rec in records:
            f.write(rec)

def parse_account(rec):
    account_id = rec[0:4].decode("ascii", errors="replace")
    name = rec[4:24].decode("ascii", errors="replace")
    balance_str = rec[24:34].decode("ascii", errors="replace")
    try:
        balance = int(balance_str)
    except ValueError:
        balance = 0
    return account_id, name, balance

def format_account(account_id, name, balance):
    id_b = account_id.encode("ascii")[:4].ljust(4, b" ")
    name_b = name.encode("ascii")[:20].ljust(20, b" ")
    bal_b = f"{balance:010d}".encode("ascii")[:10]
    return id_b + name_b + bal_b

def parse_book(rec):
    book_id = rec[0:4].decode("ascii", errors="replace")
    title = rec[4:24].decode("ascii", errors="replace")
    owner = rec[24:28].decode("ascii", errors="replace")
    return book_id, title, owner

def format_book(book_id, title, owner):
    id_b = book_id.encode("ascii")[:4].ljust(4, b" ")
    title_b = title.encode("ascii")[:20].ljust(20, b" ")
    owner_b = owner.encode("ascii")[:4].ljust(4, b" ")
    return id_b + title_b + owner_b

def parse_trans(rec):
    book = rec[0:4].decode("ascii", errors="replace")
    amount_str = rec[4:14].decode("ascii", errors="replace")
    seller = rec[14:18].decode("ascii", errors="replace")
    buyer = rec[18:22].decode("ascii", errors="replace")
    try:
        amount = int(amount_str)
    except ValueError:
        amount = 0
    return book, amount, seller, buyer

def format_trans(book, amount, seller, buyer):
    book_b = book.encode("ascii")[:4].ljust(4, b" ")
    amt_b = f"{amount:010d}".encode("ascii")[:10]
    seller_b = seller.encode("ascii")[:4].ljust(4, b" ")
    buyer_b = buyer.encode("ascii")[:4].ljust(4, b" ")
    return book_b + amt_b + seller_b + buyer_b

def main():
    # Read input
    if not os.path.exists(INPUT_PATH):
        print("Error: Input file is empty")
        return

    with open(INPUT_PATH, "rb") as f:
        input_data = f.read()

    if len(input_data) < INPUT_REC_LEN:
        print("Error: Input file is empty")
        return

    input_rec = input_data[:INPUT_REC_LEN]
    buyer_id = input_rec[0:4].decode("ascii", errors="replace").rstrip()
    seller_id = input_rec[4:8].decode("ascii", errors="replace").rstrip()
    book_id = input_rec[8:12].decode("ascii", errors="replace").rstrip()
    amount_str = input_rec[12:22].decode("ascii", errors="replace")
    try:
        amount = int(amount_str.strip() or "0")
    except ValueError:
        amount = 0

    # Validate users and book
    accounts = read_records(ACCOUNTS_PATH, ACCOUNT_REC_LEN)
    books = read_records(BOOKS_PATH, BOOK_REC_LEN)

    buyer_found = False
    seller_found = False
    book_found = False
    valid_owner = False

    for rec in accounts:
        aid, _, _ = parse_account(rec)
        if aid.rstrip() == buyer_id:
            buyer_found = True
        if aid.rstrip() == seller_id:
            seller_found = True

    for rec in books:
        bid, _, owner = parse_book(rec)
        if bid.rstrip() == book_id:
            book_found = True
            if owner.rstrip() == seller_id:
                valid_owner = True

    if not (buyer_found and seller_found and book_found and valid_owner):
        print("Transaction failed due to validation errors")
        return

    # Process transaction
    # Update accounts
    new_accounts = []
    for rec in accounts:
        aid, name, bal = parse_account(rec)
        if aid.rstrip() == buyer_id:
            bal -= amount
        if aid.rstrip() == seller_id:
            bal += amount
        new_accounts.append(format_account(aid, name, bal))
    write_records(ACCOUNTS_PATH, new_accounts)

    # Update books
    new_books = []
    for rec in books:
        bid, title, owner = parse_book(rec)
        if bid.rstrip() == book_id:
            owner = buyer_id
        new_books.append(format_book(bid, title, owner))
    write_records(BOOKS_PATH, new_books)

    # Append transaction
    trans_records = read_records(TRANSACTIONS_PATH, TRANS_REC_LEN)
    new_trans = format_trans(book_id, amount, seller_id, buyer_id)
    trans_records.append(new_trans)
    write_records(TRANSACTIONS_PATH, trans_records)

    print("Transaction completed successfully")

if __name__ == "__main__":
    main()
