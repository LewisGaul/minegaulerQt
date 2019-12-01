
from ..minefield import Grid
from ..utils import get_nbrs, prettify_grid


def find_numbers(board):
    """Put the displayed numbers in a dictionary with coordinate as key,
    storing their neighbouring clickable cells."""
    x_size, y_size = len(board[0]), len(board)
    numbers = []
    # Look through all the cells to find the revealed numbers
    index = 0
    for x in range(x_size):
        for y in range(y_size):
            contents = board[y][x]
            if type(contents) is str or contents == 0:
                continue
            val = num = contents
            nbrs = get_nbrs(x, y, x_size, y_size)
            clickable_nbrs = []
            for (i, j) in nbrs:
                c = board[j][i]
                # Ignore flags [for now]
                if str(c)[0] in ['L']:
                    val -= int(c[1])
                elif str(c)[0] in ['U', 'F', 'M']:
                    # Include displayed mines for state before game was lost
                    clickable_nbrs.append((i, j))
            clickable_nbrs.sort() #helps with debugging but not necessary
            numbers.append({'index': index,
                            'num':   num,
                            'val':   val,
                            'coord': (x, y),
                            'nbrs':  clickable_nbrs})
            index += 1
    return numbers

def find_groups(numbers):
    """Find and return a list containing the equivalence groups."""
    groups = []
    # Reorganise from a dictionary of displayed numbers with their neighbours
    #  (numbers) to a dictionary of unclicked cells with their
    #  neighbouring displayed numbers (nr_nbrs_of_unclicked).
    nr_nbrs_of_unclicked = dict()
    for nr_index, nr in enumerate(numbers):
        for unclicked in nr['nbrs']:
            nr_nbrs_of_unclicked.setdefault(unclicked, []).append(nr_index)
    grouped_nrs = {}
    for grp_coord, nr_group in nr_nbrs_of_unclicked.items():
        grouped_nrs.setdefault(tuple(sorted(nr_group)), []).append(grp_coord)

    index = 0
    for nr_nbrs, coords in grouped_nrs.items():
        # Store the equivalence group referencing its coords and the shared
        #  number coordinates.
        grp = {'index':    index,
               'coords':   coords,
               'size':     len(coords),
               'nrs':      list(nr_nbrs), #[numbers[j] for j in nr_nbrs],
               'contains': 0
               }
        groups.append(grp)
        index += 1
    # Store the indices of the groups in the neighbouring numbers
    for i, g in enumerate(groups):
        for j in g['nrs']:
            nr = numbers[j]
            if 'grps' not in nr:
                nr['grps'] = []
            nr['grps'].append(i)
    return groups

def print_groups(groups, hint=None):
    if hint is None:
        disp = groups
    elif type(hint) is int:
        disp = [groups[hint]]
    elif type(hint) is dict:
        disp = [hint]
    elif type(hint) is list:
        if len(hint) == 0:
            return
        if type(hint[0]) is int:
            disp = map(lambda i: groups[i], hint)
        elif type(hint[0]) is dict:
            disp = hint
    else:
        return
    for g in disp:
        h = g.copy()
        if 'index' in g:
            print(g['index'], end=' ')
            h.pop('index')
        h.pop('size')
        print(h)





test_boards = {}
test_boards[1] = [
    ['U', 'U', 'U', 'U', 'U', 4, 2, 1],
    [1, 2, 'U', 'U', 'U', 'U', 'U', 1],
    [1, 1, 'U', 'U', 'U', 'U', 'U', 'U'],
    ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
    ['U', 'U', 2, 1, 1, 1, 'U', 'U'],
    [1, 1, 1, 0, 0, 1, 'U', 'U'],
    [0, 0, 0, 0, 0, 1, 'U', 'U'],
    [0, 0, 0, 0, 0, 1, 1, 1]
]
test_boards[3] = [
    ['U', 'U', 'U', 'U', 'U', 'U', 'U', 1, 0, 0, 2, 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 2, 1, 1, 1, 0, 1, 'U', 'U', 'U', 'U'],
    ['U', 'U', 'U', 'U', 'U', 'U', 'U', 2, 1, 0, 4, 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 4, 2, 'U', 1, 1, 2, 'U', 'U', 'U', 'U'],
    ['U', 'U', 'U', 'U', 'U', 'U', 3, 'U', 1, 0, 3, 'U', 5, 4, 2, 5, 'U', 'U', 'U', 'U', 'U', 2, 1, 1, 1, 'U', 5, 'U', 'U', 'U'],
    ['U', 'U', 'U', 'U', 'U', 'U', 'U', 2, 1, 0, 2, 3, 'U', 2, 1, 2, 3, 'U', 5, 'U', 3, 1, 0, 0, 1, 1, 4, 'U', 'U', 'U'],
    ['U', 'U', 'U', 'U', 'U', 'U', 'U', 3, 2, 1, 0, 1, 1, 2, 'U', 1, 2, 'U', 'U', 2, 2, 1, 1, 0, 0, 1, 3, 'U', 'U', 'U'],
    ['U', 'U', 3, 1, 2, 'U', 'U', 'U', 'U', 2, 1, 1, 1, 1, 3, 3, 3, 2, 2, 1, 2, 'U', 3, 1, 0, 1, 'U', 'U', 'U', 'U'],
    ['U', 'U', 2, 1, 2, 2, 3, 3, 'U', 'U', 'U', 'U', 2, 1, 2, 'U', 3, 1, 1, 1, 3, 'U', 'U', 2, 1, 3, 3, 'U', 'U', 'U'],
    ['U', 'U', 'U', 1, 0, 0, 0, 1, 1, 1, 1, 'U', 'U', 1, 2, 2, 3, 'U', 1, 1, 'U', 3, 2, 2, 'U', 2, 'U', 4, 'U', 'U'],
    ['U', 4, 2, 1, 0, 0, 0, 0, 0, 0, 1, 'U', 2, 2, 1, 1, 2, 2, 2, 1, 1, 1, 0, 1, 1, 2, 3, 'U', 3, 1],
    ['U', 'U', 2, 1, 1, 0, 1, 1, 1, 0, 1, 'U', 1, 1, 'U', 2, 2, 'U', 1, 0, 0, 1, 1, 1, 0, 0, 2, 'U', 2, 0],
    ['U', 'U', 3, 'U', 1, 1, 2, 'U', 1, 1, 2, 'U', 1, 1, 2, 'U', 2, 1, 1, 0, 1, 2, 'U', 1, 1, 1, 2, 1, 1, 0],
    [1, 2, 'U', 2, 1, 1, 'U', 3, 2, 1, 'U', 'U', 2, 2, 2, 3, 2, 1, 0, 0, 1, 'U', 4, 3, 2, 'U', 3, 3, 2, 1],
    [0, 1, 1, 1, 0, 1, 2, 'U', 1, 2, 3, 'U', 'U', 3, 'U', 3, 'U', 1, 0, 1, 2, 3, 'U', 'U', 2, 2, 'U', 'U', 'U', 1],
    [1, 1, 1, 0, 0, 0, 1, 1, 2, 2, 'U', 'U', 4, 'U', 3, 'U', 2, 1, 0, 2, 'U', 3, 2, 2, 1, 1, 2, 3, 2, 1],
    [1, 'U', 3, 3, 1, 2, 1, 1, 2, 'U', 'U', 2, 'U', 3, 3, 2, 2, 2, 1, 3, 'U', 2, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 4, 'U', 4, 'U', 5, 'U', 1, 3, 'U', 'U', 3, 2, 'U', 1, 1, 'U', 2, 'U', 3, 2, 2, 0, 0, 0, 0, 1, 1, 1, 0],
    [1, 4, 'U', 'U', 'U', 'U', 4, 1, 3, 'U', 'U', 2, 1, 1, 1, 1, 1, 2, 1, 3, 'U', 2, 0, 1, 1, 1, 1, 'U', 3, 2],
    ['U', 'U', 1, 'U', 'U', 'U', 4, 1, 3, 'U', 'U', 2, 0, 1, 3, 3, 2, 0, 0, 2, 'U', 4, 4, 4, 'U', 1, 3, 5, 'U', 'U'],
    ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 1, 1, 2, 'U', 'U', 3, 1, 1, 3, 3, 'U', 'U', 'U', 3, 1, 3, 'U', 'U', 'U'],
    ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 4, 2, 5, 'U', 'U', 'U'],
    ['U', 'U', 'U', 1, 'U', 'U', 'U', 'U', 'U', 2, 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
    ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U']
]
if __name__ == '__main__':
    print('')
    def test(num, per_cell=1):
        print(prettify_grid(test_boards[num], {0:'-', 'U':'#'}))
        board = SolverReducedBoard(test_boards[num], ignore_flags=True,
                                   per_cell=per_cell)
        print(board)
        # board.print_numbers()
        return board
