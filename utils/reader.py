import pandas as pd
from pandas.io.sas.sas_constants import dataset_length
import json

def xlsx_reader(filename):
    df=pd.read_excel(filename)
    return df

filename = r"C:\Users\netadmin\Documents\Cursor_Projects\bar_load_assistent\config_data\dummy_data.xlsx"
data = xlsx_reader(filename)
print(data)
list = []
dict = {}
for index, row in data.iterrows():
    name = row['FirstName'] + ' ' + row['SureName']
    weight = row['Weight']
    squat = row['Squat1']
    filename = row['FirstName'] + '_' + row['SureName'] + '.json'
    file = {
        'declared_weight': squat,
        'first': row['FirstName'],
        'sure_name': row['SureName']
    }
    print(file)
    with open(filename, 'w') as f:
        f.write(json.dumps(file, indent=4))



