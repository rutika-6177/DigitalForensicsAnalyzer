"""
AegisForensics // Case Reset Utility
Wipes all evidence records and stored physical images to start a fresh investigation.
Run with: py reset_case.py
"""

import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import db_manager

def main():
    print("=" * 60)
    print("  AEGIS FORENSICS // RESET CASE DATABASE")
    print("=" * 60)
    db_manager.clear_all_evidence()
    print("  * All evidence records purged from database/forensic.db")
    print("  * All stored images removed from storage/images/")
    print("  * Database and storage successfully reset to blank state!\n")

if __name__ == "__main__":
    main()
