import pandas as pd
import numpy as np
import yfinance as yf

df = yf.download("2330.TW", start = "2018-01-01", end = "2020-12-31")
# 轉換線價格(一短線週期)
df['9_max'] = (df['High'].rolling(window=9).max())
df['9_min'] = (df['Low'].rolling(window=9).max())
df['CL'] = round((df['9_max'] + df['9_min']) / 2, 4)

# 基準線價格(一中線週期)
df['26_max'] = (df['High'].rolling(window=26).max())
df['26_min'] = (df['Low'].rolling(window=26).max())
df['SL'] = round((df['26_max'] + df['26_min']) / 2, 4)

# 雲帶先行線A價格(LLA)(CL+SL)/2
df['(CL+SL)/2'] = round((df['CL'] + df['SL']) / 2, 4)
# 雲帶先行線B價格(LLB)
df['52_max'] = (df['High'].rolling(window=52).max())
df['52_min'] = (df['Low'].rolling(window=52).max())
df['52_max_min'] = round((df['52_max'] + df['52_min']) / 2, 4)

df['LLA'] = np.nan
df['LLB'] = np.nan
df['LS'] = np.nan # 延遲帶
# 將第52天的價格當作第一筆，+ 26是配合雲帶平移
df['CL'][43:] = df['CL'][:-43] # s
df['SL'][26:] = df['CL'][:-26] # m
df['LLA'][52:] = df['(CL+SL)/2'][:-52] #ca
df['LLB'][26:] = df['52_max_min'][:-26] # cb
df['LS'][78:] = df['Close'][:-78]

df = df[78:]
# print(df)

# import matplotlib.pyplot as plt
# rows = (df.index)
# columns = ['CL', 'SL', 'LLA', 'LLB', 'LS']
# result = df.loc[rows, columns]
# result.set_index(df.index.get_level_values('Date'), inplace=True)
# chart = result.plot(title = 'test',
#                     xlabel='date',
#                     ylabel='price',
#                     legend=True,
#                     figsize=(10,5))
# plt.fill_between( df.index.get_level_values('Date'), df['LLB'], df['LLA'], where = None, color='grey', alpha=0.3, label = 'Value')

# plt.show()



bull_times = 0 # 多頭交易次數
bear_times = 0 # 空頭交易次數
sl_ar = [] # 停損點的不同持倉日的最佳AR
tp_ar = [] # 停利點的不同持倉日的最佳AR
at_least_holding = [] # 最低持倉日
ave_ar_at_least_holding = [] # 最低持倉日1-60的平均AR
ar_other = [] # [最低持倉日, 停損點, 停利點]
ar_re = [] # 回測AR

for k in range(0, 60):
    n = k + 1 # 最低持倉日
    print(n)
    for x in range(5, 21): # 停損SL(sl_min)
        for y in range(5, 21): # 停利TP(tp_max)
            del at_least_holding[:]
            for i in range(0, len(df['LLB']) // 2):
                f = i + 2 # 進場日期index
                # 多頭
                if(df['CL'][i] < df['SL'][i] and df['CL'][i + 1] > df['SL'][i + 1]):
                    if(df['Close'][i + 1] > df['SL'][i + 1] and df['Close'][i + 1] > max(df['LLA'][i + 1], df['LLB'][i + 1])):
                        
                        # print(df[f])
                        for j in range(i + 1, len(df['LLB']) // 2 - n): # j = i + 1 = t
                            if((df['CL'][j + n] - df['Open'][f]) / df['Open'][f] >= (y / 100)): # 停利
                                return_rate = (df['Open'][j + n + 1] - df['Open'][f]) / df['Open'][f] # HPR
                                ar = return_rate * 250 / (j + n + 1 - f) # j + n + 1: 賣出日期index
                                at_least_holding.append(ar)
                                break
                            elif(df['SL'][j + n] < df['SL'][j + n] and j - f >= n): # 正常退場
                                return_rate = (df['Open'][j + n + 1] - df['Open'][f]) / df['Open'][f] # HPR
                                ar = return_rate * 250 / (j + n + 1 - f) # j + n + 1: 賣出日期index
                                at_least_holding.append(ar)
                                break
                            elif((df['Close'][j + n] - df['Open'][f]) / df['Open'][f] <= -(x / 100)): # 停損
                                return_rate = (df['Open'][j + n + 1] - df['Open'][f]) / df['Open'][f] # HPR
                                ar = return_rate * 250 / (j + n + 1 - f) # j + n + 1: 賣出日期index
                                at_least_holding.append(ar)
                                break
                #空頭
                elif(df['CL'][i] >= df['SL'][i] and df['CL'][i + 1] < df['SL'][i + 1]):
                    if(df['Close'][i + 1] < df['SL'][i + 1] and df['Close'][i + 1] < min(df['LLA'][i + 1], df['LLB'][i + 1])):
                        for j in range(i+1, len(df['LLB']) // 2 - n): #j=i+1=t
                            if((df['Close'][j + n] - df['Open'][f]) / df['Open'][f] <= -(y / 100)): #停利
                                returnrate = (df['Open'][j + n + 1] - df['Open'][f]) / df['Open'][f]#HPR
                                ar = returnrate * 250 / (j + n + 1 - f)
                                at_least_holding.append(ar) #AR
                                break
                            elif((df['CL'][j + n] > df['SL'][j + n]) and ((j - f)>= n)):#正常退場
                                returnrate = (df['Open'][j + n + 1] - df['Open'][f]) / df['Open'][f]#HPR
                                ar = returnrate * 250 / (j + n + 1 - f)
                                at_least_holding.append(ar) #AR
                                break
                            elif(((df['Close'][j + n] - df['Open'][f]) / df['Open'][f]) >= (x / 100)): #停損
                                returnrate = (df['Open'][j + n + 1] - df['Open'][f]) / df['Open'][f]#HPR
                                ar = returnrate * 250 / (j + n + 1 - f)
                                at_least_holding.append(ar) #AR
                                break
            tot = 0
            if(len(at_least_holding) > 0):
                for z in range(len(at_least_holding)):
                    tot += at_least_holding[z]
                ave = tot / len(at_least_holding) #不同停利、停損、Nmin下的AR平均
                ave_ar_at_least_holding.append(ave) #平均AR
                ar_other.append([n, (x/100), (y/100)]) #最低持倉日, 停損點sl_min, 停利點sl_max
            
            # print(tot)

best_ar = max(ave_ar_at_least_holding)
index = ave_ar_at_least_holding.index(best_ar)
min_holding = ar_other[index][0]
sl_min = ar_other[index][1]
tp_max = ar_other[index][2]

print('最佳AR:%f'%best_ar)
print('最低持倉日:%d天'%min_holding)
print('停損點SL_min:%.2f'%sl_min)
print('停利點SL_max:%.2f'%tp_max)