# -*- coding: utf-8 -*-
# @Time    : 2021/4/30 11:25
# @Author  : Ryan

import json
import time

import pandas as pd


class DoubleAverageLines:
    """
    双均线交易策略类

    实现基于两条移动平均线（MA）交叉的技术分析策略，通过识别金叉和死叉信号
    来判断买入和卖出时机。金叉（短周期均线上穿长周期均线）作为买入信号，
    死叉（短周期均线下穿长周期均线）作为卖出信号。
    """

    def __init__(self):
        pass

    # [
    #     1499040000000, // 开盘时间
    # "0.01634790", // 开盘价
    # "0.80000000", // 最高价
    # "0.01575800", // 最低价
    # "0.01577100", // 收盘价(当前K线未结束的即为最新价)
    # "148976.11427815", // 成交量
    # 1499644799999, // 收盘时间
    # "2434.19055334", // 成交额
    # 308, // 成交笔数
    # "1756.87402397", // 主动买入成交量
    # "28.46694368", // 主动买入成交额
    # "17928899.62484339" // 请忽略该参数
    # ]

    def klinesToDataFrame(self, klines):
        """
        将K线数据列表转换为Pandas DataFrame格式

        解析Binance API返回的K线数组，将其转换为结构化的DataFrame，
        包含时间、价格、成交量等字段，便于后续技术分析和指标计算。

        :param klines: K线数据列表，每个元素是一个包含11个字段的数组：
                      [开盘时间, 开盘价, 最高价, 最低价, 收盘价, 成交量,
                       收盘时间, 成交额, 成交笔数, 主动买入量, 主动买入额]
        :return: 转换后的DataFrame，包含以下列：
                 - openTime: 开盘时间（字符串格式）
                 - openPrice: 开盘价
                 - maxPrice: 最高价
                 - minPrice: 最低价
                 - closePrice: 收盘价
                 - closeTime: 收盘时间（字符串格式）
                 - openTime2: 开盘时间副本（用作索引）
                 失败时返回None
        """

        if klines is None:
            print("klinesToDataFrame---error:klines is None.")
            return None

        openTimeList = []
        openPriceList = []
        maxPriceList = []
        minPriceList = []
        closePriceList = []
        dealVoluMeList = []
        closeTimeList = []
        dealTotalMoneyList = []
        dealCountList = []
        dealBuyVolumeList = []
        dealBuyTotalMoneyList = []

        for kline in klines:
            if (type(kline)).__name__ == 'list':
                openTimeList.append(self.stampToTime(kline[0]))
                openPriceList.append(kline[1])
                maxPriceList.append(kline[2])
                minPriceList.append(kline[3])
                closePriceList.append(kline[4])
                dealVoluMeList.append(kline[5])
                closeTimeList.append(self.stampToTime(kline[6]))
                dealTotalMoneyList.append(kline[7])
                dealCountList.append(kline[8])
                dealBuyVolumeList.append(kline[9])
                dealBuyTotalMoneyList.append(kline[10])
            else:
                print("error: kline is not list.")

        kLinesDict = {"openTime": openTimeList, "openPrice": openPriceList, "maxPrice": maxPriceList,
                      "minPrice": minPriceList, "closePrice": closePriceList, "closeTime": closeTimeList,
                      "openTime2": openTimeList}

        klines_df = pd.DataFrame(kLinesDict)

        # for index, row in klines_df.iterrows():
        #     print(str(row["openTime"]) + "\t" + row["openPrice"] + "\t" + row["maxPrice"] + "\t" + row[
        #         "minPrice"] + "\t" + row["closePrice"] + "\t" + str(row["closeTime"]) + "\t")

        return klines_df

    def readJsonFromFile(self, filePath):
        """
        从JSON文件读取K线数据

        读取本地存储的JSON格式K线数据文件，用于离线分析或测试。

        :param filePath: JSON文件的路径
        :return: 解析后的数据列表，如果数据格式不是列表则返回None
        """
        # Opening JSON file
        f = open(filePath, )
        data = json.load(f)
        f.close()
        # Iterating through the json
        # list
        print("readJsonFromFile =")
        if (type(data)).__name__ == 'list':
            for i in data:
                print(i)
            # Closing file
            return data

        return None

    def release_trade_stock(self, ma_x_line, ma_y_line, code, df):
        """
        执行双均线策略，生成交易信号

        计算两条不同周期的移动平均线，识别金叉和死叉信号点，
        并验证信号的时间有效性，返回最终的交易决策。

        策略逻辑：
        - 金叉：短周期MA从下方穿越长周期MA，产生买入信号
        - 死叉：短周期MA从上方穿越长周期MA，产生卖出信号
        - 时间验证：只执行当前K线时间窗口内的有效信号

        :param ma_x_line: 短周期均线的周期长度（例如5日均线）
        :param ma_y_line: 长周期均线的周期长度（例如10日均线），必须大于ma_x_line
        :param code: 交易对代码，例如 'BTCUSDT'
        :param df: 包含K线数据的DataFrame，必须有openTime、closePrice等列
        :return: 交易信号字符串：
                 - "buy,<open_time>"：买入信号，附带开盘时间
                 - "sell,<open_time>"：卖出信号，附带开盘时间
                 - None：无明确交易信号
        """

        print('\n' + code + ' 均线 ' + str(ma_x_line) + ' 和 ' + str(ma_y_line) + ' :')

        df[["openTime"]] = df[["openTime"]].astype(str)  # int类型 转换 成str类型，否则会被当做时间戳使用，造成时间错误
        df[["openTime2"]] = df[["openTime2"]].astype(str)  # int类型 转换 成str类型，否则会被当做时间戳使用，造成时间错误

        # print("===========================================\n")
        df['openTime'] = pd.to_datetime(df['openTime'])
        df['openTime2'] = pd.to_datetime(df['openTime2'])

        df.set_index('openTime2', inplace=True)
        df = df.sort_index(ascending=True)

        # 求出均线
        maX = df['closePrice'].rolling(ma_x_line).mean()
        maY = df['closePrice'].rolling(ma_y_line).mean()

        df = df[ma_y_line:]  # 这个切片很重要，否则会报错，因为数据不匹配
        # 因为 ma_x_line < ma_y_line ,所以均线 切到 ma_y_line
        maX = maX[ma_y_line:]  # 切片，与 df 数据条数保持一致
        maY = maY[ma_y_line:]  # 切片，与 df 数据条数保持一致

        # print("df数据行数=" + str(len(df)))
        # print(df)
        # 从尾部，删除1行
        # df.drop(df.tail(1).index, inplace=True)

        # print("tmp_last_df--数据切片：")
        # for index, row in df.iterrows():
        #     print(str(row["openTime"]) + "\t" + row["openPrice"] + "\t" + row["maxPrice"] + "\t" + row[
        #         "minPrice"] + "\t" + row["closePrice"] + "\t" + str(row["closeTime"]) + "\t")

        print("最后一行数据：")
        last_row = df.iloc[-1, :]  # 第1行，所有列
        print(str(last_row["openTime"]) + "\t" + last_row["openPrice"] + "\t" + last_row["maxPrice"] + "\t" + last_row[
            "minPrice"] + "\t" + last_row["closePrice"] + "\t" + str(last_row["closeTime"]) + "\t")

        print("-------------------------------------------------------\n")
        s1 = maX < maY  # 得到 bool 类型的 Series
        s2 = maX > maY

        death_ex = s1 & s2.shift(1)  # 判定死叉的条件
        death_date = df.loc[death_ex].index  # 死叉对应的日期

        golden_ex = ~(s1 | s2.shift(1))  # 判断金叉的条件
        golden_record = df.loc[golden_ex]
        golden_date = golden_record.index  # 金叉的日期

        s1 = pd.Series(data=1, index=golden_date)  # 1 作为金叉的标识
        s2 = pd.Series(data=0, index=death_date)  # 0 作为死叉的标识

        s = s1.append(s2)  # 合并
        s = s.sort_index(ascending=True)  # 排序

        print("金叉和死叉对应的时间：", s)

        hold = 0  # 持有的股数

        for i in range(0, len(s)):

            if s[i] == 1:
                # 金叉，买入股票的单价
                golden_time = s.index[i]
                trade_buy_price = float(df.loc[golden_time]['closePrice'])  # 收盘价作为买入的价格

                open_time = df.loc[golden_time]['openTime']  # 开盘时间
                close_time = df.loc[golden_time]['closeTime']  # 收盘时间

                isRightTime = self.judgeCurrentTimeWithLastRecordTime(str(open_time), str(close_time))

                str_date = str(golden_time)
                print(str_date + "\t" + "买入" + code + "\t" + str(round(trade_buy_price, 8)) + "---" + str(isRightTime))
                if isRightTime:
                    print("release_trade_stock---buy")
                    return "buy," + str(open_time)

            else:
                # 死叉，卖出股票的单价
                death_time = s.index[i]
                trade_sell_price = float(df.loc[death_time]['closePrice'])  # 收盘价作为卖出的价格

                open_time = df.loc[death_time]['openTime']  # 开盘时间
                close_time = df.loc[death_time]['closeTime']  # 收盘时间

                isRightTime = self.judgeCurrentTimeWithLastRecordTime(str(open_time), str(close_time))

                str_date = str(death_time)
                print(str_date + "\t" + "卖出" + str(code) + "\t" + str(round(trade_sell_price, 8)) + "---" + str(isRightTime))
                if isRightTime:
                    print("release_trade_stock---sell")
                    return "sell," + str(open_time)

        print("release_trade_stock---None")

        return None

    # 判断当前时间，是否在k线时间范围内
    def judgeCurrentTimeWithLastRecordTime(self, openTime, closeTime):
        """
        判断当前时间是否在K线的有效时间窗口内

        通过比较当前系统时间与K线的开盘/收盘时间，验证交易信号是否仍然有效。
        只有当信号对应的K线时间窗口包含当前时刻时，才执行交易。

        :param openTime: K线开盘时间字符串，格式为 'YYYY-MM-DD HH:MM:SS'
        :param closeTime: K线收盘时间字符串，格式为 'YYYY-MM-DD HH:MM:SS'
        :return: True表示当前时间在K线时间范围内，信号有效；False表示已过期
        """

        dateTime_interval = pd.to_datetime(closeTime) - pd.to_datetime(openTime)

        seconds_interval = dateTime_interval.seconds  # int类型，秒数
        # print("seconds_interval 的类型=")
        # print(type(seconds_interval))
        # print(seconds_interval)

        now = int(round((time.time() - seconds_interval) * 1000))

        now02 = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now / 1000))

        if now02 >= openTime and now02 <= closeTime:
            # print("成功---"+openTime+"\t"+now02+"\t"+closeTime)
            return True
        else:
            # print("失败---"+openTime+"\t"+now02+"\t"+closeTime)
            return False

    def stampToTime(self, stamp):
        """
        将毫秒时间戳转换为可读的时间字符串

        将Binance API返回的毫秒级Unix时间戳转换为 'YYYY-MM-DD HH:MM:SS' 格式。

        :param stamp: 毫秒级时间戳（整数或字符串）
        :return: 格式化后的时间字符串，例如 '2021-04-30 15:30:00'
        """

        # now = int(round(time.time() * 1000))
        stamp_int = int(stamp)

        now02 = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stamp_int / 1000))

        return now02
