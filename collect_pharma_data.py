# Setup
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import mechanicalsoup
import requests

pd.options.display.max_columns = 20
pd.options.display.width = 200
pd.options.display.max_colwidth = 20

##
fda_ft_2019 = pd.read_excel(r"..\ft_2018_2019_2.xlsx", header=0)

fda_ft_2019

##
# Setup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

import time
import datetime
from collections import OrderedDict

# Make sure stock dates aren't weekends when 30, 60, 90 days are added to the stock price on the day of fast
# track designation
def nearest_weekday(dd):
    ddd = None
    if dd.weekday() == 5:
        ddd = dd - datetime.timedelta(days=1)
    elif dd.weekday() == 6:
        ddd = dd + datetime.timedelta(days=1)
    else:
        ddd = dd
    return ddd

no_stock_data_found = [] # Save the names of companies where data wasn't found, so I can double check

all_data = []

# Loop to collect FDA and financial data for each row in the dataframe
for idx, i in enumerate(fda_ft_2019.values):

    all_data_collec = OrderedDict()

    all_data_collec['ticker'] = fda_ft_2019.iloc[idx]['ticker']
    all_data_collec['applicant'] = fda_ft_2019.iloc[idx]['Applicant']
    all_data_collec['use'] = fda_ft_2019.iloc[idx]['Use']
    all_data_collec['drug'] = fda_ft_2019.iloc[idx]['Proprietary Name'] # Use commercial name, not chemical/drug name
    all_data_collec['fast_tracked'] = datetime.datetime.strftime(fda_ft_2019.iloc[idx]['Fast track date'], "%m/%d/%Y")

    # Set up driver and web options
    chrome_options = webdriver.ChromeOptions()
    #user_agent = 'Mozilla/5.0 Chrome/60.0.3112.50'
    #chrome_options.add_argument('user-agent={0}'.format(user_agent))
    chrome_options.add_argument('--headless')  # suppress opening a browser
    driver = webdriver.Chrome(r"..\chromedriver_83.exe",
                              options=chrome_options
                              )
    print("Collecting data on {}...".format(fda_ft_2019.iloc[idx]['Applicant']))

    # Approval date
    url = 'https://www.accessdata.fda.gov/scripts/cder/daf/'
    driver.get(url)

    searchfield = driver.find_element_by_xpath('//*[@id="searchterm"]')
    searchfield.send_keys(fda_ft_2019.iloc[idx]['Established Name'])

    try:
        submitb = driver.find_element_by_xpath('//*[@id="DrugNameform"]/div[2]/button[1]')
        submitb.click()
        print("Searching for FDA approval date...")
        time.sleep(5)

        field = driver.find_element_by_xpath('//*[@id="accordion"]/div[5]/div[1]/h4/a')
        field.click()
        time.sleep(5)
        appr_date = driver.find_element_by_xpath('//*[@id="exampleApplOrig"]/tbody/tr/td[1]')

        all_data_collec['FDA_approved'] = appr_date.text
        print("FDA approval date found.")

    except NoSuchElementException as ind:
        print("FDA approval date not found.")
        all_data_collec['FDA_approved'] = 'not found'

    if fda_ft_2019.iloc[idx]['ticker'] != 'priv':
        # Stock prices
        print("Searching for stock prices for the first three months after fast track designation...")
        url1 = 'https://finance.yahoo.com/quote/{}?p={}&.tsrc=fin-srch'.format(fda_ft_2019.iloc[idx]['ticker'],
                                                                              fda_ft_2019.iloc[idx]['ticker'])

        driver.get(url1)

        # Market cap
        try:
            cap = driver.find_element_by_xpath('//*[@id="quote-summary"]/div[2]/table/tbody/tr[1]/td[2]/span')
            all_data_collec['market_cap'] = cap.text
        except NoSuchElementException as n:
            all_data_collec['market_cap'] = "NA"

        sdate = datetime.datetime.strftime(fda_ft_2019.iloc[idx]['Fast track date'], "%m/%d/%Y")

        edate = datetime.datetime.strptime(sdate, "%m/%d/%Y") + datetime.timedelta(days=100)
        edate = datetime.datetime.strftime(edate, "%m/%d/%Y")

        hist_tab = driver.find_element_by_xpath('//*[@id="quote-nav"]/ul/li[6]/a')
        hist_tab.click()
        print("Going to history tab...")
        time.sleep(10)

        try:
            # Print results
            print('〰'*int(np.floor((24-len(fda_ft_2019.iloc[idx]['Applicant'].replace('\n', ' '))/2))),
                  fda_ft_2019.iloc[idx]['Applicant'].replace('\n', ' '),
                  '〰' *int(np.floor(((24-len(fda_ft_2019.iloc[idx]['Applicant'].replace('\n', ' '))/2))))
                  )
            print('-' *6, 'at_ft', '-' * 12, '30d', '-' * 12, '60d', '-' * 12, '90d', '-' * 6)

            dropdown = driver.find_element_by_xpath(
                '//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[1]/div[1]/div[1]/div/div/div/span')
            dropdown.click()

            startdate_box = driver.find_element_by_xpath('//*[@id="dropdown-menu"]/div/div[1]/input')
            startdate_box.send_keys(sdate)
            enddate_box = driver.find_element_by_xpath('//*[@id="dropdown-menu"]/div/div[2]/input')
            enddate_box.send_keys(edate)
            submit_button = driver.find_element_by_xpath('//*[@id="dropdown-menu"]/div/div[3]/button[1]')
            submit_button.click()
            #print("Submitting dates...")

            appl = driver.find_element_by_xpath(
                '//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[1]/div[1]/button/span')
            appl.click()
            time.sleep(10)

            table_ = driver.find_elements_by_css_selector(
                '#Col1-1-HistoricalDataTable-Proxy > section > div.Pb\(10px\).Ovx\('
                'a\).W\(100\%\) > table > tbody')

            all = []
            for row in table_:
                x = row.text.split('\n')
                for i in x:
                    # print(i)
                    col = OrderedDict()
                    items_ = i.split(' ')
                    d = ' '.join(items_[0:3])
                    d = datetime.datetime.strptime(d, "%b %d, %Y").strftime("%m/%d/%Y")
                    col['date'] = d
                    try:
                        col['closing_price'] = items_[6]
                    except IndexError as ind:
                        continue

                    all.append(col)

            all = pd.DataFrame(all)

            approval_date = sdate
            approval_date_dt = datetime.datetime.strptime(approval_date, "%m/%d/%Y")

            try:
                all_data_collec['closing_price_sdate'] = \
                all[all['date'] == datetime.datetime.strftime(nearest_weekday(approval_date_dt), "%m/%d/%Y")][
                    'closing_price'].values[0]
                print(' '*6, "found")
            except IndexError as ind:
                all_data_collec['price_30d'] = "NA"
                print(' '*6, "not found")

            try:
                all_data_collec['price_30d'] = all[all['date'] == datetime.datetime.strftime(
                    nearest_weekday(approval_date_dt +  datetime.timedelta(days=28)), "%m/%d/%Y")][
                    'closing_price'].values[0]
                print(' '*24, "found")
            except IndexError as ind:
                all_data_collec['price_30d'] = "NA"
                print(' '*24, "not found")

            try:
                all_data_collec['price_60d'] = all[all['date'] == datetime.datetime.strftime(
                    nearest_weekday(approval_date_dt + datetime.timedelta(days=60)), "%m/%d/%Y")][
                    'closing_price'].values[0]
                print(' '*42, "found")
            except IndexError as ind:
                all_data_collec['price_60d'] = "NA"
                print(' '*42, "not found")

            try:
                all_data_collec['price_90d'] = all[all['date'] == datetime.datetime.strftime(
                     nearest_weekday(approval_date_dt + datetime.timedelta(days=90)), "%m/%d/%Y")][
                    'closing_price'].values[0]
                print(' '*58, "found")
            except IndexError as ind:
                all_data_collec['price_90d'] = "NA"
                print(' '*58, "not found")

            print('\n')

        except NoSuchElementException as ex:
            no_stock_data_found.append(fda_ft_2019.iloc[idx]['ticker'])
            print(' '*12, 'No stock data found', ' '*12)
            print('\n')

        driver.close()

        # Get S&P500 data for the same dates
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')  # suppress opening a browser
        driver = webdriver.Chrome(r"..\chromedriver_81.exe",
                                  options=chrome_options
                                  )

        url2 = 'https://finance.yahoo.com/quote/%5EGSPC/history?p=%5EGSPC'
        driver.get(url2)
        time.sleep(8)

        dropdown = driver.find_element_by_xpath(
            '//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[1]/div[1]/div[1]/div/div/div/span')
        dropdown.click()

        startdate_box = driver.find_element_by_xpath('//*[@id="dropdown-menu"]/div/div[1]/input')
        startdate_box.clear()
        startdate_box.send_keys(sdate)
        enddate_box = driver.find_element_by_xpath('//*[@id="dropdown-menu"]/div/div[2]/input')
        enddate_box.clear()
        enddate_box.send_keys(edate)
        submit_button = driver.find_element_by_xpath('//*[@id="dropdown-menu"]/div/div[3]/button[1]')
        submit_button.click()

        appl = driver.find_element_by_xpath(
            '//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[1]/div[1]/button/span')
        appl.click()
        time.sleep(10)

        table_ = driver.find_elements_by_css_selector(
            '#Col1-1-HistoricalDataTable-Proxy > section > div.Pb\(10px\).Ovx\('
            'a\).W\(100\%\) > table > tbody')

        all = []
        for row in table_:
            x = row.text.split('\n')
            for i in x:
                col = OrderedDict()
                items_ = i.split(' ')
                d = ' '.join(items_[0:3])
                d = datetime.datetime.strptime(d, "%b %d, %Y").strftime("%m/%d/%Y")
                col['date'] = d
                try:
                    col['closing_price'] = items_[6]
                except IndexError as ind:
                    continue

                all.append(col)

        all = pd.DataFrame(all)

        approval_date = sdate
        approval_date_dt = datetime.datetime.strptime(approval_date, "%m/%d/%Y")

        # S&P 500 closing prices on the same dates
        all_data_collec['sp_closing_price_sdate'] = \
            all[all['date'] == datetime.datetime.strftime(nearest_weekday(approval_date_dt), "%m/%d/%Y")][
            'closing_price'].values[0]

        all_data_collec['sp_price_30d'] = all[all['date'] == datetime.datetime.strftime(
            nearest_weekday(approval_date_dt + datetime.timedelta(days=28)), "%m/%d/%Y")]['closing_price'].values[0]

        all_data_collec['sp_price_60d'] = all[all['date'] == datetime.datetime.strftime(
            nearest_weekday(approval_date_dt + datetime.timedelta(days=60)), "%m/%d/%Y")]['closing_price'].values[0]

        all_data_collec['sp_price_90d'] = all[all['date'] == datetime.datetime.strftime(
            nearest_weekday(approval_date_dt + datetime.timedelta(days=90)), "%m/%d/%Y")]['closing_price'].values[0]

        all_data.append(all_data_collec)

        driver.close()

    else:
        all_data_collec['market_cap'] = "NA"
        all_data_collec['closing_price_sdate'] = "NA"
        all_data_collec['price_30d'] = "NA"
        all_data_collec['price_60d'] = "NA"
        all_data_collec['price_90d'] = "NA"

        all_data.append(all_data_collec)

    # Save progress while code is running
    if idx % 3 == 0:
        pd.DataFrame(all_data).to_csv(r"..\SCRAPED_DATA.csv")

    info_df = pd.DataFrame(all_data)
    print(info_df)
    print('\n')

info_df = pd.DataFrame(all_data)
print(info_df)


# Save final results
info_df.to_csv(r"..\SCRAPED_DATA.csv")


