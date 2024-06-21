import urllib3
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from datetime import date
import uuid
import os

def set_output(name, value):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f'{name}={value}', file=fh)

def set_multiline_output(name, value):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        delimiter = uuid.uuid1()
        print(f'{name}<<{delimiter}', file=fh)
        print(value, file=fh)
        print(delimiter, file=fh)

def convert_date(date_str):
    current_year = str(date.today().year)
    date_obj = datetime.strptime(date_str, "%d-%b")
    date_obj = date_obj.replace(year=2024)
    return date_obj.date()

def convert_date_time(date_str):
    current_year = str(date.today().year)
    date_obj = datetime.strptime(date_str, "%d-%b %H:%M")
    date_obj = date_obj.replace(year=2024)
    return date_obj

http = urllib3.PoolManager()
url = "https://www.investorgain.com/report/live-ipo-gmp/331/"
response = http.request('GET', url)
soup = BeautifulSoup(response.data, 'html.parser')
table = soup.find('table', id='mainTable')
table_header = table.find('thead')
table_headers = table_header.findAll('a')
headers = []
for cell in table_headers:
    header = cell.text
    header = header.replace("(₹)", "")
    headers.append(header)

table_body = table.find('tbody')
table_rows = table_body.findAll('tr')
data = []

price_list = ['Price', 'GMP(₹)']
date_list = ['Open', 'Close', 'BoA Dt', 'Listing']

for row in table_rows:
    row_data = []
    cells = row.find_all('td')
    if (len(cells) <= 1):
        continue
    for cell in cells:
        if ('data-label' in cell.attrs):
            if (cell.attrs['data-label'] == 'IPO'):
                ipo = cell.find('a').find(string = True)
                row_data.append(ipo.text)
            elif (cell.attrs['data-label'] in price_list):
                if (cell.text != '--'):
                    row_data.append(float(cell.text))
                else:
                    row_data.append(0)
            elif (cell.attrs['data-label'] in date_list):
                row_data.append(convert_date(cell.text))
            elif (cell.attrs['data-label'] == 'GMP Updated'):
                row_data.append(convert_date_time(cell.text))
            elif (cell.attrs['data-label'] == 'Fire Rating'):
                fire_rating_img = cell.find('img')
                fire_rating_text = fire_rating_img.attrs['title'].replace("Rating ", "").replace("/5", "")
                row_data.append(fire_rating_text)
            else:
                row_data.append(cell.text)
    data.append(row_data)
df = pd.DataFrame(data = data, columns = headers)
filtered_df = df[df['GMP'] > 80]
filtered_df = df.loc[(df['GMP'] > 80) & (df['Fire Rating'] == '5') & (df['Close'] > date.today())]
output_string = ""
for index, row in filtered_df.iterrows():
    for column, value in row.items():
        if (isinstance(value, date)):
            date_format = "%B %d, %Y"
            if (column == 'GMP Updated'):
                date_format = "%B %d, %Y - %I:%M%p"
            value = value.strftime(date_format)
        if (isinstance(value, float)):
            value = '₹' + str(value)
        output_string += f"{column}: {value}\n"
    output_string += "\n"
set_multiline_output('IPO', output_string)
print(output_string)
