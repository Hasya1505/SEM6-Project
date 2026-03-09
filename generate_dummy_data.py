"""
Dummy Data Generator for Medical Store Management System
Generates 1 year of realistic sales data with trends
"""

import mysql.connector
from datetime import datetime, timedelta
import random
import hashlib
from config import Config

# ============================================
# DATABASE CONNECTION
# ============================================
def get_db():
    """Create MySQL database connection"""
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# ============================================
# DATA TEMPLATES
# ============================================

# Staff users (5-6 users)
STAFF_USERS = [
    {'username': 'rajesh', 'password': 'rajesh123', 'full_name': 'Rajesh Kumar', 'role': 'cashier', 'email': 'rajesh@medistore.com', 'phone': '+91-9123456701'},
    {'username': 'priya', 'password': 'priya123', 'full_name': 'Priya Sharma', 'role': 'cashier', 'email': 'priya@medistore.com', 'phone': '+91-9123456702'},
    {'username': 'amit', 'password': 'amit123', 'full_name': 'Amit Patel', 'role': 'cashier', 'email': 'amit@medistore.com', 'phone': '+91-9123456703'},
    {'username': 'neha', 'password': 'neha123', 'full_name': 'Neha Verma', 'role': 'cashier', 'email': 'neha@medistore.com', 'phone': '+91-9123456704'},
    {'username': 'vikram', 'password': 'vikram123', 'full_name': 'Vikram Singh', 'role': 'owner', 'email': 'vikram@medistore.com', 'phone': '+91-9123456705'},
    {'username': 'sneha', 'password': 'sneha123', 'full_name': 'Sneha Rao', 'role': 'cashier', 'email': 'sneha@medistore.com', 'phone': '+91-9123456706'},
]

# Customer first names and last names for generating ~130 customers
FIRST_NAMES = [
    'Aarav', 'Vivaan', 'Aditya', 'Arjun', 'Sai', 'Vihaan', 'Dhruv', 'Krishna', 'Shaurya', 'Advaith',
    'Aadhya', 'Diya', 'Ananya', 'Saanvi', 'Ishita', 'Kavya', 'Navya', 'Myra', 'Pari', 'Riya',
    'Rahul', 'Rohan', 'Karan', 'Nikhil', 'Kunal', 'Siddharth', 'Varun', 'Yash', 'Akash', 'Harsh',
    'Pooja', 'Anjali', 'Priyanka', 'Swati', 'Megha', 'Tanvi', 'Shreya', 'Divya', 'Nikita', 'Jaya',
    'Manoj', 'Suresh', 'Ramesh', 'Dinesh', 'Mahesh', 'Prakash', 'Santosh', 'Ganesh', 'Rajesh', 'Naresh',
    'Sunita', 'Geeta', 'Rita', 'Seema', 'Meena', 'Rekha', 'Lata', 'Sushma', 'Kavita', 'Vandana'
]

LAST_NAMES = [
    'Kumar', 'Sharma', 'Patel', 'Singh', 'Verma', 'Rao', 'Reddy', 'Nair', 'Iyer', 'Desai',
    'Joshi', 'Gupta', 'Agarwal', 'Mehta', 'Shah', 'Das', 'Pillai', 'Menon', 'Bhat', 'Kulkarni',
    'Chopra', 'Kapoor', 'Malhotra', 'Sethi', 'Khanna', 'Arora', 'Bhatia', 'Sinha', 'Jain', 'Bansal',
    'Pandey', 'Mishra', 'Tiwari', 'Dubey', 'Shukla', 'Saxena', 'Trivedi', 'Chaturvedi', 'Dixit',
    'Yadav', 'Chauhan', 'Rathore', 'Thakur', 'Bisht', 'Negi', 'Rawat', 'Bhatt'
]

# Comprehensive medicine list (150+ products)
MEDICINES = [
    # Pain Relief & Fever (20)
    {'name': 'Paracetamol 500mg', 'manufacturer': 'Sun Pharma', 'category': 'Pain Relief', 'usage': 'Fever, Headache, Body Pain', 'price_range': (10, 20)},
    {'name': 'Dolo 650mg', 'manufacturer': 'Micro Labs', 'category': 'Pain Relief', 'usage': 'Fever, Pain', 'price_range': (15, 25)},
    {'name': 'Crocin Advance', 'manufacturer': 'GSK', 'category': 'Pain Relief', 'usage': 'Fast Fever Relief', 'price_range': (18, 28)},
    {'name': 'Ibuprofen 400mg', 'manufacturer': 'Abbott', 'category': 'Pain Relief', 'usage': 'Pain, Inflammation', 'price_range': (20, 35)},
    {'name': 'Brufen 200mg', 'manufacturer': 'Abbott', 'category': 'Pain Relief', 'usage': 'Pain Relief', 'price_range': (12, 22)},
    {'name': 'Combiflam', 'manufacturer': 'Sanofi', 'category': 'Pain Relief', 'usage': 'Fever, Pain, Inflammation', 'price_range': (25, 40)},
    {'name': 'Disprin', 'manufacturer': 'Reckitt Benckiser', 'category': 'Pain Relief', 'usage': 'Headache, Fever', 'price_range': (8, 15)},
    {'name': 'Saridon', 'manufacturer': 'Piramal', 'category': 'Pain Relief', 'usage': 'Headache Relief', 'price_range': (10, 18)},
    {'name': 'Diclofenac 50mg', 'manufacturer': 'Cipla', 'category': 'Pain Relief', 'usage': 'Joint Pain, Arthritis', 'price_range': (15, 30)},
    {'name': 'Voveran 50mg', 'manufacturer': 'Novartis', 'category': 'Pain Relief', 'usage': 'Inflammation, Pain', 'price_range': (30, 50)},
    {'name': 'Aceclofenac 100mg', 'manufacturer': 'Lupin', 'category': 'Pain Relief', 'usage': 'Pain, Inflammation', 'price_range': (20, 35)},
    {'name': 'Nimesulide 100mg', 'manufacturer': 'Dr. Reddy\'s', 'category': 'Pain Relief', 'usage': 'Pain, Fever', 'price_range': (12, 25)},
    {'name': 'Meftal Spas', 'manufacturer': 'Blue Cross', 'category': 'Pain Relief', 'usage': 'Abdominal Pain, Cramps', 'price_range': (35, 55)},
    {'name': 'Aspirin 75mg', 'manufacturer': 'Bayer', 'category': 'Pain Relief', 'usage': 'Pain, Heart Protection', 'price_range': (15, 28)},
    {'name': 'Naproxen 250mg', 'manufacturer': 'Alkem', 'category': 'Pain Relief', 'usage': 'Pain, Inflammation', 'price_range': (18, 32)},
    {'name': 'Tramadol 50mg', 'manufacturer': 'Sun Pharma', 'category': 'Pain Relief', 'usage': 'Moderate to Severe Pain', 'price_range': (40, 70)},
    {'name': 'Etoricoxib 60mg', 'manufacturer': 'MSD', 'category': 'Pain Relief', 'usage': 'Arthritis Pain', 'price_range': (45, 75)},
    {'name': 'Zerodol P', 'manufacturer': 'Ipca', 'category': 'Pain Relief', 'usage': 'Pain, Fever', 'price_range': (28, 45)},
    {'name': 'Volini Gel 30g', 'manufacturer': 'Ranbaxy', 'category': 'Pain Relief', 'usage': 'Muscle Pain Relief', 'price_range': (85, 125)},
    {'name': 'Moov Cream 50g', 'manufacturer': 'Reckitt Benckiser', 'category': 'Pain Relief', 'usage': 'Muscle Ache', 'price_range': (75, 110)},
    
    # Antibiotics (25)
    {'name': 'Amoxicillin 250mg', 'manufacturer': 'Dr. Reddy\'s', 'category': 'Antibiotic', 'usage': 'Bacterial Infection', 'price_range': (100, 150)},
    {'name': 'Amoxicillin 500mg', 'manufacturer': 'Cipla', 'category': 'Antibiotic', 'usage': 'Bacterial Infection', 'price_range': (150, 200)},
    {'name': 'Azithromycin 250mg', 'manufacturer': 'Alkem', 'category': 'Antibiotic', 'usage': 'Respiratory Infection', 'price_range': (120, 180)},
    {'name': 'Azithromycin 500mg', 'manufacturer': 'Sun Pharma', 'category': 'Antibiotic', 'usage': 'Bacterial Infection', 'price_range': (160, 220)},
    {'name': 'Ciprofloxacin 500mg', 'manufacturer': 'Ranbaxy', 'category': 'Antibiotic', 'usage': 'UTI, Bacterial Infection', 'price_range': (80, 130)},
    {'name': 'Cephalexin 250mg', 'manufacturer': 'Abbott', 'category': 'Antibiotic', 'usage': 'Skin Infection', 'price_range': (90, 140)},
    {'name': 'Doxycycline 100mg', 'manufacturer': 'Lupin', 'category': 'Antibiotic', 'usage': 'Bacterial Infection', 'price_range': (70, 120)},
    {'name': 'Levofloxacin 500mg', 'manufacturer': 'Wockhardt', 'category': 'Antibiotic', 'usage': 'Respiratory Infection', 'price_range': (110, 170)},
    {'name': 'Metronidazole 400mg', 'manufacturer': 'Cipla', 'category': 'Antibiotic', 'usage': 'Bacterial, Parasitic Infection', 'price_range': (30, 60)},
    {'name': 'Ofloxacin 200mg', 'manufacturer': 'Dr. Reddy\'s', 'category': 'Antibiotic', 'usage': 'UTI, Infection', 'price_range': (50, 90)},
    {'name': 'Augmentin 625mg', 'manufacturer': 'GSK', 'category': 'Antibiotic', 'usage': 'Bacterial Infection', 'price_range': (180, 250)},
    {'name': 'Cefixime 200mg', 'manufacturer': 'Lupin', 'category': 'Antibiotic', 'usage': 'Bacterial Infection', 'price_range': (140, 200)},
    {'name': 'Clarithromycin 250mg', 'manufacturer': 'Abbott', 'category': 'Antibiotic', 'usage': 'Respiratory Infection', 'price_range': (120, 180)},
    {'name': 'Clindamycin 150mg', 'manufacturer': 'Pfizer', 'category': 'Antibiotic', 'usage': 'Skin Infection', 'price_range': (100, 160)},
    {'name': 'Co-Amoxiclav 375mg', 'manufacturer': 'Alkem', 'category': 'Antibiotic', 'usage': 'Bacterial Infection', 'price_range': (150, 210)},
    {'name': 'Erythromycin 250mg', 'manufacturer': 'Abbott', 'category': 'Antibiotic', 'usage': 'Bacterial Infection', 'price_range': (60, 100)},
    {'name': 'Gentamicin Injection', 'manufacturer': 'Sun Pharma', 'category': 'Antibiotic', 'usage': 'Serious Infection', 'price_range': (90, 150)},
    {'name': 'Linezolid 600mg', 'manufacturer': 'Pfizer', 'category': 'Antibiotic', 'usage': 'Serious Bacterial Infection', 'price_range': (350, 500)},
    {'name': 'Moxifloxacin 400mg', 'manufacturer': 'Bayer', 'category': 'Antibiotic', 'usage': 'Respiratory Infection', 'price_range': (200, 300)},
    {'name': 'Nitrofurantoin 100mg', 'manufacturer': 'Cipla', 'category': 'Antibiotic', 'usage': 'UTI', 'price_range': (70, 110)},
    {'name': 'Norfloxacin 400mg', 'manufacturer': 'Ranbaxy', 'category': 'Antibiotic', 'usage': 'UTI', 'price_range': (40, 70)},
    {'name': 'Penicillin V 250mg', 'manufacturer': 'GSK', 'category': 'Antibiotic', 'usage': 'Bacterial Infection', 'price_range': (50, 90)},
    {'name': 'Rifampicin 450mg', 'manufacturer': 'Lupin', 'category': 'Antibiotic', 'usage': 'Tuberculosis', 'price_range': (120, 180)},
    {'name': 'Tetracycline 250mg', 'manufacturer': 'Pfizer', 'category': 'Antibiotic', 'usage': 'Bacterial Infection', 'price_range': (45, 80)},
    {'name': 'Vancomycin 500mg', 'manufacturer': 'Sun Pharma', 'category': 'Antibiotic', 'usage': 'Serious Infection', 'price_range': (450, 650)},
    
    # Gastric & Digestive (20)
    {'name': 'Omeprazole 20mg', 'manufacturer': 'Lupin', 'category': 'Antacid', 'usage': 'Acidity, Gastritis, Ulcer', 'price_range': (40, 65)},
    {'name': 'Pantoprazole 40mg', 'manufacturer': 'Intas', 'category': 'Antacid', 'usage': 'Acid Reflux, GERD', 'price_range': (45, 70)},
    {'name': 'Rabeprazole 20mg', 'manufacturer': 'Dr. Reddy\'s', 'category': 'Antacid', 'usage': 'Acidity, Ulcer', 'price_range': (50, 75)},
    {'name': 'Esomeprazole 40mg', 'manufacturer': 'Cipla', 'category': 'Antacid', 'usage': 'GERD, Ulcer', 'price_range': (55, 85)},
    {'name': 'Ranitidine 150mg', 'manufacturer': 'GSK', 'category': 'Antacid', 'usage': 'Acidity, Heartburn', 'price_range': (25, 45)},
    {'name': 'Famotidine 20mg', 'manufacturer': 'Merck', 'category': 'Antacid', 'usage': 'Acidity, Ulcer', 'price_range': (30, 50)},
    {'name': 'Domperidone 10mg', 'manufacturer': 'Cipla', 'category': 'Antiemetic', 'usage': 'Nausea, Vomiting', 'price_range': (20, 40)},
    {'name': 'Ondansetron 4mg', 'manufacturer': 'Dr. Reddy\'s', 'category': 'Antiemetic', 'usage': 'Nausea, Vomiting', 'price_range': (35, 60)},
    {'name': 'Metoclopramide 10mg', 'manufacturer': 'Sun Pharma', 'category': 'Antiemetic', 'usage': 'Nausea, GERD', 'price_range': (15, 30)},
    {'name': 'Lactobacillus Capsules', 'manufacturer': 'Abbott', 'category': 'Probiotic', 'usage': 'Digestive Health', 'price_range': (80, 130)},
    {'name': 'Digestive Enzymes', 'manufacturer': 'Himalaya', 'category': 'Digestive Aid', 'usage': 'Digestion Support', 'price_range': (65, 100)},
    {'name': 'Antacid Gel 200ml', 'manufacturer': 'Sanofi', 'category': 'Antacid', 'usage': 'Acidity, Gas', 'price_range': (70, 110)},
    {'name': 'Gas-X Tablets', 'manufacturer': 'Novartis', 'category': 'Antiflatulent', 'usage': 'Gas, Bloating', 'price_range': (40, 65)},
    {'name': 'Loperamide 2mg', 'manufacturer': 'Johnson & Johnson', 'category': 'Antidiarrheal', 'usage': 'Diarrhea', 'price_range': (30, 50)},
    {'name': 'ORS Powder', 'manufacturer': 'FDC', 'category': 'Rehydration', 'usage': 'Dehydration, Diarrhea', 'price_range': (10, 20)},
    {'name': 'Bisacodyl 5mg', 'manufacturer': 'Cipla', 'category': 'Laxative', 'usage': 'Constipation', 'price_range': (25, 45)},
    {'name': 'Lactulose Syrup 200ml', 'manufacturer': 'Abbott', 'category': 'Laxative', 'usage': 'Constipation', 'price_range': (95, 145)},
    {'name': 'Isabgol Husk 100g', 'manufacturer': 'Dabur', 'category': 'Fiber Supplement', 'usage': 'Constipation, Digestive Health', 'price_range': (55, 85)},
    {'name': 'Sucralfate Suspension 200ml', 'manufacturer': 'Sun Pharma', 'category': 'Ulcer Treatment', 'usage': 'Stomach Ulcer', 'price_range': (85, 130)},
    {'name': 'Simethicone Drops', 'manufacturer': 'Pfizer', 'category': 'Antiflatulent', 'usage': 'Gas Relief', 'price_range': (50, 80)},
    
    # Allergy & Cold (15)
    {'name': 'Cetirizine 10mg', 'manufacturer': 'Cipla', 'category': 'Antihistamine', 'usage': 'Allergy, Cold, Runny Nose', 'price_range': (20, 35)},
    {'name': 'Loratadine 10mg', 'manufacturer': 'Sun Pharma', 'category': 'Antihistamine', 'usage': 'Allergy Relief', 'price_range': (25, 40)},
    {'name': 'Fexofenadine 120mg', 'manufacturer': 'Sanofi', 'category': 'Antihistamine', 'usage': 'Seasonal Allergy', 'price_range': (30, 50)},
    {'name': 'Levocetirizine 5mg', 'manufacturer': 'Dr. Reddy\'s', 'category': 'Antihistamine', 'usage': 'Allergy, Urticaria', 'price_range': (25, 45)},
    {'name': 'Montelukast 10mg', 'manufacturer': 'Cipla', 'category': 'Antiallergic', 'usage': 'Asthma, Allergy', 'price_range': (50, 85)},
    {'name': 'Chlorpheniramine 4mg', 'manufacturer': 'GSK', 'category': 'Antihistamine', 'usage': 'Allergy, Cold', 'price_range': (12, 25)},
    {'name': 'Cough Syrup 100ml', 'manufacturer': 'Himalaya', 'category': 'Cough Medicine', 'usage': 'Cough, Cold', 'price_range': (75, 110)},
    {'name': 'Benadryl Cough Syrup 100ml', 'manufacturer': 'Johnson & Johnson', 'category': 'Cough Medicine', 'usage': 'Dry Cough', 'price_range': (95, 135)},
    {'name': 'Corex Cough Syrup 100ml', 'manufacturer': 'Pfizer', 'category': 'Cough Medicine', 'usage': 'Wet Cough', 'price_range': (80, 120)},
    {'name': 'Vicks VapoRub 25ml', 'manufacturer': 'P&G', 'category': 'Cough & Cold', 'usage': 'Congestion Relief', 'price_range': (55, 85)},
    {'name': 'Nasal Decongestant Spray', 'manufacturer': 'GSK', 'category': 'Decongestant', 'usage': 'Nasal Congestion', 'price_range': (70, 110)},
    {'name': 'Pseudoephedrine 30mg', 'manufacturer': 'Pfizer', 'category': 'Decongestant', 'usage': 'Nasal Congestion', 'price_range': (35, 60)},
    {'name': 'Ambroxol 30mg', 'manufacturer': 'Cipla', 'category': 'Mucolytic', 'usage': 'Productive Cough', 'price_range': (40, 65)},
    {'name': 'Bromhexine 8mg', 'manufacturer': 'Sun Pharma', 'category': 'Mucolytic', 'usage': 'Cough with Mucus', 'price_range': (30, 55)},
    {'name': 'Phenylephrine Nasal Drops', 'manufacturer': 'Abbott', 'category': 'Decongestant', 'usage': 'Nasal Congestion', 'price_range': (45, 75)},
    
    # Diabetes (12)
    {'name': 'Metformin 500mg', 'manufacturer': 'Mankind', 'category': 'Antidiabetic', 'usage': 'Type 2 Diabetes', 'price_range': (30, 50)},
    {'name': 'Metformin 850mg', 'manufacturer': 'Cipla', 'category': 'Antidiabetic', 'usage': 'Type 2 Diabetes', 'price_range': (40, 65)},
    {'name': 'Glimepiride 1mg', 'manufacturer': 'Sun Pharma', 'category': 'Antidiabetic', 'usage': 'Type 2 Diabetes', 'price_range': (35, 60)},
    {'name': 'Glimepiride 2mg', 'manufacturer': 'Torrent', 'category': 'Antidiabetic', 'usage': 'Type 2 Diabetes', 'price_range': (45, 75)},
    {'name': 'Glipizide 5mg', 'manufacturer': 'Pfizer', 'category': 'Antidiabetic', 'usage': 'Type 2 Diabetes', 'price_range': (40, 70)},
    {'name': 'Sitagliptin 50mg', 'manufacturer': 'MSD', 'category': 'Antidiabetic', 'usage': 'Type 2 Diabetes', 'price_range': (120, 180)},
    {'name': 'Vildagliptin 50mg', 'manufacturer': 'Novartis', 'category': 'Antidiabetic', 'usage': 'Type 2 Diabetes', 'price_range': (110, 170)},
    {'name': 'Pioglitazone 15mg', 'manufacturer': 'Dr. Reddy\'s', 'category': 'Antidiabetic', 'usage': 'Type 2 Diabetes', 'price_range': (80, 130)},
    {'name': 'Gliclazide 80mg', 'manufacturer': 'Serdia', 'category': 'Antidiabetic', 'usage': 'Type 2 Diabetes', 'price_range': (50, 85)},
    {'name': 'Insulin Glargine Vial', 'manufacturer': 'Sanofi', 'category': 'Insulin', 'usage': 'Diabetes', 'price_range': (800, 1200)},
    {'name': 'Insulin Aspart Vial', 'manufacturer': 'Novo Nordisk', 'category': 'Insulin', 'usage': 'Diabetes', 'price_range': (750, 1100)},
    {'name': 'Glucometer Strips 25s', 'manufacturer': 'Abbott', 'category': 'Diabetes Care', 'usage': 'Blood Glucose Testing', 'price_range': (450, 650)},
    
    # Cardiovascular (15)
    {'name': 'Atorvastatin 10mg', 'manufacturer': 'Torrent', 'category': 'Cholesterol', 'usage': 'High Cholesterol', 'price_range': (50, 80)},
    {'name': 'Atorvastatin 20mg', 'manufacturer': 'Pfizer', 'category': 'Cholesterol', 'usage': 'High Cholesterol', 'price_range': (70, 110)},
    {'name': 'Rosuvastatin 10mg', 'manufacturer': 'Sun Pharma', 'category': 'Cholesterol', 'usage': 'High Cholesterol', 'price_range': (60, 95)},
    {'name': 'Rosuvastatin 20mg', 'manufacturer': 'AstraZeneca', 'category': 'Cholesterol', 'usage': 'High Cholesterol', 'price_range': (85, 130)},
    {'name': 'Amlodipine 5mg', 'manufacturer': 'Cipla', 'category': 'Antihypertensive', 'usage': 'High Blood Pressure', 'price_range': (25, 45)},
    {'name': 'Amlodipine 10mg', 'manufacturer': 'Pfizer', 'category': 'Antihypertensive', 'usage': 'High Blood Pressure', 'price_range': (35, 60)},
    {'name': 'Telmisartan 40mg', 'manufacturer': 'Glenmark', 'category': 'Antihypertensive', 'usage': 'High Blood Pressure', 'price_range': (45, 75)},
    {'name': 'Losartan 50mg', 'manufacturer': 'Merck', 'category': 'Antihypertensive', 'usage': 'High Blood Pressure', 'price_range': (40, 70)},
    {'name': 'Enalapril 5mg', 'manufacturer': 'Dr. Reddy\'s', 'category': 'Antihypertensive', 'usage': 'Hypertension', 'price_range': (30, 55)},
    {'name': 'Metoprolol 50mg', 'manufacturer': 'AstraZeneca', 'category': 'Beta Blocker', 'usage': 'Blood Pressure, Heart', 'price_range': (35, 60)},
    {'name': 'Atenolol 50mg', 'manufacturer': 'Cipla', 'category': 'Beta Blocker', 'usage': 'Hypertension, Angina', 'price_range': (25, 45)},
    {'name': 'Aspirin 75mg', 'manufacturer': 'Bayer', 'category': 'Antiplatelet', 'usage': 'Heart Protection', 'price_range': (15, 30)},
    {'name': 'Clopidogrel 75mg', 'manufacturer': 'Sun Pharma', 'category': 'Antiplatelet', 'usage': 'Blood Clot Prevention', 'price_range': (55, 90)},
    {'name': 'Digoxin 0.25mg', 'manufacturer': 'GSK', 'category': 'Cardiac Glycoside', 'usage': 'Heart Failure', 'price_range': (20, 40)},
    {'name': 'Nitroglycerin Spray', 'manufacturer': 'Pfizer', 'category': 'Antianginal', 'usage': 'Angina Attack', 'price_range': (180, 280)},
    
    # Vitamins & Supplements (20)
    {'name': 'Vitamin D3 60K', 'manufacturer': 'Cipla', 'category': 'Vitamin Supplement', 'usage': 'Vitamin D Deficiency', 'price_range': (80, 120)},
    {'name': 'Vitamin B12 1500mcg', 'manufacturer': 'Sun Pharma', 'category': 'Vitamin Supplement', 'usage': 'B12 Deficiency', 'price_range': (60, 95)},
    {'name': 'Vitamin C 500mg', 'manufacturer': 'HealthKart', 'category': 'Vitamin Supplement', 'usage': 'Immunity, Antioxidant', 'price_range': (40, 70)},
    {'name': 'Multivitamin Tablets', 'manufacturer': 'HealthKart', 'category': 'Vitamin Supplement', 'usage': 'General Health', 'price_range': (110, 170)},
    {'name': 'Calcium Tablets 500mg', 'manufacturer': 'Sun Pharma', 'category': 'Mineral Supplement', 'usage': 'Bone Health', 'price_range': (55, 85)},
    {'name': 'Calcium + Vitamin D3', 'manufacturer': 'Cipla', 'category': 'Mineral Supplement', 'usage': 'Bone Health', 'price_range': (70, 110)},
    {'name': 'Iron Tablets 100mg', 'manufacturer': 'Abbott', 'category': 'Mineral Supplement', 'usage': 'Anemia', 'price_range': (45, 75)},
    {'name': 'Folic Acid 5mg', 'manufacturer': 'Dr. Reddy\'s', 'category': 'Vitamin Supplement', 'usage': 'Anemia, Pregnancy', 'price_range': (15, 30)},
    {'name': 'Omega-3 Fish Oil', 'manufacturer': 'HealthKart', 'category': 'Supplement', 'usage': 'Heart, Brain Health', 'price_range': (250, 400)},
    {'name': 'Zinc Tablets 50mg', 'manufacturer': 'Sanofi', 'category': 'Mineral Supplement', 'usage': 'Immunity, Skin Health', 'price_range': (50, 80)},
    {'name': 'Magnesium 400mg', 'manufacturer': 'Nature\'s Bounty', 'category': 'Mineral Supplement', 'usage': 'Muscle, Nerve Health', 'price_range': (60, 100)},
    {'name': 'Vitamin E 400 IU', 'manufacturer': 'HealthKart', 'category': 'Vitamin Supplement', 'usage': 'Antioxidant, Skin', 'price_range': (55, 90)},
    {'name': 'Biotin 10000mcg', 'manufacturer': 'HealthKart', 'category': 'Vitamin Supplement', 'usage': 'Hair, Skin, Nails', 'price_range': (65, 105)},
    {'name': 'Protein Powder 500g', 'manufacturer': 'Optimum Nutrition', 'category': 'Supplement', 'usage': 'Muscle Building', 'price_range': (1200, 1800)},
    {'name': 'Vitamin A 5000 IU', 'manufacturer': 'Sun Pharma', 'category': 'Vitamin Supplement', 'usage': 'Vision, Immunity', 'price_range': (35, 60)},
    {'name': 'Vitamin K2 100mcg', 'manufacturer': 'HealthKart', 'category': 'Vitamin Supplement', 'usage': 'Bone, Heart Health', 'price_range': (70, 115)},
    {'name': 'Coenzyme Q10 100mg', 'manufacturer': 'HealthKart', 'category': 'Supplement', 'usage': 'Heart, Energy', 'price_range': (180, 280)},
    {'name': 'Glucosamine Chondroitin', 'manufacturer': 'Abbott', 'category': 'Supplement', 'usage': 'Joint Health', 'price_range': (350, 550)},
    {'name': 'Probiotics 10 Billion CFU', 'manufacturer': 'HealthKart', 'category': 'Supplement', 'usage': 'Gut Health', 'price_range': (450, 700)},
    {'name': 'Collagen Peptides', 'manufacturer': 'HealthKart', 'category': 'Supplement', 'usage': 'Skin, Joint Health', 'price_range': (800, 1200)},
    
    # Additional Common Medicines (20)
    {'name': 'Betadine Solution 100ml', 'manufacturer': 'Win-Medicare', 'category': 'Antiseptic', 'usage': 'Wound Cleaning', 'price_range': (95, 145)},
    {'name': 'Dettol Liquid 500ml', 'manufacturer': 'Reckitt Benckiser', 'category': 'Antiseptic', 'usage': 'Wound Cleaning, Disinfection', 'price_range': (135, 195)},
    {'name': 'Savlon Antiseptic Cream', 'manufacturer': 'Johnson & Johnson', 'category': 'Antiseptic', 'usage': 'Minor Cuts, Burns', 'price_range': (55, 85)},
    {'name': 'Band-Aid 10 Strips', 'manufacturer': 'Johnson & Johnson', 'category': 'First Aid', 'usage': 'Wound Protection', 'price_range': (35, 55)},
    {'name': 'Cotton Roll 100g', 'manufacturer': 'Various', 'category': 'First Aid', 'usage': 'Wound Dressing', 'price_range': (40, 65)},
    {'name': 'Gauze Bandage 4inch', 'manufacturer': 'Various', 'category': 'First Aid', 'usage': 'Wound Dressing', 'price_range': (25, 45)},
    {'name': 'Digital Thermometer', 'manufacturer': 'Omron', 'category': 'Medical Device', 'usage': 'Temperature Measurement', 'price_range': (180, 280)},
    {'name': 'BP Monitor Digital', 'manufacturer': 'Omron', 'category': 'Medical Device', 'usage': 'Blood Pressure Check', 'price_range': (1800, 2800)},
    {'name': 'Nebulizer Machine', 'manufacturer': 'Omron', 'category': 'Medical Device', 'usage': 'Respiratory Treatment', 'price_range': (2500, 4000)},
    {'name': 'Hand Sanitizer 500ml', 'manufacturer': 'Dettol', 'category': 'Hygiene', 'usage': 'Hand Disinfection', 'price_range': (85, 135)},
    {'name': 'Surgical Face Masks 50s', 'manufacturer': 'Various', 'category': 'PPE', 'usage': 'Protection', 'price_range': (120, 200)},
    {'name': 'N95 Mask 10s', 'manufacturer': '3M', 'category': 'PPE', 'usage': 'High Protection', 'price_range': (280, 450)},
    {'name': 'Surgical Gloves 100s', 'manufacturer': 'Ansell', 'category': 'PPE', 'usage': 'Protection', 'price_range': (250, 400)},
    {'name': 'Eye Drops Lubricant', 'manufacturer': 'Allergan', 'category': 'Eye Care', 'usage': 'Dry Eyes', 'price_range': (75, 125)},
    {'name': 'Antifungal Cream 15g', 'manufacturer': 'GSK', 'category': 'Dermatology', 'usage': 'Fungal Infection', 'price_range': (65, 105)},
    {'name': 'Hydrocortisone Cream', 'manufacturer': 'Abbott', 'category': 'Dermatology', 'usage': 'Skin Inflammation', 'price_range': (55, 90)},
    {'name': 'Clotrimazole Cream', 'manufacturer': 'Bayer', 'category': 'Dermatology', 'usage': 'Antifungal', 'price_range': (60, 95)},
    {'name': 'Calamine Lotion 100ml', 'manufacturer': 'Lacto', 'category': 'Dermatology', 'usage': 'Skin Irritation', 'price_range': (45, 75)},
    {'name': 'Sunscreen SPF 50 100ml', 'manufacturer': 'Neutrogena', 'category': 'Skin Care', 'usage': 'Sun Protection', 'price_range': (280, 450)},
    {'name': 'Petroleum Jelly 100g', 'manufacturer': 'Vaseline', 'category': 'Skin Care', 'usage': 'Skin Moisturizer', 'price_range': (65, 105)},
]

# ============================================
# DATA GENERATION FUNCTIONS
# ============================================

def clear_existing_data(db):
    """Clear existing data from tables (except users)"""
    print("Clearing existing data...")
    cursor = db.cursor()
    
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE bill_items")
        cursor.execute("TRUNCATE TABLE bills")
        cursor.execute("TRUNCATE TABLE regular_purchases")
        cursor.execute("TRUNCATE TABLE supplier_purchases")
        cursor.execute("TRUNCATE TABLE products")
        cursor.execute("TRUNCATE TABLE customers")
        # Keep existing users or clear if needed
        cursor.execute("DELETE FROM users WHERE username NOT IN ('admin', 'cashier')")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        db.commit()
        print("✓ Existing data cleared")
    except Exception as e:
        print(f"Error clearing data: {e}")
        db.rollback()

def generate_staff_users(db):
    """Generate 5-6 staff users"""
    print("\nGenerating staff users...")
    cursor = db.cursor()
    
    count = 0
    for user in STAFF_USERS:
        hashed_pw = hash_password(user['password'])
        try:
            cursor.execute("""
                INSERT INTO users (username, password, full_name, role, email, phone)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE username = username
            """, (user['username'], hashed_pw, user['full_name'], user['role'], user['email'], user['phone']))
            count += 1
        except Exception as e:
            print(f"Error inserting user {user['username']}: {e}")
    
    db.commit()
    print(f"✓ Created {count} staff users")
    return count

def generate_customers(db, count=130, walkin_percentage=0.4):
    """Generate ~130 customers with 40% walk-ins"""
    print(f"\nGenerating {count} customers ({int(count * walkin_percentage)} walk-ins)...")
    cursor = db.cursor()
    
    regular_count = int(count * (1 - walkin_percentage))
    walkin_count = count - regular_count
    
    created = 0
    
    # Generate regular customers
    for i in range(regular_count):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        phone = f"+91-{random.randint(7000000000, 9999999999)}"
        email = f"{name.lower().replace(' ', '.')}@example.com"
        address = f"{random.randint(1, 999)} {random.choice(['MG Road', 'Park Street', 'Main Road', 'Station Road', 'Gandhi Nagar'])}, {random.choice(['Ahmedabad', 'Gandhinagar', 'Rajkot', 'Surat', 'Vadodara'])}"
        
        try:
            cursor.execute("""
                INSERT INTO customers (name, phone, email, address)
                VALUES (%s, %s, %s, %s)
            """, (name, phone, email, address))
            created += 1
        except Exception as e:
            # Skip duplicates
            pass
    
    # Generate walk-in customers (generic names with numbers)
    for i in range(walkin_count):
        name = f"Walk-in Customer {i+1}"
        phone = f"+91-{random.randint(7000000000, 9999999999)}"
        
        try:
            cursor.execute("""
                INSERT INTO customers (name, phone, email, address)
                VALUES (%s, %s, NULL, NULL)
            """, (name, phone))
            created += 1
        except Exception as e:
            # Skip duplicates
            pass
    
    db.commit()
    print(f"✓ Created {created} customers")
    return created

def generate_products(db, min_count=100, max_count=200, low_stock_percentage=0.1):
    """Generate 100-200 products with 10% low stock"""
    product_count = random.randint(min_count, max_count)
    print(f"\nGenerating {product_count} products ({int(product_count * low_stock_percentage)} low stock)...")
    cursor = db.cursor()
    
    # Determine how many medicines to use (randomize selection)
    available_medicines = MEDICINES.copy()
    random.shuffle(available_medicines)
    
    # Calculate how many low stock items
    low_stock_count = int(product_count * low_stock_percentage)
    normal_stock_count = product_count - low_stock_count
    
    created = 0
    shelf_locations = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4', 'C1', 'C2', 'C3', 'C4', 
                       'D1', 'D2', 'D3', 'D4', 'E1', 'E2', 'E3', 'E4', 'F1', 'F2', 'F3', 'F4',
                       'G1', 'G2', 'G3', 'G4', 'H1', 'H2', 'H3', 'H4']
    
    for i in range(product_count):
        # Cycle through medicines if we need more products than available medicines
        med = available_medicines[i % len(available_medicines)]
        
        # Add variation to product name if using duplicates
        name_variation = "" if i < len(available_medicines) else f" Pack-{(i // len(available_medicines)) + 1}"
        name = med['name'] + name_variation
        
        price = round(random.uniform(med['price_range'][0], med['price_range'][1]), 2)
        
        # Determine stock level
        if i < low_stock_count:
            # Low stock item (below minimum threshold)
            min_stock_level = random.randint(15, 30)
            stock_quantity = random.randint(0, min_stock_level - 1)
        else:
            # Normal stock item
            min_stock_level = random.randint(15, 30)
            stock_quantity = random.randint(min_stock_level + 10, 500)
        
        shelf_location = random.choice(shelf_locations)
        batch_number = f"BATCH-{random.randint(1000, 9999)}-{random.randint(100, 999)}"
        expiry_date = (datetime.now() + timedelta(days=random.randint(180, 1095))).strftime('%Y-%m-%d')
        
        try:
            cursor.execute("""
                INSERT INTO products (name, manufacturer, price, stock_quantity, min_stock_level, 
                                    shelf_location, category, usage_type, batch_number, expiry_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, med['manufacturer'], price, stock_quantity, min_stock_level, 
                  shelf_location, med['category'], med['usage'], batch_number, expiry_date))
            created += 1
        except Exception as e:
            print(f"Error inserting product {name}: {e}")
    
    db.commit()
    print(f"✓ Created {created} products")
    return created

def get_sales_multiplier(date):
    """Get sales multiplier based on real trends"""
    # Weekend boost (Friday-Sunday)
    weekend_multiplier = 1.3 if date.weekday() >= 4 else 1.0
    
    # Monthly patterns (higher at month start and end)
    day_of_month = date.day
    if day_of_month <= 5 or day_of_month >= 25:
        monthly_multiplier = 1.2
    else:
        monthly_multiplier = 1.0
    
    # Seasonal patterns (more sales in winter and monsoon)
    month = date.month
    if month in [11, 12, 1, 2]:  # Winter
        seasonal_multiplier = 1.25
    elif month in [6, 7, 8]:  # Monsoon
        seasonal_multiplier = 1.15
    elif month in [4, 5]:  # Summer
        seasonal_multiplier = 1.1
    else:
        seasonal_multiplier = 1.0
    
    # Festival season boost (Oct-Nov)
    festival_multiplier = 1.2 if month in [10, 11] else 1.0
    
    return weekend_multiplier * monthly_multiplier * seasonal_multiplier * festival_multiplier

def get_time_of_day_multiplier():
    """Get time preference for bill generation"""
    # Higher probability for morning (8-12) and evening (17-21)
    hour_weights = {
        8: 0.08, 9: 0.12, 10: 0.15, 11: 0.14, 12: 0.10,  # Morning rush
        13: 0.04, 14: 0.03, 15: 0.04, 16: 0.06,           # Afternoon lull
        17: 0.08, 18: 0.10, 19: 0.12, 20: 0.08, 21: 0.06  # Evening rush
    }
    return random.choices(list(hour_weights.keys()), weights=list(hour_weights.values()))[0]

def generate_bills_for_year(db):
    """Generate 1 year of daily sales (10-15 transactions per day)"""
    print("\nGenerating 1 year of sales data...")
    cursor = db.cursor()
    
    # Get all products and customers
    cursor.execute("SELECT id, name, price, stock_quantity FROM products WHERE stock_quantity > 0")
    products = cursor.fetchall()
    
    cursor.execute("SELECT id, name, phone FROM customers")
    customers = cursor.fetchall()
    
    cursor.execute("SELECT id FROM users WHERE role IN ('owner', 'cashier')")
    staff = cursor.fetchall()
    
    if not products or not customers or not staff:
        print("Error: Need products, customers, and staff to generate bills")
        return 0
    
    # Generate bills for past 1 year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    total_bills = 0
    current_date = start_date
    
    while current_date <= end_date:
        # Get sales multiplier for this date
        multiplier = get_sales_multiplier(current_date)
        
        # Determine number of bills for this day (10-15, modified by multiplier)
        base_bills = random.randint(10, 15)
        daily_bills = int(base_bills * multiplier)
        
        # Generate bills for this day
        for _ in range(daily_bills):
            # Random time during business hours
            hour = get_time_of_day_multiplier()
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            bill_datetime = current_date.replace(hour=hour, minute=minute, second=second)
            bill_number = f"INV-{bill_datetime.strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"
            
            # Select customer (80% registered, 20% walk-in)
            customer = random.choice(customers)
            customer_id = customer[0]
            customer_name = customer[1]
            customer_phone = customer[2] if len(customer) > 2 else None
            
            # Select staff member
            staff_id = random.choice(staff)[0]
            
            # Generate bill items (1-8 items per bill)
            num_items = random.choices([1, 2, 3, 4, 5, 6, 7, 8], 
                                      weights=[5, 15, 25, 25, 15, 10, 3, 2])[0]
            
            selected_products = random.sample(products, min(num_items, len(products)))
            
            subtotal = 0
            bill_items_data = []
            
            for product in selected_products:
                product_id = product[0]
                medicine_name = product[1]
                price = float(product[2])
                stock = product[3]
                
                quantity = random.choices([1,2], weights=[70,30])[0]
                # Skip bill if no valid items


                item_total = price * quantity
                subtotal += item_total

                bill_items_data.append((None, product_id, medicine_name, price, quantity, item_total))
            # Skip bill if no valid items
                if not bill_items_data: 
                   continue

            
            # Calculate GST and total
            gst = round(subtotal * 0.12, 2)  # 12% GST
            total_amount = round(subtotal + gst, 2)
            
            try:
                # Insert bill
                cursor.execute("""
                    INSERT INTO bills (bill_number, customer_id, customer_name, phone, 
                                     subtotal, gst, total_amount, bill_date, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (bill_number, customer_id, customer_name, customer_phone, 
                      subtotal, gst, total_amount, bill_datetime, staff_id))
                
                bill_id = cursor.lastrowid
                
                # Insert bill items
                for item in bill_items_data:
                    cursor.execute("""
                        INSERT INTO bill_items (bill_id, product_id, medicine_name, price, quantity, total_amount)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (bill_id,) + item[1:])
                
                # Update product stock (reduce by quantity sold)
                for item in bill_items_data:
                    if item[1]:  # if product_id exists
                        cursor.execute("""
                            UPDATE products 
                            SET stock_quantity = GREATEST(stock_quantity - %s, 0)
                            WHERE id = %s
                        """, (item[4], item[1]))
                
                total_bills += 1
                
                # Commit every 100 bills to avoid large transactions
                if total_bills % 100 == 0:
                    db.commit()
                    print(f"  Processed {total_bills} bills...", end='\r')
                
            except Exception as e:
                print(f"\nError creating bill for {current_date}: {e}")
                db.rollback()
        
        current_date += timedelta(days=1)
    
    db.commit()
    print(f"\n✓ Created {total_bills} bills over 1 year")
    return total_bills

def generate_regular_purchases(db):
    """Generate regular purchase patterns for customers"""
    print("\nGenerating regular purchase patterns...")
    cursor = db.cursor()
    
    # Get customers and products
    cursor.execute("SELECT id FROM customers WHERE name NOT LIKE 'Walk-in%' LIMIT 50")
    regular_customers = cursor.fetchall()
    
    cursor.execute("SELECT id, name FROM products WHERE category IN ('Antidiabetic', 'Antihypertensive', 'Cholesterol', 'Pain Relief') LIMIT 30")
    chronic_medicines = cursor.fetchall()
    
    if not regular_customers or not chronic_medicines:
        print("Skipping regular purchases - insufficient data")
        return 0
    
    count = 0
    for customer in regular_customers:
        # Each regular customer has 1-3 regular medicines
        num_regular_meds = random.choices([1, 2, 3], weights=[50, 35, 15])[0]
        selected_meds = random.sample(chronic_medicines, min(num_regular_meds, len(chronic_medicines)))
        
        for med in selected_meds:
            try:
                cursor.execute("""
                    INSERT INTO regular_purchases (customer_id, product_id, medicine_name, default_quantity)
                    VALUES (%s, %s, %s, %s)
                """, (customer[0], med[0], med[1], random.randint(1, 3)))
                count += 1
            except:
                pass
    
    db.commit()
    print(f"✓ Created {count} regular purchase patterns")
    return count

# ============================================
# MAIN EXECUTION
# ============================================

def main():
    print("="*60)
    print("Medical Store Dummy Data Generator")
    print("="*60)
    
    db = get_db()
    if not db:
        print("Failed to connect to database. Exiting.")
        return
    
    try:
        # Clear existing data
        clear_existing_data(db)
        
        # Generate data
        staff_count = generate_staff_users(db)
        customer_count = generate_customers(db, count=130, walkin_percentage=0.4)
        product_count = generate_products(db, min_count=100, max_count=200, low_stock_percentage=0.1)
        bill_count = generate_bills_for_year(db)
        regular_purchases_count = generate_regular_purchases(db)
        
        print("\n" + "="*60)
        print("DATA GENERATION COMPLETE!")
        print("="*60)
        print(f"Staff Users:          {staff_count}")
        print(f"Customers:            {customer_count}")
        print(f"Products:             {product_count}")
        print(f"Bills (1 year):       {bill_count}")
        print(f"Regular Purchases:    {regular_purchases_count}")
        print("="*60)
        print("\nLogin Credentials:")
        print("-" * 60)
        print("Admin:   username='admin'   password='admin123'")
        print("Cashier: username='cashier' password='cashier123'")
        for user in STAFF_USERS:
            print(f"{user['role'].title():8} username='{user['username']}' password='{user['password']}'")
        print("="*60)
        
    except Exception as e:
        print(f"\nError during data generation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()
