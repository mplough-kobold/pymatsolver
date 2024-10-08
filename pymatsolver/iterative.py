import numpy as np
import scipy
import scipy.sparse as sp
from scipy.sparse.linalg import aslinearoperator, bicgstab
from packaging.version import Version
from pymatsolver.solvers import Base

# The tol kwarg was removed from bicgstab in scipy 1.14.0.
# See https://docs.scipy.org/doc/scipy-1.12.0/reference/generated/scipy.sparse.linalg.bicgstab.html
TOL_ARG_NAME = "rtol" if Version(scipy.__version__) >= Version("1.14.0") else "tol"


class BicgJacobi(Base):
    """Bicg Solver with Jacobi preconditioner"""

    _factored = False
    solver = None
    maxiter = 1000
    tol = 1E-6

    def __init__(self, A, symmetric=True):
        self.A = A
        self.symmetric = symmetric
        self.dtype = A.dtype
        self.solver = bicgstab

    def factor(self):
        if self._factored:
            return
        nSize = self.A.shape[0]
        Ainv = sp.spdiags(1./self.A.diagonal(), 0, nSize, nSize)
        self.M = aslinearoperator(Ainv)
        self._factored = True

    def _solve1(self, rhs):
        self.factor()
        sol, info = self.solver(
            self.A,
            rhs,
            **{
                TOL_ARG_NAME: self.tol,
                "maxiter": self.maxiter,
                "M": self.M,
            }
        )
        return sol

    def _solveM(self, rhs):
        self.factor()
        sol = []
        for icol in range(rhs.shape[1]):
            sol.append(
                self.solver(
                    self.A,
                    rhs[:, icol].flatten(),
                    **{
                        TOL_ARG_NAME: self.tol,
                        "maxiter": self.maxiter,
                        "M": self.M,
                    }
                )[0]
            )
        out = np.hstack(sol)
        out.shape
        return out

    def clean(self):
        self.M = None
        self.A = None
        self._factored = False
