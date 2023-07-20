import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.gaussian_process import GaussianProcessRegressor
import sklearn.gaussian_process.kernels as kern
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, make_scorer


def make_grid(_min_x, _max_x, _min_y, _max_y, _n, x_label='x', y_label='y'):
    _lin_x = np.linspace(_min_x, _max_x, _n)
    _lin_y = np.linspace(_min_y, _max_y, _n)
    _xv, _yv = np.meshgrid(_lin_x, _lin_y)

    return pd.DataFrame({x_label: _xv.ravel(), y_label: _yv.ravel()})


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


def make_gpr(_x_train, _y_train):
    inp_kernel = kern.RBF(length_scale=10 * np.ones(_x_train.shape[1]))
    _gpr = GaussianProcessRegressor(
        kernel=inp_kernel,
        n_restarts_optimizer=100
    )
    _scaler = StandardScaler()
    _x_train_scaled = _scaler.fit_transform(_x_train.values, y=_y_train.values)
    _gpr.fit(_x_train_scaled, _y_train)

    return _gpr, _scaler


def plot_gpr(_x_train, _gpr, _scaler, y_label='result'):
    _grid = make_grid(
        _x_train.iloc[:, 0].min(),
        _x_train.iloc[:, 0].max(),
        _x_train.iloc[:, 1].min(),
        _x_train.iloc[:, 1].max(),
        50,
        x_label=_x_train.columns[0],
        y_label=_x_train.columns[1]
    )
    _grid[y_label] = _gpr.predict(_scaler.transform(_grid.values))
    plot_np(_grid)


def score_gpr(_x_train, _y_train, _gpr, _scaler):
    _x_train_scaled = _scaler.fit_transform(_x_train.values)

    rmse_scorer = make_scorer(lambda y_true, y_pred: np.sqrt(mean_squared_error(y_true, y_pred)), greater_is_better=False)
    results = cross_val_score(_gpr, _x_train_scaled, _y_train, cv=3, scoring=rmse_scorer)
    print("RMSE Validation:", results)
    print("Mean RMSE =", results.mean())


def perform_gpr_analysis(_x_train, _y_train, y_label='result'):
    _gpr, _scaler = make_gpr(_x_train, _y_train)

    plot_gpr(_x_train, _gpr, _scaler, y_label=y_label)
    score_gpr(_x_train, _y_train, _gpr, _scaler)

    return _gpr, _scaler
