# example of ARCH model
from random import gauss, seed
from statsmodels.graphics.tsaplots import plot_acf
from arch import arch_model
from matplotlib import pyplot
import numpy as np
import pandas as pd
# seed pseudorandom number generator

seed(1)
# create dataset
data = [gauss(0, i * 0.01) for i in range(0, 100)]
pyplot.plot(data)
pyplot.show()

# square the dataset
squared_data = [x**2 for x in data]
# create acf plot
plot_acf(pd.Series(squared_data))
pyplot.show()

# split into train/test
n_test = 10
train, test = data[:-n_test], data[-n_test:]
# define model
model = arch_model(train, mean="Zero", vol="ARCH", p=15, q=15)
# fit model
model_fit = model.fit()
model_fit.summary()
# forecast the test set
yhat = model_fit.forecast(horizon=n_test)
# plot the actual variance
var = [i * 0.01 for i in range(0, 100)]
pyplot.plot(var[-n_test:])
# plot forecast variance
pyplot.plot(yhat.variance.values[-1, :])
pyplot.show()
