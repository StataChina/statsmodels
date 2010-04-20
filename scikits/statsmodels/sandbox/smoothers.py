"""
This module contains scatterplot smoothers, that is classes
who generate a smooth fit of a set of (x,y) pairs.
"""

import numpy as np
import numpy.linalg as L
import kernel
from scipy.linalg import solveh_banded
from scipy.optimize import golden

#from models import _hbspline        # Need to alter setup to be able to import
                                    # extension from models or drop for scipy
#from models.bspline import BSpline, _band2array

class KernelSmoother(object):
    """
    1D Kernel Density Regression/Kernel Smoother
    """
    def __init__(self, x, y, Kernel = kernel.DefaultKernel()):
        if isinstance(Kernel,kernel.DefaultKernel):
            Kernel = kernel.Gaussian()
        self.Kernel = Kernel
        self.x = np.array(x)
        self.y = np.array(y)

    def fit(self):
        pass

    def __call__(self, x):
        return np.array([self.predict(xx) for xx in x])

    def predict(self, x):
        return self.Kernel.smooth(self.x, self.y, x)

    def conf(self,x):
        return np.array([self.Kernel.smoothconf(self.x, self.y, xx) for xx in x])

    def var(self, x):
        return np.array([self.Kernel.smoothvar(self.x, self.y, xx) for xx in x])

    def std(self, x):
        return np.sqrt(self.var(x))

class PolySmoother(object):
    """
    Polynomial smoother up to a given order.
    Fit based on weighted least squares.

    The x values can be specified at instantiation or when called.
    """
    #JP: heavily adjusted to work as plugin replacement for bspline
    #   smoother in gam.py  initalized by function default_smoother
    #   Only fixed exceptions, I didn't check whether it is statistically
    #   correctand I think it is not, there are still be some dimension
    #   problems, and there were some dimension problems initially.
    # TODO: undo adjustments and fix dimensions correctly
    # comment: this is just like polyfit with initialization options
    #          and additional results (OLS on polynomial of x (x is 1d?))


    def df_fit(self):
        """
        Degrees of freedom used in the fit.
        """
        return self.order + 1

    def gram(self, d=None):
        #fake for spline imitation
        pass

    def smooth(self,*args, **kwds):
        return self.fit(*args, **kwds)

    def df_resid(self):
        """
        Residual degrees of freedom from last fit.
        """
        return self.N - self.order - 1

    def __init__(self, order, x=None):
        order = 3 # set this because we get knots instead of order
        self.order = order

        #print order, x.shape
        self.coef = np.zeros((order+1,), np.float64)
        if x is not None:
            if x.ndim > 1: x=x[0,:]
            self.X = np.array([x**i for i in range(order+1)]).T

    def __call__(self, x=None):

        if x is not None:
            if x.ndim > 1: x=x[0,:]
            X = np.array([(x**i) for i in range(self.order+1)])
        else: X = self.X
        #return np.squeeze(np.dot(X.T, self.coef))
        #need to check what dimension this is supposed to be
        if X.shape[1] == self.coef.shape[0]:
            return np.squeeze(np.dot(X, self.coef))#[0]
        else:
            return np.squeeze(np.dot(X.T, self.coef))#[0]

    def fit(self, y, x=None, weights=None):
        self.N = y.shape[0]
        if y.ndim == 1:
            y = y[:,None]
        if weights is None or np.isnan(weights).all():
            weights = 1
            _w = 1
        else:
            _w = np.sqrt(weights)[:,None]
        if x is None:
            if not hasattr(self, "X"):
                raise ValueError, "x needed to fit PolySmoother"
        else:
            if x.ndim > 1: x=x[0,:]
            self.X = np.array([(x**i) for i in range(self.order+1)]).T
        #print _w.shape

        X = self.X * _w

        _y = y * _w#[:,None]
        #self.coef = np.dot(L.pinv(X).T, _y[:,None])
        #self.coef = np.dot(L.pinv(X), _y)
        self.coef = L.lstsq(X, _y)[0]






if __name__ == "__main__":
    import numpy as np
    from scikits.statsmodels.sandbox import smoothers as s
    import matplotlib.pyplot as plt
    from numpy import sin, array, random

    import time

    x = random.normal(size = 500)
    y = array([sin(i*5)/i + 2*i + (3+i)*random.normal() for i in x])

    K = s.kernel.Gaussian(0.25)

    KS = s.KernelSmoother(x, y, K)

    KSx = np.arange(-3,3,0.1)
    #start = time.time()
    KSy = KS.conf(KSx)
    #print time.time() - start

    KVar = KS.std(KSx)

    fig = plt.figure()
    ax = fig.add_subplot(211)
    ax.plot(x,y,"+")
    ax.plot(KSx, KSy,"o")
    ax.set_ylim(-20,30)
    ax2 = fig.add_subplot(212)
    ax2.plot(KSx, KVar, "o")
    plt.show()














# comment out for now to remove dependency on _hbspline

##class SmoothingSpline(BSpline):
##
##    penmax = 30.
##
##    def fit(self, y, x=None, weights=None, pen=0.):
##        banded = True
##
##        if x is None:
##            x = self.tau[(self.M-1):-(self.M-1)] # internal knots
##
##        if pen == 0.: # can't use cholesky for singular matrices
##            banded = False
##
##        if x.shape != y.shape:
##            raise ValueError, 'x and y shape do not agree, by default x are the Bspline\'s internal knots'
##
##        bt = self.basis(x)
##        if pen >= self.penmax:
##            pen = self.penmax
##
##        if weights is None:
##            weights = np.array(1.)
##
##        wmean = weights.mean()
##        _w = np.sqrt(weights / wmean)
##        bt *= _w
##
##        # throw out rows with zeros (this happens at boundary points!)
##
##        mask = np.flatnonzero(1 - np.alltrue(np.equal(bt, 0), axis=0))
##
##        bt = bt[:, mask]
##        y = y[mask]
##
##        self.df_total = y.shape[0]
##
##        if bt.shape[1] != y.shape[0]:
##            raise ValueError, "some x values are outside range of B-spline knots"
##        bty = np.dot(bt, _w * y)
##        self.N = y.shape[0]
##        if not banded:
##            self.btb = np.dot(bt, bt.T)
##            _g = _band2array(self.g, lower=1, symmetric=True)
##            self.coef, _, self.rank = L.lstsq(self.btb + pen*_g, bty)[0:3]
##            self.rank = min(self.rank, self.btb.shape[0])
##        else:
##            self.btb = np.zeros(self.g.shape, np.float64)
##            nband, nbasis = self.g.shape
##            for i in range(nbasis):
##                for k in range(min(nband, nbasis-i)):
##                    self.btb[k, i] = (bt[i] * bt[i+k]).sum()
##
##            bty.shape = (1, bty.shape[0])
##            self.chol, self.coef = solveh_banded(self.btb +
##                                                 pen*self.g,
##                                                 bty, lower=1)
##
##        self.coef = np.squeeze(self.coef)
##        self.resid = np.sqrt(wmean) * (y * _w - np.dot(self.coef, bt))
##        self.pen = pen
##
##    def gcv(self):
##        """
##        Generalized cross-validation score of current fit.
##        """
##
##        norm_resid = (self.resid**2).sum()
##        return norm_resid / (self.df_total - self.trace())
##
##    def df_resid(self):
##        """
##        self.N - self.trace()
##
##        where self.N is the number of observations of last fit.
##        """
##
##        return self.N - self.trace()
##
##    def df_fit(self):
##        """
##        = self.trace()
##
##        How many degrees of freedom used in the fit?
##        """
##        return self.trace()
##
##    def trace(self):
##        """
##        Trace of the smoothing matrix S(pen)
##        """
##
##        if self.pen > 0:
##            _invband = _hbspline.invband(self.chol.copy())
##            tr = _trace_symbanded(_invband, self.btb, lower=1)
##            return tr
##        else:
##            return self.rank
##
##class SmoothingSplineFixedDF(SmoothingSpline):
##    """
##    Fit smoothing spline with approximately df degrees of freedom
##    used in the fit, i.e. so that self.trace() is approximately df.
##
##    In general, df must be greater than the dimension of the null space
##    of the Gram inner product. For cubic smoothing splines, this means
##    that df > 2.
##    """
##
##    target_df = 5
##
##    def __init__(self, knots, order=4, coef=None, M=None, target_df=None):
##        if target_df is not None:
##            self.target_df = target_df
##        BSpline.__init__(self, knots, order=order, coef=coef, M=M)
##        self.target_reached = False
##
##    def fit(self, y, x=None, df=None, weights=None, tol=1.0e-03):
##
##        df = df or self.target_df
##
##        apen, bpen = 0, 1.0e-03
##        olddf = y.shape[0] - self.m
##
##        if not self.target_reached:
##            while True:
##                curpen = 0.5 * (apen + bpen)
##                SmoothingSpline.fit(self, y, x=x, weights=weights, pen=curpen)
##                curdf = self.trace()
##                if curdf > df:
##                    apen, bpen = curpen, 2 * curpen
##                else:
##                    apen, bpen = apen, curpen
##                    if apen >= self.penmax:
##                        raise ValueError, "penalty too large, try setting penmax higher or decreasing df"
##                if np.fabs(curdf - df) / df < tol:
##                    self.target_reached = True
##                    break
##        else:
##            SmoothingSpline.fit(self, y, x=x, weights=weights, pen=self.pen)
##
##class SmoothingSplineGCV(SmoothingSpline):
##
##    """
##    Fit smoothing spline trying to optimize GCV.
##
##    Try to find a bracketing interval for scipy.optimize.golden
##    based on bracket.
##
##    It is probably best to use target_df instead, as it is
##    sometimes difficult to find a bracketing interval.
##
##    """
##
##    def fit(self, y, x=None, weights=None, tol=1.0e-03,
##            bracket=(0,1.0e-03)):
##
##        def _gcv(pen, y, x):
##            SmoothingSpline.fit(y, x=x, pen=np.exp(pen), weights=weights)
##            a = self.gcv()
##            return a
##
##        a = golden(_gcv, args=(y,x), brack=(-100,20), tol=tol)
##
##def _trace_symbanded(a,b, lower=0):
##    """
##    Compute the trace(a*b) for two upper or lower banded real symmetric matrices.
##    """
##
##    if lower:
##        t = _zero_triband(a * b, lower=1)
##        return t[0].sum() + 2 * t[1:].sum()
##    else:
##        t = _zero_triband(a * b, lower=0)
##        return t[-1].sum() + 2 * t[:-1].sum()
##
##
##
##def _zero_triband(a, lower=0):
##    """
##    Zero out unnecessary elements of a real symmetric banded matrix.
##    """
##
##    nrow, ncol = a.shape
##    if lower:
##        for i in range(nrow): a[i,(ncol-i):] = 0.
##    else:
##        for i in range(nrow): a[i,0:i] = 0.
##    return a
