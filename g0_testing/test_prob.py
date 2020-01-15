import matplotlib.pyplot as plt
import seaborn as sns

# uniform distribution
from scipy.stats import uniform

n = 10
start = 10
width = 20

data_uniform = uniform.rvs(size=n, loc=start, scale=width)

## creates 10 observations drawn from the uniform distribution
data_uniform


## normal distribution
from scipy.stats import norm

data_normal = norm.rvs(size=10, loc=0, scale=10)

data_normal

player_fppm = player.loc[player["MIN"] > 0, :]["FPPM"]

ax = sns.distplot(player_fppm, kde=True, bins=100, color="skyblue")


##### use http://www.insightsbot.com/fitting-probability-distributions-with-python/
import scipy
import scipy.stats
import matplotlib
import matplotlib.pyplot as plt


class Distribution(object):
    def __init__(self, dist_names_list=[]):
        self.dist_names = ["norm", "lognorm", "expon", "pareto"]
        self.dist_results = []
        self.params = {}

        self.DistributionName = ""
        self.PValue = 0
        self.Param = None

        self.isFitted = False

    def Fit(self, y):
        self.dist_results = []
        self.params = {}
        for dist_name in self.dist_names:
            dist = getattr(scipy.stats, dist_name)
            param = dist.fit(y)

            self.params[dist_name] = param
            # Applying the Kolmogorov-Smirnov test
            D, p = scipy.stats.kstest(y, dist_name, args=param)
            self.dist_results.append((dist_name, p))
        # select the best fitted distribution
        sel_dist, p = max(self.dist_results, key=lambda item: item[1])
        # store the name of the best fit and its p value
        self.DistributionName = sel_dist
        self.PValue = p

        self.isFitted = True
        return self.DistributionName, self.PValue

    def Random(self, n=1):
        if self.isFitted:
            dist_name = self.DistributionName
            param = self.params[dist_name]
            # initiate the scipy distribution
            dist = getattr(scipy.stats, dist_name)
            return dist.rvs(*param[:-2], loc=param[-2], scale=param[-1], size=n)
        else:
            raise ValueError("Must first run the Fit method.")

    def Plot(self, y):
        x = self.Random(n=len(y))
        plt.hist(x, alpha=0.5, label="Fitted")
        plt.hist(y, alpha=0.5, label="Actual")
        plt.legend(loc="upper right")


dst = Distribution()

dst.Fit(player_fppm)

dst.Plot(player_fppm)


import seaborn as sns

ax = sns.distplot(dst.Random(n=1000), kde=True, bins=100, color="skyblue")

# fit discrete distribution?
from scipy.stats import multinomial

p = [0.3, 0.3, 0.4]
k = 1

dist = multinomial(n=k, p=p)

dist.pmf([1, 0, 0])

rng = np.random.default_rng()

rng.multinomial(1, [0.1, 0.1, 0.8], size=10)

rng.multinomial(20, [1 / 6.0] * 6, size=1)
array([[4, 1, 7, 5, 2, 1]])  # random


## mock transformation from list to probabilities

# probable FPPMs
import numpy as np

possible_fppm = np.arange(0, 3.1, 0.1)

from g1_data_gathering.DataFetcher import DataFetcher

