

import random as rnd
import logging

from utils import prettify_grid, get_nbrs


class Minefield(list):
    def __init__(self, x_size, y_size):
        super().__init__()
        for j in range(y_size):
            row = x_size*[0]
            self.append(row)
        self.x_size, self.y_size = x_size, y_size
        self.all_coords = [(x, y) for x in range(x_size) for y in range(y_size)]
        self.nr_mines = 0
        self.mine_coords = []
        self.completed_board = []
        for j in range(y_size):
            self.completed_board.append(x_size*[0])
    def __repr__(self):
        mines = " with {} mines".format(self.nr_mines) if self.nr_mines else ""
        return "<{}x{} minefield{}>".format(self.x_size, self.y_size, mines)
    def __str__(self):
        return prettify_grid(self)
    def print_completed_board(self):
        print(prettify_grid(self.completed_board, {0: '-'}) + '\n')
    def create_from_list(self, coords):
        assert self.mine_coords == [], "Minefield already created."
        self.mine_coords = coords
        self.nr_mines = len(self.mine_coords)
        for (x, y) in coords:
            self[y][x] += 1
    def create(self, nr_mines, per_cell=1, safe_coords=[]):
        assert self.mine_coords == [], "Minefield already created."
        self.nr_mines = nr_mines
        self.per_cell = per_cell
        assert (nr_mines < (self.x_size*self.y_size - 1) * per_cell), (
            "Too many mines ({}) for grid with dimensions {} x {}.".format(
                nr_mines, self.x_size, self.y_size))
        avble_coords = [c for c in self.all_coords if c not in safe_coords]
        # Can't give opening on first click if too many mines.
        if nr_mines > len(avble_coords) * per_cell:
            logging.warning(
                "Unable to create minefield with requested safe_coords - "
                "too many mines ({} mines, {} cells, {} safe_coords).".format(
                    nr_mines, self.x_size*self.y_size, len(safe_coords)))
            avble_coords = self.all_coords[:]
        if per_cell == 1:
            rnd.shuffle(avble_coords)
            self.create_from_list(avble_coords[:nr_mines])
        else:
            n = 0
            while n < nr_mines:
                pos = rnd.randint(0, self.x_size*self.y_size - 1)
                x, y = pos % self.x_size, pos // self.x_size
                if (x, y) not in safe_coords and self[y][x] < self.per_cell:
                    self[y][x] += 1
                    self.mine_coords.append((x, y))
                    n += 1
            self.mine_coords.sort()
        # print(prettify_grid(self))
        self.get_completed_board()
        self.get_3bv()
    def get_completed_board(self):
        for (x, y) in self.all_coords:
            mines = self[y][x]
            if mines > 0:
                # print((x, y))
                self.completed_board[y][x] = 'F' + str(mines)
                # print(prettify_grid(self.completed_board))
                for (i, j) in get_nbrs(x, y, self.x_size, self.y_size):
                    # print("  ", (i, j), self[j][i])
                    if self[j][i] == 0:
                        self.completed_board[j][i] += mines
    def get_openings(self):
        self.openings = []
        all_found = set()
        for (x, y) in self.all_coords:
            coord = (x, y)
            if self.completed_board[y][x] == 0 and coord not in all_found:
                opening = set([coord])
                check = set([coord])
                while check:
                    c = check.pop()
                    nbrs = set(get_nbrs(c[0], c[1], self.x_size, self.y_size))
                    check |= {(i, j) for (i, j) in nbrs - opening
                               if self.completed_board[j][i] == 0}
                    opening |= nbrs
                self.openings.append(sorted(opening))
                all_found |= opening
    def get_3bv(self):        #[Move to C?]
        if hasattr(self, 'bbbv'):
            return self.bbbv
        self.get_openings()
        clicks = len(self.openings)
        exposed = len({c for opening in self.openings for c in opening})
        clicks += self.x_size*self.y_size - len(set(self.mine_coords)) - exposed
        self.bbbv = clicks

    def serialise(self, path):
        assert mine_coords is not None, (
            "Minefield not initialised - nothing to save.")
        # No need to be secure.
        obj = dict()
        for attr in ['mine_coords', 'x_size', 'y_size', 'per_cell']:
            obj[attr] = getattr(self, attr)
        with open(path, 'w') as f:
            json.dump(obj, f)
    @classmethod
    def deserialise(cls, path):
        with open(path, 'r') as f:
            obj = json.load(f)
        mf = cls(obj['x_size'], obj['y_size'])
        # json stores tuples as lists - convert back.
        mine_coords = map(tuple, obj['mine_coords'])
        mf.create_from_list(mine_coords)
        mf.per_cell = obj['per_cell']
        return mf





if __name__ == '__main__':
    mf = Minefield(8, 4)
    mf.create(7)
    mf.print_completed_board()
