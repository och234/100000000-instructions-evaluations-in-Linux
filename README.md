# 100000000-instructions-evaluations-in-Linux

The batch script should be run in the file with SPEC2000 and SPEC2000 folders should not be tempered with to make sure it can be iterated through smoothly by the batch script.
The cache is in it's default stage and can be changed from the default folder in SPEC20000.

This project made used of a 2 level cache - L1: split cache and L2: unified cache. I evaluated the impact of changing the cache configuration, such as L1 and L2 Cache size, Associativity, Block Size and Latency hit time. This was done using a SimpleScalar “sim-outorder” model and the SPEC 2000 benchmark suite. The result was compared using: Number of instructions per cycle (IPC),  L1 data cache miss rate L1 instruction cache miss rate L2 unified cache miss rate  The number of load instructions executed Total Simulation time

I ran each SPEC2000 benchmark for 100 million instructions after skipping 100 million instructions. Skipping a large number of instructions is quite important to warm up the cache, and running a relatively large number of instructions is important to get more accurate results.

In order to accelerate the process of running the 10 SPEC2000 benchmarks. I worte a bash script which was able to iterate through all the benchmarks and produce a text document of the outputs needed for execution from each benchmark and configuration. 

Simple scalar and the Benchmarks can be gotten from:
http://simplescalar.com/ by Todd M. Austin, Ph.D.
