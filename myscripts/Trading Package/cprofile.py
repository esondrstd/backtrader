import cProfile

with cProfile.Profile() as pr:
    my_func()  

pr.dump_stats('/path/to/filename.prof')
