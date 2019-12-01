// Compile with:
// gcc -shared -Wl,-soname,c_utils -o c_utils.so find_configs.c

#include <stdio.h>
#include <stdlib.h>

#define min(x, y) ((x) < (y) ? x : y)
#define max(x, y) ((x) > (y) ? x : y)


typedef struct number {
    int index;
    int val;
    int grps[9]; /*absolute max number of groups is 8, plus terminating zero*/
} Number;

typedef struct group {
    int max;
    Number nrs[8]; //absolute max number of adjacent numbers is 8
    int nNrs;
} Group;

typedef struct results {
    int **data;
    int length;
} Results;


void print_configs(int** configs, int grps);
void free_configs(int** configs);
int** find_configs(Group* groups, int grps, int* nCfgs_ptr);
void test(void);


int main(){ //used to test find_configs
    // Number numbers[] = {
    //     0, 1, {0, 1}, //index, val, grps
    //     1, 1, {1, 2},
    //     2, 1, {2, 3},
    //     3, 1, {2, 3, 4},
    //     4, 1, {3, 4, 5}
    // };
    // Group groups[] = {
    //     1, {numbers[0]}, 1, //max, nrs, nNrs
    //     1, {numbers[0], numbers[1]}, 2,
    //     1, {numbers[1], numbers[2], numbers[3]}, 3,
    //     1, {numbers[2], numbers[3], numbers[4]}, 3,
    //     1, {numbers[3], numbers[4]}, 2,
    //     1, {numbers[4]}, 1
    // };
    // Number numbers[] = {
    //     0, 1, {0, 1}, //index, val, grps
    //     1, 1, {2, 3},
    //     2, 1, {1, 3, 4},
    //     3, 1, {3, 4, 5},
    //     4, 1, {4, 5, 6},
    //     5, 2, {5, 6, 7}
    // };
    // Group groups[] = {
    //     1, {numbers[0]}, 1, //max, nrs, nNrs
    //     1, {numbers[0], numbers[2]}, 2,
    //     1, {numbers[1]}, 1,
    //     1, {numbers[1], numbers[2], numbers[3]}, 3,
    //     1, {numbers[2], numbers[3], numbers[4]}, 3,
    //     1, {numbers[3], numbers[4], numbers[5]}, 3,
    //     1, {numbers[4], numbers[5]}, 2,
    //     2, {numbers[5]}, 1
    // };
    Number numbers[] = {
        0, 1, {0, 1, 2}, //index, val, grps
        1, 1, {1, 2, 3},
        2, 1, {2, 3, 4},
    };
    Group groups[] = {
        1, {numbers[0]}, 1, //max, nrs, nNrs
        1, {numbers[0], numbers[1]}, 2,
        1, {numbers[0], numbers[1], numbers[2]}, 3,
        1, {numbers[1], numbers[2]}, 2,
        1, {numbers[2]}, 1
    };
    int grps = 5, nCfgs = 0;
    int **cfgs = find_configs(groups, grps, &nCfgs);
    print_configs(cfgs, grps);
    free_configs(cfgs);

    return 0;
}


void print_number(Number nr){
    printf("Number %d with value %d and groups [%d", nr.index, nr.val, nr.grps[0]);
    int i;
    for (i = 1; nr.grps[i] > nr.grps[i-1]; i++)
        printf(", %d", nr.grps[i]);
    printf("]\n");
}


void print_group(Group grp, int g_num){
    printf("Group %d with max %d and numbers:\n", g_num, grp.max);
    int i = 0;
    while (i < grp.nNrs){
        printf("  ");
        print_number(grp.nrs[i++]);
    }
}


void print_configs(int** ptr, int nGroups){
    if (!*ptr){
        printf("No configs found\n");
        return;
    }
    int i, *cfg, nConfigs = 0;
    printf("Configs (C):\n");
    while (*ptr){
        if (nConfigs == 10){ //this many printed, stop there
            printf("  ...\n");
            break;
        }
        printf("  (");
        cfg = *ptr++; //get pointer to cfg and increment for next cfg
        for (i = 0; i < nGroups - 1; i++){
            printf("%d, ", *cfg++); //print cfg element
        }
        printf("%d)\n", *cfg); //print last element of cfg
        nConfigs++;
    }
    while (*ptr){
        ptr++;
        nConfigs++; //count how many configs
    }
    printf("Total of %d configs\n", nConfigs);
}


int* make_config(int size, int* contents, int copy_size){
    int *cfg = malloc(sizeof(int) * size);
    if (!cfg) { //catch malloc unable to find storage error
        printf("malloc failed");
        return NULL;
    }
    int *ptr = cfg;
    for (; copy_size; copy_size--)
        *ptr++ = *contents++;
    return cfg;
}


void free_configs(int** cfgs){
    // Free the memory allocated for the actual configs
    int **ptr = cfgs;
    while (*ptr){
        free(*ptr++);
    }
    // Free the memory allocated for the pointers to the configs
    free(cfgs);
}


int** find_configs(Group groups[], int nGroups, int* nCfgs_ptr){
    /* This function is made to be called from Python. It takes the equivalence
       groups with their neighbouring numbers and max number of mines and finds
       all possible configurations of mines. The configurations are first
       stored in a linked list defined here, and then returned as (a pointer to)
       an array of pointers (which point to int[nGroups] array). */
    // int count;
    // for (count = 0; count < nGroups; count++)
    //     print_group(groups[count], count);
    // Create the structure for a doubly linked list
    typedef struct node {
        int *data;
        struct node *next;
        struct node *prev;
    } Config_tree;
    // Initialise with a head node and an initial cfg
    Config_tree *new_cfg;
    new_cfg = malloc(sizeof(Config_tree));
    if (!new_cfg){
        printf("malloc failed!");
        return NULL;
    }
    Config_tree head = {NULL, new_cfg, NULL}; //not used to store data
    new_cfg->data = make_config(nGroups, NULL, 0); //cfg with no groups set
    new_cfg->next = NULL;
    new_cfg->prev = &head;
    // Find the configurations
    int i, j, k, g_index, g_min, g_max, nr_val, space, nConfigs = 1;
    Group g;
    Number nr;
    Config_tree *cfg, *next_cfg, *prev_cfg; //nodes
    for (i = 0; i < nGroups; i++){
        g = groups[i];
        // print_group(g, i);
        cfg = &head;
        while (cfg->next) {
            cfg = cfg->next;
            g_min = 0; g_max = g.max;
            for (j = 0; j < g.nNrs; j++){
                nr = g.nrs[j];
                // print_number(nr);
                nr_val = nr.val;
                space = 0;
                k = 0;
                do {
                    g_index = nr.grps[k];
                    if (g_index < i)
                        nr_val -= cfg->data[g_index];
                    else if (g_index > i)
                        space += groups[g_index].max;
                    k++;
                } while (nr.grps[k] > nr.grps[k-1]);
                g_max = min(g_max, nr_val);
                g_min = max(g_min, nr_val - space);
                // printf("%d %d %d %d\n", nr_val, space, g_min, g_max);
            }
            if (g_min > g_max) { //remove cfg
                // printf("Uh oh?\n");
                // return NULL;
                prev_cfg = cfg->prev;
                next_cfg = cfg->next;
                if (next_cfg) //if not the end of the linked list
                    next_cfg->prev = prev_cfg;
                prev_cfg->next = next_cfg;
                free(cfg);
                cfg = prev_cfg; //to be used in while loop
                nConfigs--;
                // printf("nConfigs=%d\n", nConfigs);
                continue;
            }
            cfg->data[i] = g_min; //fill in first possibility for this group
            for (j = g_min + 1; j <= g_max; j++){
                new_cfg = malloc(sizeof(Config_tree));
                if (!new_cfg) { //catch malloc unable to find storage error
                    printf("malloc failed");
                    return NULL;
                }
                new_cfg->data = make_config(nGroups, cfg->data, i);
                new_cfg->data[i] = j;
                new_cfg->next = head.next;
                new_cfg->next->prev = new_cfg;
                new_cfg->prev = &head;
                head.next = new_cfg;
                nConfigs++;
                // printf("nConfigs=%d\n", nConfigs);
            }
        }
    }
    *nCfgs_ptr = nConfigs;
    // Create array to contain pointers to the configs
    int **cfg_ptr_array = malloc(sizeof(int*) * (nConfigs+1));
    if (!cfg_ptr_array){
        printf("malloc failed");
        return NULL;
    }
    cfg = head.next; //used to iterate through linked list
    // Store pointers to configs and free memory containing Config_tree nodes
    for (i = 0; i < nConfigs; i++){
        *(cfg_ptr_array + i) = cfg->data;
        prev_cfg = cfg;
        cfg = cfg->next;
        free(prev_cfg);
    }
    *(cfg_ptr_array + nConfigs) = NULL; //terminate array of configs
    // if (nConfigs > 10){
    //     printf("Found %d configs (C)\n", nConfigs);
    // } else
    //     print_configs(cfg_ptr_array, nGroups);

    return cfg_ptr_array;
}
