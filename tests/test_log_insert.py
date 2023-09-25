import random
from datetime import datetime
import sys
sys.path.insert(0,'..')

# Sample data for demonstration
sample_data = [
    {'id': '1', 'status': 'Success', 'response': 'Response Data 1'},
    {'id': '2', 'status': 'Error', 'response': 'Error Message'}
]

# Generate random timestamps for demonstration
for data in sample_data:
    data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Generate the INSERT statement
insert_statement = "INSERT INTO scheduler.logs (id, status, response, timestamp) VALUES"

for data in sample_data:
    values = f"('{data['id']}', '{data['status']}', '{data['response']}', '{data['timestamp']}')"
    insert_statement += f"\n{values},"

# Remove the trailing comma and add a semicolon to complete the statement
insert_statement = insert_statement.rstrip(',') + ';'

print(insert_statement)

#db.execute(insert_statement)