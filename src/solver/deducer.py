

from ..minefield import Grid
from ..utils import prettify_grid
from . import find_numbers, find_groups, print_groups


class SolverReducedBoard(Grid):
    """
    Takes a board which is being played and tries to make as many logical
    deductions as possible. This is done in the following steps:
     - Check for groups which have a fixed number of mines because of being the
       only group next to a number (including after the numbers are reduced)
       (e.g. corner or edge situations);
     - Check for groups which must have at least one mine (e.g. 3-2 situation).
    The numbers in the grid are reduced when certain mine positions are found,
    however mines can not always be shown as it may be that it is known there is
    one mine in a group of three cells for example.
    """
    def __init__(self, board, ignore_flags=True, **settings):
        self.x_size, self.y_size = len(board[0]), len(board)
        super().__init__(self.x_size, self.y_size)
        # Copy contents of board into this grid
        for x, y in self.all_coords:
            contents = board[y][x]
            if ignore_flags and str(contents)[0] == 'F':
                self[y][x] = 'U'
            elif contents == 0:
                # Store open cells as a dash so that numbers reduced to zero can
                #  be distinguished.
                self[y][x] = '-'
            else:
                self[y][x] = contents
        self.orig_board = board #store the original board
        for attr in ['per_cell']:
            setattr(self, attr, settings[attr])
        self.clickable_coords = [(x, y) for (x, y) in self.all_coords
                                 if self[y][x] == 'U']
        self.found_mines = sum([int(c[1]) for row in self for c in row
                                if str(c)[0] in ['F', 'L']])
        # start_time = tm.time()
        self.numbers = find_numbers(self)
        self.groups = find_groups(self.numbers)
        for g in self.groups:
            # Get smallest neighbouring number
            min_nr = min([self.numbers[i]['val'] for i in g['nrs']])
            # Store upper bound on number of mines that can be in the group
            g['max'] = min(g['size'] * self.per_cell, min_nr)
        self.edge_coords = [c for g in self.groups for c in g['coords']]
        self.reduce_numbers()
        # self.check_for_overlap_groups()
        # print(f"Total initialise time: {tm.time()-start_time:.2f}")
        self.extract_reduced_lists()
    def __str__(self):
        for g in self.groups:
            if g['contains']:
                if g['max'] == 0:
                    char = '*'
                else:
                    char = '+'
                for x, y in g['coords']:
                    self[y][x] = char
            elif g['max'] == 0:
                for x, y in g['coords']:
                    self[y][x] = '~'
        return prettify_grid(self, {'U':'#'})
    def print_numbers(self, hint=None):
        if hint is None:
            numbers = [(i, n) for i, n in enumerate(self.numbers)]
        elif type(hint) is int:
            numbers = [(hint, self.numbers[hint])]
        elif type(hint) is dict:
            numbers = [(hint['index'], hint)]
        elif type(hint) is list:
            if type(hint[0]) is int:
                numbers = map(lambda i: (i, self.numbers[i]), hint)
            elif type(hint[0]) is dict:
                numbers = map(lambda n: (n['index'], n), hint)
        elif hint == 'nonzero':
            numbers = [(i, nr) for i, nr in enumerate(self.numbers) if nr['val']]
        else:
            return
        for i, nr in numbers:
            h = nr.copy()
            h.pop('index')
            print(i, h)
    def print_groups(self, hint=None):
        print_groups(self.groups, hint)
    def reduce_numbers(self):
        # Check for numbers which only have one neighbouring group and set the
        #  number of mines in that group to match the number. Doing this before
        #  reducing the numbers which have a superset of groups (like at an
        #  edge) is simply a time optimisation.
        self.check_for_numbers_with_one_group()
        # print(self)
        # Look for numbers for which the neighbouring groups are a subset of
        #  another number's neighbouring groups and remove the subset from the
        #  number which has the superset (also reducing the number).
        #[This should be done recursively to find every deduction]
        # Start with the numbers which have few neighbouring groups
        sorted_numbers = sorted(self.numbers, key=lambda n: len(n['grps']))
        for nr1 in sorted_numbers:
            for nr2 in sorted_numbers:
                if nr1 == nr2 or len(nr2['grps']) == 0:
                    continue
                if len(nr2['grps']) > len(nr1['grps']): #nr2 can't be a subset
                    break
                if not set(nr2['grps']) - set(nr1['grps']): #nr2 subset of nr1
                    # print('Subset number:')
                    # self.print_numbers([nr1, nr2])
                    # Subtract the value of nr2 from nr1
                    nr1['val'] -= nr2['val']
                    assert nr1['val'] >= 0
                    # Remove the nr2 subset of groups from nr1
                    for j in nr2['grps']:
                        self.groups[j]['nrs'].remove(nr1['index'])
                        nr1['grps'].remove(j)
                        if len(nr1['grps']) == 0:
                            assert nr1['val'] == 0
                            self.change_board_number_value(nr1)
                            # self.numbers.pop(nr1['index'])
                    # The groups of nr1 have been changed so it no longer has a
                    #  physical coordinate representation. The number on the
                    #  board is instead represented with a character.
                    nr1['repr'] = 'N'
                    self.change_board_number_value(nr1)
                    # Check if decreasing the number changes the max of nbr groups
                    for j in nr1['grps'].copy():
                        g_nbr = self.groups[j]
                        if nr1['val'] < g_nbr['max']:
                            # If nr['val']==0 this will remove consideration of g_nbr
                            self.decrease_group_max(j, g_nbr['max'] - nr1['val'])
                    # Check if the reduced numbers now only have one group
                    if len(nr1['grps']) == 1: #the superset minus the nr2 set
                        # print("Single group nr1:")
                        # self.print_numbers(nr1)
                        self.increase_group_min(nr1['grps'][0], nr1['val'])
                    if len(nr2['grps']) == 1: #the subset number
                        # print("Single group nr2:")
                        # self.print_numbers(nr2)
                        self.increase_group_min(nr2['grps'][0], nr2['val'])
    def change_board_number_value(self, nr):
        try:
            val = nr['repr']
        except KeyError:
            val = nr['val']
        x, y = nr['coord']
        self[y][x] = val
    def check_for_numbers_with_one_group(self):
        for nr in [n for n in self.numbers if len(n['grps']) == 1]:
            # If nr is only next to one group, fix that group by setting its min
            if len(nr['grps']) == 1: #check a group hasn't already been removed
                g = nr['grps'][0]
                # This will remove nr from self.numbers
                self.increase_group_min(g, nr['val'])
    def increase_group_min(self, g_num, inc):
        g = self.groups[g_num]
        g['contains'] += inc
        g_nrs = g['nrs'].copy()
        # For each number next to the group decrease its value
        for i in g['nrs']:
            nr = self.numbers[i]
            nr['val'] -= inc
            assert nr['val'] >= 0
            self.change_board_number_value(nr)
        # Check if decreasing the number changes the max of nbr groups
        for i in g_nrs:
            nr = self.numbers[i]
            for j in nr['grps'].copy():
                g_nbr = self.groups[j]
                if nr['val'] < g_nbr['max']:
                    # If nr['val']==0 this will remove consideration of g_nbr
                    self.decrease_group_max(j, g_nbr['max'] - nr['val'])
    def decrease_group_max(self, g_num, dec):
        """
        Decrease the max number of mines a (reduced) group can hold. If the
        max becomes zero the group is fixed, and so is removed from the list of
        groups for all surrounding numbers. When this is done a number may be
        left with only one group, which means that group can also be fixed.
        """
        g = self.groups[g_num]
        g['max'] -= dec
        assert g['max'] >= 0
        if g['max'] == 0:
            for i in g['nrs']:
                nr = self.numbers[i]
                # Remove the group from all neighbouring numbers' groups. If
                #  this is the last group nr is removed from
                #  self.numbers and should have nr['val']==0.
                nr['grps'].remove(g_num)
                if len(nr['grps']) == 1:
                    self.increase_group_min(nr['grps'][0], nr['val'])
                elif len(nr['grps']) == 0: #[Not sure about this]
                    assert nr['val'] == 0
                    self.change_board_number_value(nr)
                    # self.numbers.pop(i)
                    # print(i)
    def check_for_overlap_groups(self): #[Not working]
        while True:
            changed = False
            for nr in self.numbers:
                tot_grps_max = sum([self.groups[i]['max'] for i in nr['grps']])
                for g_num in nr['grps']:
                    g = self.groups[g_num]
                    g_min = g['max'] - tot_grps_max + nr['val']
                    if g_min > 0:
                        for g_nr in g['nrs']:
                            g_nr['val'] -= g_min
                            x, y = g_nr['coord']
                            self[y][x] = g_nr['val']
                            if g_nr['val'] < 0:
                                raise ValueError("Invalid board")
                        g['contains'] += g_min
                        g['max'] -= g_min
                        changed = True
            if not changed:
                break
            # Update the upper bound for the groups
            for i, g in enumerate(self.groups):
                min_nr = min([nr['val'] for nr in g['nrs']])
                g['max'] = min(g['max'], min_nr)
    def extract_reduced_lists(self):
        """Remove numbers which have value 0 and separate fixed groups out."""
        ## REMOVE NUMBERS WITH VALUE 0
        nr_index_map = {}
        i = 0
        while i < len(self.numbers):
            nr = self.numbers[i]
            if nr['val'] == 0:
                self.numbers.pop(i)
            else:
                nr_index_map[nr['index']] = i
                nr['index'] = i
                i += 1
        ## PUT FIXED GROUPS IN A SEPARATE LIST AND UPDATE NUMBER INDICES
        grp_index_map = {}
        self.fixed_groups = []
        j = 0
        while j < len(self.groups):
            g = self.groups[j]
            if g['max'] == 0:
                self.groups.pop(j)
                g.pop('index')
                g.pop('nrs')
                g.pop('max')
                self.fixed_groups.append(g)
            else:
                g['nrs'] = list(map(lambda i: nr_index_map[i], g['nrs']))
                grp_index_map[len(self.fixed_groups) + j] = j
                g['index'] = j
                j += 1
        ## UPDATE GROUP INDICES
        for nr in self.numbers:
            nr_grps = []
            for j in nr['grps']:
                # Only include a reference to the group if it isn't fixed
                if j in grp_index_map:
                    nr_grps.append(grp_index_map[j])
            nr['grps'] = nr_grps







if __name__ == '__main__':
    pass
