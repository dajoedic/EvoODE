"""Independent NumPy/SciPy implementation of the Q5-W reference algorithm.

The read-only MATLAB reference determines the algorithm, not this module's text.
All public coefficients are expressed in the original library coordinates.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import math
import numpy as np
from scipy.linalg import lstsq
from scipy.optimize import brentq
from scipy.signal import convolve

LAMBDAS = np.logspace(-4, 0, 100)


@dataclass(frozen=True)
class Column:
    name: str
    function: Callable[[np.ndarray], np.ndarray]
    powers: tuple[int, ...]


def scales(x, columns):
    """Reference scale_Theta=2: state 2p-norm, not unit column norms."""
    powers = np.asarray([c.powers for c in columns], dtype=int)
    p = int(powers.max())
    if p == 0:
        return np.ones(len(columns))
    state_scale = np.sum(np.abs(x) ** (2*p), axis=0) ** (1/(2*p))
    state_scale[state_scale == 0] = 1
    return np.prod(state_scale[None, :] ** (-powers), axis=1)


def _corner(y):
    """Relative error of two endpoint-interpolating lines, sharing a knot."""
    n = len(y)
    if n < 3 or not np.all(np.isfinite(y)) or np.max(np.abs(y)) == 0:
        raise ValueError("corner spectrum is degenerate")
    y = y / np.max(np.abs(y)) * n
    errors = np.full(n, np.inf)
    for k in range(1, n-1):
        left = np.linspace(y[0], y[k], k+1)
        right = np.linspace(y[k], y[-1], n-k)
        with np.errstate(divide='ignore', invalid='ignore'):
            errors[k] = np.sum(((left-y[:k+1])/y[:k+1])**2) + np.sum(((right-y[k:])/y[k:])**2)
    if not np.any(np.isfinite(errors)):
        raise ValueError("no finite corner fit")
    return int(np.argmin(errors))


def corner_parameters(x):
    n = len(x)
    spectrum = np.abs(np.fft.fftshift(np.fft.fft(x)))[:math.ceil(n/2)] / math.sqrt(2*math.ceil(n/2))
    peak = int(np.argmax(spectrum))
    a = _corner(np.cumsum(spectrum[:peak+1]))
    b = _corner(np.log(spectrum[:peak+1]))
    knot = (a+b)//2
    frequency = max(peak-knot+1, 1)
    logtau = math.log(1e-16)
    def equation(m):
        return math.log((2*m-1)/m**2)*(4*math.pi**2*frequency**2*m**2-3*n**2)-2*n**2*logtau
    root = brentq(equation, 1, 2e8)
    if root > n/2-1:
        root = n/(2*frequency)
    m = min((n-1)//2, math.ceil(root))
    if m < 2:
        raise ValueError("corner support has fewer than five points")
    p = max(2, math.floor(logtau/math.log(1-(1-1/m)**2)))
    return dict(half_support_samples=m, degree=p, corner_frequency=frequency)


def estimate_noise(y):
    d1 = (y[3:-1]-y[1:-3])/2
    d2 = (y[4:]-y[:-4])/4
    sigma = math.sqrt(8/5)*np.sqrt(np.mean((d1-d2)**2))
    if sigma < .01:
        d4 = (y[8:]-y[:-8])/8
        finer = 4/3*(d1-d2/4)
        coarser = 4/3*(d2[2:-2]-d4/4)
        sigma = math.sqrt(576/714)*np.sqrt(np.mean((finer[2:-2]-coarser)**2))
    return float(sigma)


def smooth(t, y):
    n = len(y)
    dt = np.mean(np.diff(t))
    sigma = estimate_noise(y)
    width = min(math.ceil(n/math.ceil(n/100)), n//8)
    for _ in range(99):
        radius = min(max(2*width, 3), (n-1)//2)
        z = np.arange(-radius, radius+1)*dt
        kernel = np.linalg.pinv(np.column_stack([np.ones(len(z)), z, z*z]))[2]
        curvature = 2*np.mean(np.abs(convolve(y, kernel, mode='valid')))
        c = sigma**2 / ((curvature+1e-6)**2*dt**4/144)
        root = brentq(lambda v: v**5-v**3-c, 1, max(2., (c+1)**.2+2))
        updated = min(math.floor((root-1)/2), n//8)
        if updated == width:
            break
        width = updated
    weights = np.ones(2*width+1)/(2*width+1)
    return convolve(np.pad(y, (width, width), mode='reflect'), weights, mode='valid'), 2*width+1


def weak_design(t, x, columns):
    """Trapezoidal integration on observed times, with physical-time supports."""
    t, x = np.asarray(t, float), np.asarray(x, float)
    if len(t) < 9 or np.any(np.diff(t) <= 0) or not np.all(np.isfinite(x)):
        raise ValueError("finite states and at least nine increasing times required")
    metadata = [corner_parameters(y) for y in x.T]
    scaling = scales(x, columns)  # Before smoothing, as in the reference.
    filtered = np.empty_like(x)
    for eq, y in enumerate(x.T):
        filtered[:, eq], metadata[eq]['smoothing_window'] = smooth(t, y)
    theta = np.column_stack([c.function(filtered) for c in columns])*scaling
    dt = np.mean(np.diff(t))
    designs, targets = [], []
    uniform = np.allclose(np.diff(t), dt, rtol=1e-10, atol=1e-14)
    for eq, info in enumerate(metadata):
        m, p = info['half_support_samples'], info['degree']
        half = m*dt
        info['half_support_time'] = float(half)
        centers = np.flatnonzero((t-t[0] >= half-1e-12*dt) & (t[-1]-t >= half-1e-12*dt))
        info['n_test_functions'] = len(centers)
        if uniform:
            z = np.arange(-m, m+1)/m
            phi = (1-z*z)**p
            minus_derivative = 2*p*z*(1-z*z)**(p-1)/half
            g = convolve(theta, phi[:, None]*dt, mode='valid', method='auto')
            b = convolve(filtered[:, eq], -minus_derivative*dt, mode='valid')
        else:
            g, b = [], []
            for center in centers:
                lo = np.searchsorted(t, t[center]-half, side='left')
                hi = np.searchsorted(t, t[center]+half, side='right')
                times = t[lo:hi]
                z = (times-t[center])/half
                base = np.maximum(1-z*z, 0)
                phi = base**p
                negd = 2*p*z*base**(p-1)/half
                # Include the zero-valued support boundaries in the quadrature.
                times = np.r_[t[center]-half, times, t[center]+half]
                g.append(np.trapezoid(np.vstack([np.zeros(len(columns)), theta[lo:hi]*phi[:, None], np.zeros(len(columns))]), times, axis=0))
                b.append(np.trapezoid(np.r_[0, filtered[lo:hi, eq]*negd, 0], times))
            g, b = np.asarray(g), np.asarray(b)
        designs.append(g)
        targets.append(b)
    return designs, targets, scaling, metadata


def select_model(g, b, scaling, cap=None, lambdas=LAMBDAS):
    """MSTLS with scale-dependent bounds and per-equation loss minimization."""
    g, b, scaling = np.asarray(g), np.asarray(b), np.asarray(scaling)
    if g.ndim != 2 or g.shape[0] == 0 or not np.all(np.isfinite(g)):
        raise ValueError("invalid weak design")
    solves = 0
    def solve(active):
        nonlocal solves
        solves += 1
        result = np.zeros(g.shape[1])
        if np.any(active):
            result[active] = lstsq(g[:, active], b, lapack_driver='gelsy')[0]
        return result
    full = solve(np.ones(g.shape[1], bool))
    denom = np.linalg.norm(g@full)
    norms = np.linalg.norm(g, axis=0)
    bounds = np.divide(np.linalg.norm(b)*scaling, norms, out=np.full(len(norms), np.inf), where=norms>0)
    models, losses, counts = [], [], []
    for threshold in lambdas:
        coefficient = full*scaling
        removed = np.zeros(g.shape[1], bool)
        lower = threshold*np.maximum(1, bounds)
        upper = np.minimum(1, bounds)/threshold
        for _ in range(g.shape[1]):
            new_removed = (np.abs(coefficient)<lower) | (np.abs(coefficient)>upper) | (norms == 0)
            if np.array_equal(new_removed, removed):
                break
            removed = new_removed
            coefficient = solve(~removed)*scaling
        in_design_coordinates = coefficient/scaling
        residual = np.linalg.norm(g@(in_design_coordinates-full))
        projection = residual/denom if denom else (0. if residual == 0 else np.inf)
        count = int(np.count_nonzero(coefficient))
        losses.append(float(1.6*projection+.4*count/g.shape[1]))
        counts.append(count)
        models.append(coefficient)
    eligible = [i for i, count in enumerate(counts) if cap is None or count <= cap]
    chosen = min(eligible, key=lambda i: (losses[i], lambdas[i])) if eligible else None
    return (models[chosen] if chosen is not None else np.zeros(g.shape[1])), dict(
        lambda_grid_index=chosen, lambda_grid_index_base=0,
        support_indices=[] if chosen is None else np.flatnonzero(models[chosen]).tolist(),
        coefficients_original_scale=(np.zeros(g.shape[1]) if chosen is None else models[chosen]).tolist(),
        lambda_hat=None if chosen is None else float(lambdas[chosen]),
        lambda_at_grid_end=chosen in (0, len(lambdas)-1), selected=chosen is not None,
        lambda_grid=np.asarray(lambdas).tolist(), loss_curve=losses, term_counts=counts,
        least_squares_solves=solves)


def fit(t, x, columns, cap=None):
    designs, targets, scaling, metadata = weak_design(t, x, columns)
    coefficients = []
    for g, b, info in zip(designs, targets, metadata):
        coefficient, selection = select_model(g, b, scaling, cap)
        coefficients.append(coefficient)
        info.update(selection)
    return np.asarray(coefficients), metadata
