import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pyvista as pv
from sklearn.gaussian_process import GaussianProcessRegressor
import sklearn.gaussian_process.kernels as kern
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, make_scorer


PARENT_DIR = r'D:\projects\diverters\src'
CURR_DIR = os.path.join(PARENT_DIR, 'analysis_v1')
sys.path.append(PARENT_DIR)


def make_grid(_min_x, _max_x, _min_y, _max_y, _n, x_label='x', y_label='y'):
    _lin_x = np.linspace(_min_x, _max_x, _n)
    _lin_y = np.linspace(_min_y, _max_y, _n)
    _xv, _yv = np.meshgrid(_lin_x, _lin_y)

    return pd.DataFrame({x_label: _xv.ravel(), y_label: _yv.ravel()})


def plot_pyvista(_df, n):
    x = _df.iloc[:, 0].to_numpy()
    y = _df.iloc[:, 1].to_numpy()
    z = _df.iloc[:, 2].to_numpy()

    x *= 1000 / (max(x) - min(x))
    y *= 1000 / (max(y) - min(y))
    z *= 1000 / (max(z) - min(z))

    x = x.reshape((n, n))
    y = y.reshape((n, n))
    z = z.reshape((n, n))

    grid = pv.StructuredGrid(x, y, z)
    grid.plot()


def plot_np(_df, title=None):
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    ax.scatter(_df.iloc[:, 0], _df.iloc[:, 1], _df.iloc[:, 2])

    col_names = _df.columns.tolist()
    ax.set_xlabel(col_names[0])
    ax.set_ylabel(col_names[1])
    ax.set_zlabel(col_names[2], labelpad=-2)

    if title:
        ax.set_title(title)

    plt.subplots_adjust(left=0.0, right=1.20, bottom=0.0, top=1.20)

    plt.show()


df = pd.read_csv(os.path.join(CURR_DIR, 'parametric.frame'), index_col=0)
x = df.iloc[:, 0]
y = df.iloc[:, 1]
z = df.iloc[:, 2]

N = 50
gpr_grid = make_grid(min(x), max(x), min(y), max(y), N, x_label='heat_flux', y_label='mass_flow_rate')
X_train = df.iloc[:, :2]
Y_train = df.iloc[:, 2]

gpr = GaussianProcessRegressor(
    kernel=kern.RBF(length_scale=10),
    n_restarts_optimizer=10
)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

gpr.fit(X_train_scaled, Y_train)
gpr_grid['max_stress'] = gpr.predict(scaler.transform(gpr_grid.iloc[:, 0:2]))
plot_np(gpr_grid)
plt.ion()
plt.show()

rmse_scorer = make_scorer(lambda y_true, y_pred: np.sqrt(mean_squared_error(y_true, y_pred)), greater_is_better=False)
results = cross_val_score(gpr, X_train_scaled, Y_train, cv=5, scoring=rmse_scorer)
print("RMSE Validation:", results)
print("Mean RMSE =", results.mean())