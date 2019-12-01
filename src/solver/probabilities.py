

import time as tm
from os.path import dirname, join
from math import log, exp, factorial as fac
from ctypes import cdll, byref, Structure, c_int, POINTER

from ..minefield import Grid
from ..utils import prettify_grid, get_nbrs
from .deducer import SolverReducedBoard
from .gen_probs import get_unsafe_prob, get_combs


def find_configs(numbers, groups):
    """
    Use the find_configs function written in C to find all possible mine
    configurations in the groups.
    """
    if not groups:
        return []
    NineIntArray = c_int * 9
    class C_Number(Structure):
        _fields_ = [
            ("index", c_int),
            ("val", c_int),
            ("grps", NineIntArray)
            ]
    NumberArray = C_Number * 8
    class C_Group(Structure):
        _fields_ = [
            ('max', c_int),
            ('nrs', NumberArray),
            ('nNrs', c_int)
            ]
    lib = cdll.LoadLibrary(join(dirname(__file__), 'c_utils.so'))
    lib.find_configs.restype = POINTER(POINTER(c_int))
    num_of_cfgs = c_int() #initialise to pass with byref
    # print("groups:", [g['index'] for g in grps])
    GroupsArray = C_Group * len(groups)
    grp_index_map = {g['index']: i for i, g in enumerate(groups)}
    all_nrs = {numbers[i]['index'] for g in groups for i in g['nrs']}
    c_nrs = dict()
    for i, nr_index in enumerate(sorted(all_nrs)):
        nr = numbers[nr_index]
        # Map the group indices to correspond to post reduction
        nr_grps = [grp_index_map[j] for j in nr['grps']]
        # print(nr, nr_grps)
        c_nrs[nr_index] = C_Number(i,                     #index
                                   nr['val'],             #val
                                   NineIntArray(*nr_grps) #group indices
                                   )
    c_grps = []
    for g in groups:
        c_nrs_array = [c_nrs[numbers[i]['index']] for i in g['nrs']]
        c_nrs_array = NumberArray(*c_nrs_array) #convert to C array
        c_grps.append(C_Group(g['max'],     #max
                              c_nrs_array,  #nr structs array
                              len(g['nrs']) #len of c_nrs
                              ))
    c_grps = GroupsArray(*c_grps)
    ptr = lib.find_configs(byref(c_grps), len(groups), byref(num_of_cfgs))
    # lib.print_configs(ptr, len(groups))
    configs = []
    for i in range(num_of_cfgs.value):
        cfg_ptr = ptr[i]
        cfg = tuple(cfg_ptr[j] for j in range(len(groups)))
        configs.append(cfg) #the indices match up with the groups
    lib.free_configs(ptr) #free malloc'ed memory
    configs.sort() #unnecessary but cleaner
    return configs

class ProbsGrid(Grid):
    def __init__(self, board, ignore_flags=True, **settings):
        self.x_size, self.y_size = len(board[0]), len(board)
        super().__init__(self.x_size, self.y_size)
        self.board = board
        # Reduce the board with logical deductions
        t = tm.time()
        self.reduced_board = SolverReducedBoard(board, ignore_flags, **settings)
        print(f"Time to reduce board (python): {tm.time()-t:.2f} secs")
        for attr in ['mines', 'per_cell']:
            setattr(self, attr, settings[attr])
        self.numbers = self.reduced_board.numbers
        self.groups = self.reduced_board.groups
        self.fixed_groups = self.reduced_board.fixed_groups
        # Split groups into islands to speed up finding configs
        self.split_up_groups()
        # Find configs
        t = tm.time()
        self.find_split_configs()
        print(f"Time to find configs (C): {tm.time()-t:.2f} secs")
        t = tm.time()
        # Add the minimum number of mines already determined for the groups
        self.include_fixed_groups()
        # self.expand_configs()
        print(f"Time to expand configs (python): {tm.time()-t:.2f} secs")
        # Find the probabilities
        t = tm.time()
        self.find_probs()
        print(f"Time to find probs (python): {tm.time()-t:.2f} secs")
    def __str__(self):
        print_grid = []
        for row in self:
            print_grid.append(list(map(lambda p: round(100*p, 1), row)))
        return prettify_grid(print_grid, {0:' 0  ', 100:'100 '}, cell_size=4)
    def split_up_groups(self):
        # grp_nums = [g['index'] for g in self.groups if g['max']]
        grp_nums = list(range(len(self.groups)))
        self.split_groups = []
        while grp_nums:
            i = grp_nums.pop(0)
            grp = self.groups[i]
            island_grps = [grp]
            nrs = grp['nrs'][:]
            while nrs:
                nr = self.numbers[nrs.pop(0)]
                for j in nr['grps']:
                    if j in grp_nums:
                        grp2 = self.groups[j]
                        grp_nums.remove(j)
                        island_grps.append(grp2)
                        nrs.extend(grp2['nrs'])
            island_grps.sort(key=lambda g: g['index'])
            self.split_groups.append(island_grps)
        # print("split groups:")
        # for grps in self.split_groups:
        #     self.board.print_groups(grps)
        #     print("-----------")
    def find_split_configs(self):
        self.split_configs = []
        for groups in self.split_groups:
            # print("groups:", [g['index'] for g in grps])
            self.split_configs.append(find_configs(self.numbers, groups))
        # print("split configs:")
        # for c in self.split_configs:
        #     print(" ", c)
    def include_fixed_groups(self):
        for i, island_cfgs in enumerate(self.split_configs):
            island_grps = self.split_groups[i]
            contains_grps = [(j, g['contains']) for j, g in enumerate(island_grps)
                             if g['contains']]
            for cfg in island_cfgs:
                for j, m in contains_grps:
                    cfg[j] += m
        fixed_grps = [g for g in self.fixed_groups if g['contains']]
        self.split_groups.append(fixed_grps)
        self.split_configs.append([tuple(g['contains'] for g in fixed_grps)])
    def expand_configs(self):
        # Add g['contains'] to each config in split_configs
        #[Takes up to ~0.5 seconds, easily improved]
        for i, island_cfgs in enumerate(self.split_configs):
            island_grps = self.split_groups[i]
            contains_grps = [(j, g['contains']) for j, g in enumerate(island_grps)
                             if g['contains'] and g['max']]
            for cfg in island_cfgs:
                for j, m in contains_grps:
                    cfg[j] += m
        fixed_grps = [g for g in self.groups if not g['max'] and g['contains']]
        self.groups = fixed_grps
        self.configs = [[g['contains'] for g in self.groups]]
        #[This can take up to ~0.3 seconds, presumed better in C]
        for i, grps in enumerate(self.split_groups):
            self.groups.extend(grps)
            island_cfgs = self.split_configs[i]
            j = len(self.configs) - 1
            while j >= 0:
                cfg = self.configs[j]
                for cfg_part in island_cfgs[:-1]:
                    cfg_base = cfg[:]
                    cfg_base.extend(cfg_part)
                    self.configs.append(cfg_base)
                cfg.extend(island_cfgs[-1]) #re-use cfg
                j -= 1
        self.configs = sorted(map(tuple, self.configs))
    def OLDfind_configs(self):
        """
        Deprecated - useful for checking C function is running correctly.
        Uses the equivalence groups of the board to generate all possible mine
        configurations, which are stored in self.configs, a sorted list of
        tuples with each position representing a group (self.groups is a
        list with order corresponding to the order in the tuples)."""
        t1 = t2 = t3 = 0
        ttotalstart = tm.time()
        # Initialise the list of configurations for the number of mines in each
        #  group, with the index within each configuration corresponding to the
        #  group index in self.groups. Each list in cfgs will be filled in
        #  from left to right.
        cfgs = [[]]
        # Loop through the groups/along the configurations
        # for g_num in sorted(self.var_groups):
        for g_num, g in enumerate(self.groups):
            # g = self.groups[g_num]
            if g['max'] == 0:
                for cfg in cfgs:
                    cfg.append(0)
                continue
            # Move configs into temporary list to loop through, reset cfgs
            subcfgs = cfgs #configurations filled in up to index i
            cfgs = []
            # For each configuration branch off with new configurations
            #  after filling a number of mines for the next group
            for cfg in subcfgs:
                g_min = 0
                g_max = g['max'] #obtained by taking min of neighbouring nrs
                t1start = tm.time()
                # Loop through the numbers next to the current group to
                #  determine bounds on how many mines the group could contain
                for nr in g['nrs']:
                    # The effective value of the number 'nr' after mines have
                    #  been placed as in the current cfg
                    nr_val = nr['val']
                    # The amount of space potentially available in other groups
                    #  around nr
                    space = 0
                    for grp_index in nr['grps']:
                        if grp_index < g_num:
                            nr_val -= cfg[grp_index]
                        elif grp_index > g_num:
                            space += self.groups[grp_index]['max']
                    g_max = min(g_max, nr_val)
                    g_min = max(g_min, nr_val - space)
                t1 += tm.time() - t1start
                t2start = tm.time()
                for j in range(g_min, g_max + 1):
                    if j < g_max:
                        new_cfg = cfg[:]
                    else:
                        new_cfg = cfg #don't copy for last one
                    new_cfg.append(j)
                    cfgs.append(new_cfg)
                t2 += tm.time() - t2start
        t3start = tm.time()
        self.raw_configs = []
        for cfg in cfgs:
            raw_cfg = tuple([i for g_num, i in enumerate(cfg)
                             if self.groups[g_num]['max'] > 0])
            self.raw_configs.append(raw_cfg)
        self.raw_configs.sort()
        # for i, num in [(j, g['contains']) for j, g in enumerate(self.groups)
        #                if g['contains'] > 0]:
        #     for c in cfgs:
        #         c[i] += num
        # self.configs = sorted(map(tuple, cfgs))
        t3 += tm.time() - t3start
        ttotal = tm.time() - ttotalstart
        # print(f"{t1:.2f}, {t2:.2f}, {t3:.2f}, total: {ttotal:.2f}")
    def find_probs(self):
        # Number of remaining clickable cells
        unclicked_cells = len(self.reduced_board.clickable_coords)
        # Number of remaining mines (subtract found mines)
        mines = self.mines - self.reduced_board.found_mines
        # Number of cells which are next to a revealed number
        edge_cells = len(self.reduced_board.edge_coords)
        outer_cells = unclicked_cells - edge_cells
        xmax = self.per_cell
        ## DEFINE ZETA FUNCTION
        def zeta(cfg, groups):
            res = 1
            for i, g in enumerate(groups):
                res *= get_combs(cfg[i], g['size'], xmax) / fac(cfg[i])
            return res #may not be an integer
        ## SET UP ISLANDS WITH THEIR DATA
        self.all_islands = []
        nConfigs = 1
        for l, island_cfgs in enumerate(self.split_configs):
            num = len(island_cfgs)
            nConfigs *= num
            island = {'configs':      island_cfgs,
                      'nConfigs':     num,
                      'zetas':        num * [0],
                      'config_probs': num * [0],
                      'groups':       self.split_groups[l]
                      }
            for k, cfg in enumerate(island_cfgs):
                z = zeta(cfg, island['groups'])
                # print(cfg, z)
                island['zetas'][k] = z
            # for item in island.items():
            #     if item[0] == 'groups':
            #         grps = [g['coords'] for g in item[1]]
            #         print(('groups', grps))
            #     else:
            #         print(item)
            self.all_islands.append(island)
        ## FIND PROBABILITIES FOR FULL CONFIGURATIONS
        # Probabilities associated with each full configuration
        cfg_probs = nConfigs * [0]
        positions = len(self.all_islands) * [0]
        j = 0
        while True:
            prob = 1
            M = 0
            for l, island in enumerate(self.all_islands):
                pos = positions[l]
                prob *= island['zetas'][pos]
                cfg = island['configs'][pos]
                M += sum(cfg)
            if M <= mines and mines - M <= xmax * outer_cells:
                eta = get_combs(mines - M, outer_cells, xmax) / fac(mines - M)
                prob *= eta
            else:
                # print(M, mines)
                prob = 0
            cfg_probs[j] = prob
            j += 1
            for i, pos in enumerate(positions):
                if pos == self.all_islands[i]['nConfigs'] - 1:
                    positions[i] = 0
                else:
                    positions[i] += 1
                    break
            if positions == len(self.all_islands) * [0]:
                break
        # print(island)
        # print(cfg_probs)
        total = sum(cfg_probs)
        assert total > 0, "Invalid board (not enough space for mines)"
        for j in range(nConfigs):
            cfg_probs[j] /= total
        ## SPLIT PROBABILITIES INTO ISLANDS
        # Reset position counters
        for i in range(len(positions)):
        	positions[i] = 0
        j = 0
        while True:
            prob = cfg_probs[j]
            for l, island in enumerate(self.all_islands):
                pos = positions[l]
                island['config_probs'][pos] += prob
            j += 1
            for i, pos in enumerate(positions):
                if pos == self.all_islands[i]['nConfigs'] - 1:
                    positions[i] = 0
                else:
                    positions[i] += 1
                    break
            if positions == len(self.all_islands) * [0]:
                break
        ## FIND PROBABILITIES FOR INDIVIDUAL CELLS
        inner_expected = 0
        for island in self.all_islands:
            for i, grp in enumerate(island['groups']): #loop through the groups
                grp['cell_unsafe_prob'] = 0
                grp['probs'] = [0] * (xmax * grp['size'] + 1)
                for k, cfg in enumerate(island['configs']):
                    m = cfg[i]
                    cfg_prob = island['config_probs'][k]
                    grp['probs'][m] += cfg_prob
                    unsafe_prob = get_unsafe_prob(m, grp['size'], xmax)
                    grp['cell_unsafe_prob'] += unsafe_prob * cfg_prob
                assert grp['cell_unsafe_prob'] < 1.00001
                for x, y in grp['coords']:
                    # Round to remove error and allow checking for round probs
                    self[y][x] = round(grp['cell_unsafe_prob'], 5)
                grp['expected_mines'] = 0
                for num, p in enumerate(grp['probs']):
                    grp['expected_mines'] += num * p
                inner_expected += grp['expected_mines']
        ## DEAL WITH OUTER GROUP OF CELLS
        if outer_cells > 0:
            outer_mines = mines - int(inner_expected)
            outer_prob = get_unsafe_prob(outer_mines, outer_cells, xmax)
        outer_coords = (set(self.reduced_board.clickable_coords)
                        - set(self.reduced_board.edge_coords))
        for x, y in outer_coords:
            self[y][x] = outer_prob
    def OLDfind_probs(self):
        # Number of remaining clickable cells
        n = len(self.board.clickable_coords)
        # Number of remaining mines (subtract found mines)
        k = self.mines - self.board.found_mines
        # Number of cells which are next to a revealed number
        S = len(self.board.edge_coords)
        # Probabilities associated with each configuration in self.configs
        cfg_probs = []
        for cfg in self.configs:
            # print(cfg)
            M = sum(cfg) #total mines in cfg
            if (M > k                                #too many mines
                or k - M > self.per_cell * (n - S)): #not enough outer space
                cfg_probs.append(0)
                continue
            # Initialise the number of combinations
            combs = fac(k) / fac(k - M)
            # combs = 1 / fac(k - M)
            # This is the product term in xi(cfg)
            for i, m_i in enumerate(cfg):
                g_size = len(self.groups[i]['coords'])
                combs *= get_combs(g_size, m_i, self.per_cell)
                combs /= fac(m_i)
            cfg_probs.append(combs * get_combs(n - S, k - M, self.per_cell))
            # print(n, k, S, M, combs)
        # print(cfg_probs)
        assert sum(cfg_probs) > 0, "Invalid board (not enough space for mines)"
        weight = log(sum(cfg_probs))
        for i, p in enumerate(cfg_probs):
            if p == 0:
                # print("Zero probability for cfg:")
                # print(self.configs[i])
                continue
            cfg_probs[i] = exp(log(p) - weight)
        # print(self.configs)
        # print(cfg_probs)
        expected = 0
        for i, g in enumerate(self.groups):
            g_size = len(g['coords'])
            probs = [] #index to correspond to the number of mines in the group
            unsafe_prob = 0 #prob of a cell in the group having at least 1 mine
            # Loop through the numbers of mines that can be held by the group
            for j in range(g_size * self.per_cell + 1):
                p = sum([cfg_probs[k] for k, c in enumerate(self.configs)
                         if c[i]==j])
                probs.append(p)
                # print(p, get_unsafe_prob(g_size, j, self.per_cell))
                unsafe_prob += p * get_unsafe_prob(g_size, j, self.per_cell)
                if unsafe_prob > 1.0001:
                    print("Invalid configuration")
                    print(self.configs)
                    print(cfg_probs)
                    print(probs)
                    return
            # Probability of the group containing 0, 1, 2,... mines, where the
            #  number corresponds to the index
            g['probs'] = tuple(probs)
            g['exp'] = 0
            for n, p in enumerate(g['probs']):
                g['exp'] += n * p
            expected += g['exp']
            for x, y in g['coords']:
                # Round to remove error and allow checking for round probs
                self[y][x] = round(unsafe_prob, 5)
        rem_coords = set(self.board.clickable_coords) - set(self.board.edge_coords)
        if len(rem_coords) > 0:
            outer_mines = self.mines - int(expected)
            outer_prob = get_unsafe_prob(len(rem_coords), outer_mines,
                                         self.per_cell)
        for x, y in rem_coords:
            self[y][x] = outer_prob



if __name__ == '__main__':
    # print("")
    from . import test_boards
    def test(num, mines, per_cell):
        # print(prettify_grid(test_boards[num], {0:'-', 'U':'#'}))
        p = ProbsGrid(test_boards[num], ignore_flags=True, mines=mines,
                          per_cell=per_cell)
        # print(p.board)
        # p.board.print_numbers()
        # if len(p.configs) > 6:
        #     # print("Number of configs (python):", len(p.raw_configs))
        #     island_cfgs = [len(cfgs) for cfgs in p.split_configs]
        #     # tot = 1
        #     # for n in island_cfgs:
        #     #     tot *= n
        #     print("Number of configs (C):", island_cfgs, len(p.configs))
        # else:
        #     # print("Configs (python):")
        #     # for c in p.raw_configs:
        #     #     print(f"  {c}")
        #     print("Configs (C):")
        #     for c in p.configs:
        #         print(f"  {c}")
        return p
    config_results = {
        0: [()],
        1: [(0, 1, 0, 1, 0, 0), (1, 0, 1, 0, 0, 1)],
        2: [(0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0), (0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1), (0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1), (0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0), (0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1), (0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1), (0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0), (0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1), (0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0), (0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1), (0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0), (0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1), (0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0), (0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1), (0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1), (0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0), (0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1), (1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0), (1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1), (1, 0, 0, 0 , 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0), (1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1), (1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0), (1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1)]
        }

    # p = test(2, 30, 3)
    b = [['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
         ['U', 1, 2, 'U', 'U', 1, 1, 'U', 'U', 'U'],
         ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
         ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
         ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
         ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
         ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
         ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
         ]
    # p = ProbsGrid(b, mines=10, per_cell=3)
