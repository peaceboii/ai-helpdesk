import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split

def main():
    # Load raw data
    data_dir = os.path.dirname(os.path.abspath(__file__))
    raw_path = os.path.join(data_dir, 'raw_tickets.csv')
    df = pd.read_csv(raw_path)
    
    # Smart classification mapping to fix noisy labels in the synthetic Kaggle dataset
    def map_category_smart(row):
        subj = str(row['Ticket Subject']).lower()
        desc = str(row['Ticket Description']).lower()
        text = subj + " " + desc
        
        # Check HR first
        hr_keywords = ["salary", "payroll", "employee id", "hr team", "bonus", "leave", "payslip", "resignation", "vacation"]
        if any(kw in text for kw in hr_keywords):
            return "HR"
            
        billing_keywords = ["invoice", "billing", "payment", "refund", "charge", "transaction", "pricing", "receipt", "double charged", "fee", "purchased", "price", "card", "pay"]
        tech_keywords = ["bug", "crash", "timeout", "server", "database", "api", "webhook", "timed out", "error", "connection", "port", "access", "locked", "reset", "forgotten", "credentials", "login", "password", "software", "glitch", "freeze"]
        
        bill_cnt = sum(1 for kw in billing_keywords if kw in text)
        tech_cnt = sum(1 for kw in tech_keywords if kw in text)
        
        if bill_cnt == 0 and tech_cnt == 0:
            return "General"
        elif bill_cnt > tech_cnt:
            return "Billing"
        elif tech_cnt > bill_cnt:
            return "Technical"
        else:
            return "Technical"
            
    df['Category'] = df.apply(map_category_smart, axis=1)
    
    # Rename columns to Subject and Body
    df.rename(columns={'Ticket Subject': 'Subject', 'Ticket Description': 'Body'}, inplace=True)
    
    # Add synthetic HR data template sources
    hr_subjects = ['Payroll issue', 'Leave request', 'Benefits question', 'Harassment complaint', 'Salary negotiation', 'Tax form W2', 'Onboarding delay', 'Promotion query', 'Health insurance update', 'Resignation notice']
    hr_descriptions = [
        "I have not received my paycheck for this month.",
        "I would like to apply for a 2-week leave for medical reasons.",
        "Can you clarify the vision benefits?",
        "I need to report an incident with a coworker.",
        "I want to discuss a salary adjustment for my role.",
        "When will I receive my W2 tax forms?",
        "My onboarding kit hasn't arrived yet.",
        "What are the criteria for the senior role promotion?",
        "I need to add a dependent to my health insurance.",
        "Please accept my formal resignation."
    ]
    
    # Filter dataset by class
    tech_df = df[df['Category'] == 'Technical'][['Subject', 'Body', 'Category']]
    bill_df = df[df['Category'] == 'Billing'][['Subject', 'Body', 'Category']]
    gen_df = df[df['Category'] == 'General'][['Subject', 'Body', 'Category']]
    
    target_samples = 1200
    
    # Downsample to balance
    tech_sample = tech_df.sample(n=min(len(tech_df), target_samples), random_state=42)
    bill_sample = bill_df.sample(n=min(len(bill_df), target_samples), random_state=42)
    gen_sample = gen_df.sample(n=min(len(gen_df), target_samples), random_state=42)
    
    # Upsample HR synthetically with context variations
    hr_data = []
    np.random.seed(42)
    for _ in range(target_samples):
        idx = np.random.randint(0, len(hr_subjects))
        prefix = np.random.choice([
            "Hello, ", "Hi Support, ", "Dear HR, ", "Please assist, ", 
            "Can you help? ", "URGENT: ", "", "Good morning, "
        ])
        hr_data.append({
            'Subject': hr_subjects[idx],
            'Body': prefix + hr_descriptions[idx] + " " + hr_subjects[idx],
            'Category': 'HR'
        })
        
    hr_sample = pd.DataFrame(hr_data)
    
    # Combine balanced sets
    final_df = pd.concat([tech_sample, bill_sample, gen_sample, hr_sample], ignore_index=True)
    final_df.fillna('', inplace=True)
    
    # Shuffle
    final_df = final_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Split into train and test
    train_df, test_df = train_test_split(final_df, test_size=0.2, random_state=42, stratify=final_df['Category'])
    
    train_df.to_csv(os.path.join(data_dir, 'train.csv'), index=False)
    test_df.to_csv(os.path.join(data_dir, 'test.csv'), index=False)
    print("Created balanced train.csv and test.csv")
    print("Class distribution in train:")
    print(train_df['Category'].value_counts())

if __name__ == '__main__':
    main()
