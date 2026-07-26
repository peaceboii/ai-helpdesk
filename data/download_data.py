import kagglehub
import shutil
import os

print("Downloading dataset...")
path = kagglehub.dataset_download("suraj520/customer-support-ticket-dataset")
print("Path to dataset files:", path)

# Copy the file to our data folder
csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
if csv_files:
    source = os.path.join(path, csv_files[0])
    destination = os.path.join(os.path.dirname(__file__), 'raw_tickets.csv')
    shutil.copy2(source, destination)
    print(f"Copied {csv_files[0]} to {destination}")
else:
    print("No CSV found in the downloaded dataset.")
