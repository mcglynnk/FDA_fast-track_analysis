# Setup
import pandas as pd
import numpy as np
pd.options.display.max_columns = 30
pd.options.display.width = 200
pd.options.display.max_colwidth = 12

import datetime
import matplotlib.pyplot as plt
import seaborn as sns

##
# Import data
fda_ft = pd.read_csv(r"C:\Users\Kelly\Desktop\RA Capital\fast_track\SCRAPED_DATA_new.csv")
# fda_ft = fda_ft.drop([2])
# fda_ft = fda_ft.drop([32])

# --------------------------------------------------------------------------------------------------------------------
# Analysis of days between fast-track designation and approval
# --------------------------------------------------------------------------------------------------------------------
fda_ft = fda_ft[fda_ft['FDA_approved'] != 'not found']
fda_ft = fda_ft.reset_index(drop=True)

days_to_approval = []
for i, j in list(zip(fda_ft['FDA_approved'], fda_ft['fast_tracked'])):
    # print(i, j)
    d = abs(datetime.datetime.strptime(i, "%m/%d/%Y") - \
                       datetime.datetime.strptime(j, "%m/%d/%Y")).days
    print(d)
    days_to_approval.append(d)

fda_ft.insert(7, "days_to_approval", days_to_approval)

print(fda_ft)

# Outliers
# fda_ft.sort_values('days_to_approval', ascending=False)
stdev = fda_ft['days_to_approval'].std()*3
fda_ft[fda_ft['days_to_approval'] > (fda_ft['days_to_approval'].mean() + stdev)]
fda_ft[fda_ft['days_to_approval'] < (fda_ft['days_to_approval'].mean() - stdev)]

# Drop outliers
fda_ft = fda_ft.drop([18])

# Micro-cap: under $300M
# A small cap is generally a company with a market capitalization of between $300 million and $2 billion.
# Mid-cap: between $2 billion and $10 billion
fda_ft['days_to_approval'].describe() # mean 1097

# Large-cap
len(fda_ft[fda_ft['cap ($B)'] > 2]) # 12 companies
fda_ft[fda_ft['cap ($B)'] > 2]['days_to_approval'].describe() # mean 878 +/-730

# Small-cap
len(fda_ft[fda_ft['cap ($B)'].between(0.3,2)]) # 6 companies
fda_ft[fda_ft['cap ($B)'].between(0.3,2)]['days_to_approval'].describe() # mean 1070 +/-575

# Micro-cap
len(fda_ft[fda_ft['cap ($B)'] < 0.3]) # 4 companies
fda_ft[fda_ft['cap ($B)'].between(0, 0.3)]['days_to_approval'].describe() # mean 1054 +/-505

# --------------------------------------------------------------------------------------------------------------------
# Analysis of stock prices after fast-track designation
# --------------------------------------------------------------------------------------------------------------------
##
# fda_ft = pd.read_csv(r"D:\SCRAPED_DATA.csv")
fda_ft = pd.read_csv(r"C:\Users\Kelly\Desktop\RA Capital\fast_track\SCRAPED_DATA_new.csv")

# Convert market cap to numeric (in $B)
cap = []
for i in fda_ft['market_cap']:
    if isinstance(i, str):
        if "B" in i:
            cap.append(float(i.replace("B", '')))
        elif "M" in i:
            i = float(i.replace("M", ''))/1000
            cap.append(i)
    else:
        cap.append(np.nan)

fda_ft.insert(8, "cap ($B)", cap)

# Take out private companies, no stock data
fda_ft = fda_ft[fda_ft['cap ($B)'].isna() == False]

# Take out any companies missing stock data for all 3 post-fast-track time points (30d, 60d, 90d)
fda_ft = fda_ft.drop(fda_ft[(fda_ft['price_30d'].isna() == True) &
                            (fda_ft['price_60d'].isna() == True) &
                            (fda_ft['price_90d'].isna() == True)].index, axis=0)

# Add normalized stock prices (to closing price on date of fast track designation)
fda_ft['30d_norm'] = fda_ft['price_30d']/fda_ft['closing_price_sdate']
fda_ft['60d_norm'] = fda_ft['price_60d']/fda_ft['closing_price_sdate']
fda_ft['90d_norm'] = fda_ft['price_90d']/fda_ft['closing_price_sdate']

# Plot normalized stock prices for each company
# for idx, i in enumerate(fda_ft.values):
#     fda_ft.iloc[idx,17:20].plot()

# plt.show()

# Make prices numeric, some are strings
for i in ['sp_closing_price_sdate', 'sp_price_30d', 'sp_price_60d', 'sp_price_90d']:
    fda_ft[i] = fda_ft[i].apply(lambda x: x.replace(',','') if isinstance(x, str) else x)
    print(fda_ft[i])
    fda_ft[i] = fda_ft[i].apply(float)


# Normalized stock prices for S&P500
fda_ft['sp_30d_norm'] = fda_ft['sp_price_30d']/fda_ft['sp_closing_price_sdate']
fda_ft['sp_60d_norm'] = fda_ft['sp_price_60d']/fda_ft['sp_closing_price_sdate']
fda_ft['sp_90d_norm'] = fda_ft['sp_price_90d']/fda_ft['sp_closing_price_sdate']

# Percent increase over market
fda_ft['30d_over_m'] = (fda_ft['30d_norm'] - fda_ft['sp_30d_norm']) #- 1
fda_ft['60d_over_m'] = (fda_ft['60d_norm'] - fda_ft['sp_60d_norm']) #- 1
fda_ft['90d_over_m'] = (fda_ft['90d_norm'] - fda_ft['sp_90d_norm']) #- 1


# What percent of companies saw any increase in stock price at 30d after fast track designation?
len(fda_ft[fda_ft['30d_norm'] > 1])/len(fda_ft) # 42.9% (n=15)

# 60d?
len(fda_ft[fda_ft['60d_norm'] > 1])/len(fda_ft) # 42.9% (n=15)

# 90d?
len(fda_ft[fda_ft['90d_norm'] > 1])/len(fda_ft) # 45.7% (n=16)
# By how much?
len(fda_ft[fda_ft['90d_norm'] > 1.1])/len(fda_ft) # 37.1% had a greater than 10% incr in price (n=13)
len(fda_ft[fda_ft['90d_norm'] > 1.2])/len(fda_ft) # 25.7% had a greater than 20% incr in price (n=9)

# What percent lost stock value after fast track designation?
len(fda_ft[fda_ft['30d_norm'] < 1])/len(fda_ft) # 51.4% (n=18)
len(fda_ft[fda_ft['60d_norm'] < 1])/len(fda_ft) # 42.9% (n=15)
len(fda_ft[fda_ft['90d_norm'] < 1])/len(fda_ft) # 42.9% (n=15)

# How much did the stock value rise relative to the total market during the same period?
# -- Different time period for each company! updated collect_pharma_data.py to collect additional data using the S&P500
# or Dow prices.
fda_ft.iloc[5:10,13:]
fda_ft.iloc[5:10,[17,20,23]] # 30d columns
fda_ft.iloc[5:10,[18,21,24]] # 60d columns
fda_ft.iloc[5:10,[19,22,25]] # 90d columns

fda_ft['30d_over_m'].describe() # 0.5%
fda_ft['60d_over_m'].describe() # 2.0%
fda_ft['90d_over_m'].describe() # 4.2%

# What percent did better than 4.2% at 90d?
len(fda_ft[fda_ft['90d_over_m'] > 4.2])/len(fda_ft['90d_over_m']) # 34.3%

# What percent did better than 10% at 90d?
len(fda_ft[fda_ft['90d_over_m'] > 10])/len(fda_ft['90d_over_m']) # 28.5%


# Plot distributions
fig = plt.figure()
#plt.title("Distribution of stock value gains relative to market post-fast track designation")
fig.set_size_inches(5,9)

for column, n in zip(['30d_over_m', '60d_over_m', '90d_over_m'], range(1,4)):
    ax = fig.add_subplot(3,1, n)
    column = '{}'.format(column)
    time_period = column[0:2]

    # Convert to percent
    fda_ft[column] = fda_ft[column].apply(lambda x: x*100)

    # Plot
    sns.distplot(fda_ft[column])

    plt.xlim(-100,100)
    plt.xticks(np.arange(-100,100,step=20))
    # plt.yticks(np.arange(0, max(fda_ft[column]), step=0.01))
    plt.ylabel('Proportion of companies')
    plt.xlabel('Stock gains (% rel. to market) {}d post-fast track designation'.format(time_period))

plt.show()


