

def prettify_grid(grid, repr_map=dict(), cell_size=1):
    ret = ''
    for row in grid:
        for i in row:
            cell = '{:>%d}' % cell_size
            ret += cell.format(
                repr_map[i] if i in repr_map else str(i)[:cell_size])
            ret += ' '
        ret = ret[:-1] # Remove trailing space
        ret += '\n'
    ret = ret[:-1] # Remove trailing newline
    return ret

def get_nbrs(x, y, x_size, y_size):
    nbrs = []
    for i in range(max(0,x-1), min(x_size,x+2)):
        for j in range(max(0,y-1), min(y_size,y+2)):
            nbrs.append((i, j))
    return nbrs

def calc_3bvps(h):
    # Round up to 2 d.p. (converting time to seconds)
    return (1e5 * h['3bv'] // h['time']) / 100 + 0.01

def blend_colours(ratio, high=(255, 0, 0), low=(255, 255, 64), fmt='rgb'):
    colour = tuple(int(low[i] + ratio*(high[i] - low[i])) for i in range(3))
    if fmt.lower() == 'rgb':
        return colour
    elif fmt == 'hex':
        return '#%02x%02x%02x' % colour
    else:
        raise ValueError(f"Invalid format '{fmt}'")
