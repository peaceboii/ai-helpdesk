import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

def main():
    # Load raw data
    df = pd.read_csv('raw_tickets.csv')
    
    # Map ticket types to the target categories
    def map_category(ticket_type):
        if ticket_type == 'Technical issue':
            return 'Technical'
        elif ticket_type in ['Billing inquiry', 'Refund request']:
            return 'Billing'
        else:
            return 'General'
            
    df['Category'] = df['Ticket Type'].apply(map_category)
    
    # Add synthetic HR data
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
    
    # Generate 500 HR tickets by sampling
    hr_data = []
    np.random.seed(42)
    for _ in range(500):
        idx = np.random.randint(0, len(hr_subjects))
        hr_data.append({
            'Ticket Subject': hr_subjects[idx],
            'Ticket Description': hr_descriptions[idx] + " " + hr_subjects[idx], # some variation
            'Category': 'HR'
        })
        
    hr_df = pd.DataFrame(hr_data)
    
    # Select relevant columns from main dataset
    main_df = df[['Ticket Subject', 'Ticket Description', 'Category']].copy()
    
    # Combine
    final_df = pd.concat([main_df, hr_df], ignore_index=True)
    
    # Shuffle
    final_df = final_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Rename columns to Subject and Body
    final_df.rename(columns={'Ticket Subject': 'Subject', 'Ticket Description': 'Body'}, inplace=True)
    
    # Handle missing values
    final_df.fillna('', inplace=True)
    
    # Split into train and test
    train_df, test_df = train_test_split(final_df, test_size=0.2, random_state=42, stratify=final_df['Category'])
    
    train_df.to_csv('train.csv', index=False)
    test_df.to_csv('test.csv', index=False)
    print("Created train.csv and test.csv")
    print("Class distribution in train:")
    print(train_df['Category'].value_counts())

if __name__ == '__main__':
    main()
