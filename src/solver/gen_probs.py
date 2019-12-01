from math import factorial as fac, log, exp
# import time as tm


#xmax, s, m: combs
stored_combs = {
    2: {
        1: {1: 1, 2: 1},
        2: {}
    },
    3: {
    }
}

def get_combs(m, s, xmax):
    """
    Takes integer arguments
        - s (number of cells),
        - m (number of mines),
        - xmax=1 (maximum number of mines per cell).
    Returns the number of arrangements of the mines, treated as distinct."""
    if m > s*xmax:
        return 0
    elif m == 0 or s == 1:
        return 1
    elif xmax == 1:
        return fac(s) // fac(s - m)
    elif xmax >= m:
        return s**m #/ fac(s)
    else:
        try:
            return stored_combs[xmax][s][m]
        except KeyError:
            # print(f"Finding for s={s} m={m}")
            return find_combs(m, s, xmax)

def set_combs(m, s, xmax, val):
    d = stored_combs[xmax].setdefault(s, {})
    d[m] = val

def find_combs(m, s, xmax): #aka w
    assert xmax in [2, 3]
    max_trip_mines = m // 3 if xmax == 3 else 0
    initial = fac(m) * fac(s)
    tot = 0
    for t in range(max(0, m - 2*s), max_trip_mines + 1):
        for d in range(max(0, m - 2*t - s), (m - 3*t) // 2 + 1):
            tot += initial // (2**d * 6**t * fac(d) * fac(t)
                               * fac(m - 2*d - 3*t) * fac(s - m + d + 2*t))
            if t == 0 and xmax == 3:
                set_combs(s, m, 2, tot)
    set_combs(s, m, xmax, tot)
    return tot

def get_unsafe_prob(m, s, xmax):
    """
    Takes integer arguments
        - s (number of cells),
        - m (number of mines),
        - xmax=1 (maximum number of mines per cell).
    Returns the probability of a cell containing at least one mine."""
    if m > s*xmax:
        # raise ValueError("Too many mines for group size.")
        return 0
    if xmax == 1:
        return m / s
    elif xmax >= m:
        return 1 - (1 - 1/s)**m
    elif m > xmax*(s - 1):
        return 1
    else:
        return 1 - exp(log(get_combs(m, s-1, xmax)) - log(get_combs(m, s, xmax)))# / s)
