#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2022 Stéphane Caron and the qpsolvers contributors.
# Copyright (C) 2021 Dustin Kenefake
#
# This file is part of qpsolvers.
#
# qpsolvers is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# qpsolvers is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with qpsolvers. If not, see <http://www.gnu.org/licenses/>.

"""
Solver interface for `Gurobi <https://www.gurobi.com/>`__.

The Gurobi Optimizer suite ships several solvers for mathematical programming,
including problems that have linear constraints, bound constraints, integrality
constraints, cone constraints, or quadratic constraints. It targets modern CPU
architectures and multi-core processors,

See the :ref:`installation page <gurobi-install>` for additional instructions
on installing this solver.
"""

from typing import Optional, Union
import warnings

import numpy as np
import scipy.sparse as spa
from gurobipy import GRB, Model


def gurobi_solve_qp(
    P: Union[np.ndarray, spa.csc_matrix],
    q: np.ndarray,
    G: Optional[Union[np.ndarray, spa.csc_matrix]] = None,
    h: Optional[np.ndarray] = None,
    A: Optional[Union[np.ndarray, spa.csc_matrix]] = None,
    b: Optional[np.ndarray] = None,
    lb: Optional[np.ndarray] = None,
    ub: Optional[np.ndarray] = None,
    initvals: Optional[np.ndarray] = None,
    verbose: bool = False,
    **kwargs,
) -> Optional[np.ndarray]:
    """
    Solve a Quadratic Program defined as:

    .. math::

        \\begin{split}\\begin{array}{ll}
        \\mbox{minimize} &
            \\frac{1}{2} x^T P x + q^T x \\\\
        \\mbox{subject to}
            & G x \\leq h                \\\\
            & A x = b                    \\\\
            & lb \\leq x \\leq ub
        \\end{array}\\end{split}

    using `Gurobi <http://www.gurobi.com/>`_.

    Parameters
    ----------
    P :
        Primal quadratic cost matrix.
    q :
        Primal quadratic cost vector.
    G :
        Linear inequality constraint matrix.
    h :
        Linear inequality constraint vector.
    A :
        Linear equality constraint matrix.
    b :
        Linear equality constraint vector.
    lb :
        Lower bound constraint vector.
    ub :
        Upper bound constraint vector.
    initvals :
        Warm-start guess vector (not used).
    verbose :
        Set to `True` to print out extra information.

    Returns
    -------
    :
        Solution to the QP, if found, otherwise ``None``.

    Notes
    -----
    Keyword arguments are forwarded to Gurobi as parameters. For instance, we
    can call ``gurobi_solve_qp(P, q, G, h, u, FeasibilityTol=1e-8,
    OptimalityTol=1e-8)``. Gurobi settings include the following:

    .. list-table::
       :widths: 30 70
       :header-rows: 1

       * - Name
         - Description
       * - ``FeasibilityTol``
         - Primal feasibility tolerance.
       * - ``OptimalityTol``
         - Dual feasibility tolerance.
       * - ``PSDTol``
         - Positive semi-definite tolerance.
       * - ``TimeLimit``
         - Run time limit in seconds, 0 to disable.

    Check out the `Parameter Descriptions
    <https://www.gurobi.com/documentation/9.5/refman/parameter_descriptions.html>`_
    documentation for all available Gurobi parameters.

    Lower values for primal or dual tolerances yield more precise solutions at
    the cost of computation time. See *e.g.* [tolerances]_ for a primer of
    solver tolerances.
    """
    if initvals is not None:
        warnings.warn("warm-start values are ignored by this wrapper")

    model = Model()
    if not verbose:
        model.setParam(GRB.Param.OutputFlag, 0)
    for param, value in kwargs.items():
        model.setParam(param, value)

    num_vars = P.shape[0]
    identity = spa.eye(num_vars)
    x = model.addMVar(
        num_vars, lb=-GRB.INFINITY, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS
    )
    if G is not None:
        model.addMConstr(G, x, GRB.LESS_EQUAL, h)
    if A is not None:
        model.addMConstr(A, x, GRB.EQUAL, b)
    if lb is not None:
        model.addMConstr(identity, x, GRB.GREATER_EQUAL, lb)
    if ub is not None:
        model.addMConstr(identity, x, GRB.LESS_EQUAL, ub)
    objective = 0.5 * (x @ P @ x) + q @ x
    model.setObjective(objective, sense=GRB.MINIMIZE)
    model.optimize()
    status = model.status
    if status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return None
    return np.array(x.X)
