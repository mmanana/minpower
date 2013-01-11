"""
Do an many economic dispatches over a range of load values to get an
'aggregate' cost curve for a system. 
"""


from minpower.config import user_config
from minpower.get_data import parsedir
from minpower.commonscripts import joindir
from minpower.tests.test_utils import make_loads_times, solve_problem
from pandas import DataFrame
import numpy as np
import matplotlib.pyplot as plt
import argparse

def main(args):
    generators, loads, _, times, _, data = parsedir()
    generators = filter(lambda gen: gen.is_controllable, generators)
    
    if args['min'] == 0:
        args['min'] = 1.1 * sum(gen.pmin for gen in generators)
    if args['max'] == 0:
        args['max'] = 0.99 * sum(gen.pmax for gen in generators)
    
    load_values = np.arange(args['min'], args['max'], args['interval'])
    results = DataFrame(columns=['prices', 'committed'], index=load_values)
    for load_val in load_values:
        print load_val
        loads_times = make_loads_times(Pd=load_val)
        power_system, times = solve_problem(generators, 
            do_reset_config=False, **loads_times)
        t = times[0]
        results.ix[load_val, 'prices'] = power_system.buses[0].price(t)
        results.ix[load_val, 'committed'] = sum(map(
            lambda gen: gen.power(t).value > gen.pmin,
            power_system.generators()))
        
    results.to_csv(joindir(user_config.directory, 'ed_sweep.csv'))

    ax = results.plot(secondary_y=['committed'])
    ax.set_xlabel('System Load (MW)')
    ax.set_ylabel('Estimated System Price ($/MWh)')
    ax.right_ax.set_ylabel('Units committed')

    plt.savefig(joindir(user_config.directory, 'ed_sweep.png'))    
    
def get_args():
    parser = argparse.ArgumentParser(
        description="""
        Do an many economic dispatches over a range of load values to get an
        'aggregate' cost curve for a system. """)
    parser.add_argument('directory', type=str,
        help='the direcory of the problem you want to solve')
    parser.add_argument('--min', type=int,
        default=0,
        help='the load value to start at')
    parser.add_argument('--max', type=int,
        default=0,
        help='the load value to end at')
    parser.add_argument('--interval', type=float,
        default=100,
        help='the interval to increment the load by')
    args = parser.parse_args()

    user_config.directory = args.directory
    user_config.duals = True
    user_config.perfect_solve = True
    
    return vars(args)

if __name__ == '__main__':
    args = get_args()
    main(args)