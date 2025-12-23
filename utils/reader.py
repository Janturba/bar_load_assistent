import pandas as pd
from pandas.io.sas.sas_constants import dataset_length


def xlsx_reader(filename):
    df=pd.read_excel(filename)
    return df

filename = "C:\\Users\\jantu\\PycharmProjects\\bar_load_assistent\\config_data\\dummy_data.xlsx"
data = xlsx_reader(filename)
print(data)
for i in data[0]:
    print(i)

