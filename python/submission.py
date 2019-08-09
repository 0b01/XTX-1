import math, pickle, subprocess, time
import numpy as np
from core import Submission

"""
PYTHON submission

Implement the model below

##################################################### OVERVIEW ######################################################

1. Use get_next_data_as_string() OR get_next_data_as_list() OR get_next_data_as_numpy_array() to recieve the next row of data
2. Use the predict method to write the prediction logic, and return a float representing your prediction
3. Submit a prediction using self.submit_prediction(...)

################################################# OVERVIEW OF DATA ##################################################

1. get_next_data_as_string() accepts no input and returns a String representing a row of data extracted from data.csv
     Example output: '1619.5,1620.0,1621.0,,,,,,,,,,,,,1.0,10.0,24.0,,,,,,,,,,,,,1615.0,1614.0,1613.0,1612.0,1611.0,
     1610.0,1607.0,1606.0,1605.0,1604.0,1603.0,1602.0,1601.5,1601.0,1600.0,7.0,10.0,1.0,10.0,20.0,3.0,20.0,27.0,11.0,
     14.0,35.0,10.0,1.0,10.0,13.0'

2. get_next_data_as_list() accepts no input and returns a List representing a row of data extracted from data.csv,
   missing data is represented as NaN (math.nan)
     Example output: [1619.5, 1620.0, 1621.0, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, 1.0, 10.0,
     24.0, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, 1615.0, 1614.0, 1613.0, 1612.0, 1611.0, 1610.0,
     1607.0, 1606.0, 1605.0, 1604.0, 1603.0, 1602.0, 1601.5, 1601.0, 1600.0, 7.0, 10.0, 1.0, 10.0, 20.0, 3.0, 20.0,
     27.0, 11.0, 14.0, 35.0, 10.0, 1.0, 10.0, 13.0]

3. get_next_data_as_numpy_array() accepts no input and returns a Numpy Array representing a row of data extracted from
   data.csv, missing data is represented as NaN (math.nan)
   Example output: [1.6195e+03 1.6200e+03 1.6210e+03 nan nan nan nan nan nan nan nan nan nan nan nan 1.0000e+00
    1.0000e+01 2.4000e+01 nan nan nan nan nan nan nan nan nan nan nan nan 1.6150e+03 1.6140e+03 1.6130e+03 1.6120e+03
     1.6110e+03 1.6100e+03 1.6070e+03 1.6060e+03 1.6050e+03 1.6040e+03 1.6030e+03 1.6020e+03 1.6015e+03 1.6010e+03
      1.6000e+03 7.0000e+00 1.0000e+01 1.0000e+00 1.0000e+01 2.0000e+01 3.0000e+00 2.0000e+01 2.7000e+01 1.1000e+01
       1.4000e+01 3.5000e+01 1.0000e+01 1.0000e+00 1.0000e+01 1.3000e+01]

##################################################### IMPORTANT ######################################################

1. One of the methods get_next_data_as_string(), get_next_data_as_list(), or get_next_data_as_numpy_array() MUST be used and
   _prediction(pred) MUST be used to submit below in the solution implementation for the submission to work correctly.
2. get_next_data_as_string(), get_next_data_as_list(), or get_next_data_as_numpy_array() CANNOT be called more then once in a
   row without calling self.submit_prediction(pred).
3. In order to debug by printing do NOT call the default method `print(...)`, rather call self.debug_print(...)

"""


# class MySubmission is the class that you will need to implement
class MySubmission(Submission):

    def __init__(self):
        self.turn = 0
        self.ARRAY_SIZE = 5000000

        self.alpha_10 = 2. / (10. + 1.)
        self.alpha_12 = 2. / (12. + 1.)
        self.alpha_20 = 2. / (20. + 1.)
        self.alpha_50 = 2. / (50. + 1.)
        self.alpha_500 = 2. / (500. + 1.)
        self.alpha_1500 = 2. / (1500. + 1.)

        self.bias_10 = (2. - self.alpha_10) / 2. / (1. - self.alpha_10)
        self.bias_12 = (2. - self.alpha_12) / 2. / (1. - self.alpha_12)
        self.bias_20 = (2. - self.alpha_20) / 2. / (1. - self.alpha_20)
        self.bias_50 = (2. - self.alpha_50) / 2. / (1. - self.alpha_50)
        self.bias_500 = (2. - self.alpha_500) / 2. / (1. - self.alpha_500)
        self.bias_1500 = (2. - self.alpha_1500) / 2. / (1. - self.alpha_1500)

        # Huber, no weight, full period
        self.coeffs = np.array([0.0590159165491374, 0.07022091653929377, 0.03198589179700843, -0.0006409888123531155, 0.017952193358737923, 0.2408922108355985])

        self.mids = np.zeros(self.ARRAY_SIZE)
        self.y = np.zeros(self.ARRAY_SIZE)
        self.y_pred = np.zeros(self.ARRAY_SIZE)
        self.signals = np.zeros((self.ARRAY_SIZE, len(self.coeffs)))

        super().__init__()

    """
    update_data(data) appends new row to existing dataframe
    """
    def update_data(self):

        data = self.get_next_data_as_string()
        data = [float(x) if x else 0 for x in data.split(',')]
        self.x = data

        if self.turn == self.ARRAY_SIZE - 10:
            self.mids.resize(2 * len(self.mids))
            self.y.resize(2 * len(self.y))
            self.y_pred.resize(2 * len(self.y_pred))
            self.signals.resize(2 * len(self.signals))
            self.ARRAY_SIZE = 2 * self.ARRAY_SIZE

    """
    update_features(self) update features after each new line is added
    """
    def update_features(self):

        x = self.x
        turn = self.turn
        turn_prev = max(turn - 87, 0)

        askRate0 = x[0] if x[0] != 0 else np.nan
        askRate1 = x[1] if x[1] != 0 else np.nan
        bidRate0 = x[30] if x[30] != 0 else np.nan
        bidRate1 = x[31] if x[31] != 0 else np.nan

        askSize0 = x[15]
        askSize1 = x[16]
        askSize2 = x[17]
        bidSize0 = x[45]
        bidSize1 = x[46]
        bidSize2 = x[47]

        askSize012 = askSize0 + askSize1 + askSize2
        bidSize012 = bidSize0 + bidSize1 + bidSize2
        askSizeTotal = np.sum(x[15:30])
        bidSizeTotal = np.sum(x[45:60])

        mid = 0.5 * (bidRate0 + askRate0)
        mid_mic = (askSize0 * bidRate0 + bidSize0 * askRate0) / (askSize0 + bidSize0)
        y = mid - self.mids[turn_prev]
        self.mids[turn] = mid
        self.y[turn_prev] = y

        if self.turn == 0:
            self.y_ewma500 = y
            self.y_var_ewma500 = 0.18
            self.y_vol_ewma500 = math.sqrt(self.y_var_ewma500)

            self.bidSize0_var_ewma50 = 2.
            self.askSize0_var_ewma50 = 5.
            self.bidSize0_vol_ewma50 = math.sqrt(self.bidSize0_var_ewma50)
            self.askSize0_vol_ewma50 = math.sqrt(self.askSize0_var_ewma50)

            self.bidSize0_ewma50 = bidSize0
            self.askSize0_ewma50 = askSize0
            self.bidSize1_ewma50 = bidSize1
            self.askSize1_ewma50 = askSize1

            self.askSize012_ewma50 = askSize012
            self.bidSize012_ewma50 = bidSize012
            self.askSizeTotal_ewma20 = askSizeTotal
            self.bidSizeTotal_ewma20 = bidSizeTotal

            self.askSize012_var_ewma50 = 17.8295
            self.bidSize012_var_ewma50 = 25.4785
            self.askSize012_vol_ewma50 = math.sqrt(self.askSize012_var_ewma50)
            self.bidSize012_vol_ewma50 = math.sqrt(self.bidSize012_var_ewma50)
            self.askSizeTotal_var_ewma20 = 0.5155
            self.bidSizeTotal_var_ewma20 = 4.6359
            self.askSizeTotal_vol_ewma20 = math.sqrt(self.askSizeTotal_var_ewma20)
            self.bidSizeTotal_vol_ewma20 = math.sqrt(self.bidSizeTotal_var_ewma20)

            self.midMic_ewma10 = mid_mic
            self.midMic_var_ewma10 = 0.2568
            self.midMic_vol_ewma10 = math.sqrt(self.midMic_var_ewma10)

        else:
            # y
            self.y_var_ewma500 = (1. - self.alpha_500) * (self.y_var_ewma500 + self.bias_500 * self.alpha_500 * (y - self.y_ewma500) * (y - self.y_ewma500))
            self.y_vol_ewma500 = math.sqrt(self.y_var_ewma500)

            self.y_ewma500 = (1. - self.alpha_500) * self.y_ewma500 + self.alpha_500 * y

            # bidSize0 and askSize0 ewma
            self.bidSize0_var_ewma50 = (1. - self.alpha_50) * (self.bidSize0_var_ewma50 + self.bias_50 * self.alpha_50 * (bidSize0 - self.bidSize0_ewma50) * (bidSize0 - self.bidSize0_ewma50))
            self.askSize0_var_ewma50 = (1. - self.alpha_50) * (self.askSize0_var_ewma50 + self.bias_50 * self.alpha_50 * (askSize0 - self.askSize0_ewma50) * (askSize0 - self.askSize0_ewma50))
            self.bidSize0_vol_ewma50 = math.sqrt(self.bidSize0_var_ewma50)
            self.askSize0_vol_ewma50 = math.sqrt(self.askSize0_var_ewma50)

            self.bidSize0_ewma50 = (1. - self.alpha_50) * self.bidSize0_ewma50 + self.alpha_50 * bidSize0
            self.askSize0_ewma50 = (1. - self.alpha_50) * self.askSize0_ewma50 + self.alpha_50 * askSize0

            # bidSize1 and askSize1 ewma
            self.bidSize1_ewma50 = (1. - self.alpha_50) * self.bidSize1_ewma50 + self.alpha_50 * bidSize1
            self.askSize1_ewma50 = (1. - self.alpha_50) * self.askSize1_ewma50 + self.alpha_50 * askSize1

            # bidSizeTotal and askSizeTotal ewma
            self.askSize012_var_ewma50 = (1. - self.alpha_50) * (self.askSize012_var_ewma50 + self.bias_50 * self.alpha_50 * (askSize012 - self.askSize012_ewma50) * (askSize012 - self.askSize012_ewma50))
            self.bidSize012_var_ewma50 = (1. - self.alpha_50) * (self.bidSize012_var_ewma50 + self.bias_50 * self.alpha_50 * (bidSize012 - self.bidSize012_ewma50) * (bidSize012 - self.bidSize012_ewma50))
            self.askSize012_vol_ewma50 = math.sqrt(self.askSize012_var_ewma50)
            self.bidSize012_vol_ewma50 = math.sqrt(self.bidSize012_var_ewma50)
            self.askSizeTotal_var_ewma20 = (1. - self.alpha_20) * (self.askSizeTotal_var_ewma20 + self.bias_20 * self.alpha_20 * (askSizeTotal - self.askSizeTotal_ewma20) * (askSizeTotal - self.askSizeTotal_ewma20))
            self.bidSizeTotal_var_ewma20 = (1. - self.alpha_20) * (self.bidSizeTotal_var_ewma20 + self.bias_20 * self.alpha_20 * (bidSizeTotal - self.bidSizeTotal_ewma20) * (bidSizeTotal - self.bidSizeTotal_ewma20))
            self.askSizeTotal_vol_ewma20 = math.sqrt(self.askSizeTotal_var_ewma20)
            self.bidSizeTotal_vol_ewma20 = math.sqrt(self.bidSizeTotal_var_ewma20)

            self.askSize012_ewma50 = (1. - self.alpha_50) * self.askSize012_ewma50 + self.alpha_50 * askSize012
            self.bidSize012_ewma50 = (1. - self.alpha_50) * self.bidSize012_ewma50 + self.alpha_50 * bidSize012
            self.askSizeTotal_ewma20 = (1. - self.alpha_20) * self.askSizeTotal_ewma20 + self.alpha_20 * askSizeTotal
            self.bidSizeTotal_ewma20 = (1. - self.alpha_20) * self.bidSizeTotal_ewma20 + self.alpha_20 * bidSizeTotal


            # Micro mid zscore
            self.midMic_var_ewma10 = (1. - self.alpha_10) * (self.midMic_var_ewma10 + self.bias_10 * self.alpha_10 * (mid_mic - self.midMic_ewma10) * (mid_mic - self.midMic_ewma10))
            self.midMic_vol_ewma10 = math.sqrt(self.midMic_var_ewma10)

            self.midMic_ewma10 = (1. - self.alpha_10) * self.midMic_ewma10 + self.alpha_10 * mid_mic

        #### Signals ####
        self.sig1 = (bidSize0 - askSize0) / (bidSize0 + askSize0)
        self.sig2 = (bidSize1 - askSize1) / (bidSize1 + askSize1)
        self.sig3 = (bidSize012 - self.bidSize012_ewma50) / self.bidSize012_vol_ewma50 - (askSize012 - self.askSize012_ewma50) / self.askSize012_vol_ewma50
        self.sig4 = bidSize1 / bidSize0 - askSize1 / askSize0
        self.sig5 = (bidSize0 - self.bidSize0_ewma50) / self.bidSize0_vol_ewma50 - (askSize0 - self.askSize0_ewma50) / self.askSize0_vol_ewma50
        self.sig6 = (bidSizeTotal - self.bidSizeTotal_ewma20) / self.bidSizeTotal_vol_ewma20 - (askSizeTotal - self.askSizeTotal_ewma20) / self.askSizeTotal_vol_ewma20
        self.sig7 = (askRate1 - askRate0 - 0.5) - (bidRate0 - bidRate1 - 0.5)
        self.sig8 = (mid_mic - self.midMic_ewma10) / self.midMic_vol_ewma10

        signals = np.array([self.sig1, self.sig2, self.sig3, self.sig4, self.sig5, self.sig7])
        signals[np.isinf(signals)] = 0.
        signals[np.isnan(signals)] = 0.
        self.signals[turn, :] = signals	

        return

    """
    get_prediction(data) expects a row of data from data.csv as input and should return a float that represents a
       prediction for the supplied row of data
    """
    def get_prediction(self):
        prediction = np.dot(self.signals[self.turn], self.coeffs)

        if not np.isfinite(prediction):
            prediction = 0.

        prediction = np.clip(prediction, -5., 5.)
        self.y_pred[self.turn] = prediction
        return prediction


    """
    run_submission() will iteratively fetch the next row of data in the format 
       specified (get_next_data_as_string, get_next_data_as_list, get_next_data_as_numpy_array)
       for every prediction submitted to self.submit_prediction()
    """
    def run_submission(self):

        while(True):
            #start = time.time()
            self.update_data()
            self.update_features()
            prediction = self.get_prediction()

            #prediction = (time.time() - start) * 1000
            self.submit_prediction(prediction)

            self.turn += 1


if __name__ == "__main__":
    MySubmission()
