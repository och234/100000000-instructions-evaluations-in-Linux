#!/bin/bash    
	
	cd SPEC2000/bzip #enter into the directory containing the bzip files

	'run the sim-outorder configuration for this benchmark'
./sim-outorder -config ../default.cfg -redir:sim assign.txt -fastfwd 100000000 -max:inst 100000000 bzip200.peak.ev6 input.source 58

echo >> bzip_ans.txt #adding space
echo >> bzip_ans.txt
echo 'L1 inst cache 8KB, n sets: 256'>> bzip_ans.txt #this is the default configuration so we save it on-top of this benchmark
echo >> bzip_ans.txt

sed -n 149p assign.txt >> bzip_ans.txt #this prints out the instruction per cycle for the bzip benchmark and stores it in bzip_ans.txt
sed -n 197p assign.txt >> bzip_ans.txt #this prints out the l1 instruction miss rate for the bzip benchmark and stores it in bzip_ans.txt
sed -n 207p assign.txt >> bzip_ans.txt #this prints out the l1 data miss rate for the bzip benchmark and stores it in bzip_ans.txt
sed -n 209p assign.txt >> bzip_ans.txt #this prints out the l1 data write back rate for the bzip benchmark and stores it in bzip_ans.txt
sed -n 217p assign.txt >> bzip_ans.txt #this prints out the l2 unified miss rate for the bzip benchmark and stores it in bzip_ans.txt
sed -n 219p assign.txt >> bzip_ans.txt #this prints out the l2 unified write back rate for the bzip benchmark and stores it in bzip_ans.txt
sed -n 145p assign.txt >> bzip_ans.txt #this prints out the load execution time for the bzip benchmark
sed -n 146p assign.txt >> bzip_ans.txt #this prints out the store execution time for the bzip benchmark
sed -n 148p assign.txt >> bzip_ans.txt #this prints out the sim cycle for the bzip benchmark and stores it in bzip_ans.txt


cd ../crafty #enter into the directory containing the crafty files and do the same as done for bzip

./sim-outorder -config ../default.cfg -redir:sim assign.txt -fastfwd 100000000 -max:inst 100000000 crafty00.peak.ev6 < crafty.in 

echo >> crafty_ans.txt
echo >> crafty_ans.txt
echo 'L1 inst cache 8KB, n sets: 256'>> crafty_ans.txt
echo >> crafty_ans.txt


sed -n 149p assign.txt >> crafty_ans.txt
sed -n 197p assign.txt >> crafty_ans.txt
sed -n 207p assign.txt >> crafty_ans.txt
sed -n 209p assign.txt >> crafty_ans.txt
sed -n 217p assign.txt >> crafty_ans.txt
sed -n 219p assign.txt >> crafty_ans.txt
sed -n 145p assign.txt >> crafty_ans.txt
sed -n 146p assign.txt >> crafty_ans.txt
sed -n 148p assign.txt >> crafty_ans.txt


cd ../eon #enter into the directory containing the eon files and do the same as done for bzip


./sim-outorder -config ../default.cfg -redir:sim assign.txt -fastfwd 100000000 -max:inst 100000000 eon00.peak.ev6 chair.control.cook chair.camera chair.surfaces chair.cook.ppm ppm pixels_out.cook 

echo >> eon_ans.txt
echo >> eon_ans.txt
echo 'L1 inst cache 8KB, n sets: 256'>> eon_ans.txt
echo >> eon_ans.txt

sed -n 164p assign.txt >> eon_ans.txt
sed -n 160p assign.txt >> eon_ans.txt
sed -n 161p assign.txt >> eon_ans.txt
sed -n 212p assign.txt >> eon_ans.txt
sed -n 222p assign.txt >> eon_ans.txt
sed -n 224p assign.txt >> eon_ans.txt
sed -n 232p assign.txt >> eon_ans.txt
sed -n 234p assign.txt >> eon_ans.txt
sed -n 163p assign.txt >> eon_ans.txt


cd ../equake #enter into the directory containing the equake files and do the same as done for bzip

./sim-outorder -config ../default.cfg -redir:sim assign.txt -fastfwd 100000000 -max:inst 100000000 equake00.peak.ev6 < inp.in > inp.out 2> inp.err

echo >> equake_ans.txt
echo >> equake_ans.txt
echo 'L1 inst cache 8KB, n sets: 256'>> equake_ans.txt
echo >> equake_ans.txt

sed -n 150p assign.txt >> equake_ans.txt
sed -n 146p assign.txt >> equake_ans.txt
sed -n 147p assign.txt >> equake_ans.txt
sed -n 198p assign.txt >> equake_ans.txt
sed -n 208p assign.txt >> equake_ans.txt
sed -n 210p assign.txt >> equake_ans.txt
sed -n 218p assign.txt >> equake_ans.txt
sed -n 220p assign.txt >> equake_ans.txt
sed -n 149p assign.txt >> equake_ans.txt

cd ../galgel #enter into the directory containing the galgel files and do the same as done for bzip

./sim-outorder -config ../default.cfg -redir:sim assign.txt -fastfwd 100000000 -max:inst 100000000 galgel00.peak.ev6 < galgel.in

echo >> galgel_ans.txt
echo >> galgel_ans.txt
echo 'L1 inst cache 8KB, n sets: 256'>> galgel_ans.txt
echo >> galgel_ans.txt

sed -n 152p assign.txt >> galgel_ans.txt
sed -n 148p assign.txt >> galgel_ans.txt
sed -n 149p assign.txt >> galgel_ans.txt
sed -n 200p assign.txt >> galgel_ans.txt
sed -n 210p assign.txt >> galgel_ans.txt
sed -n 212p assign.txt >> galgel_ans.txt
sed -n 220p assign.txt >> galgel_ans.txt
sed -n 222p assign.txt >> galgel_ans.txt
sed -n 151p assign.txt >> galgel_ans.txt


cd ../gcc #enter into the directory containing the gcc files and do the same as done for bzip

./sim-outorder -config ../default.cfg -redir:sim assign.txt -fastfwd 100000000 -max:inst 100000000 gcc00.peak.ev6 166.i -o 166.s

echo >> gcc_ans.txt
echo >> gcc_ans.txt
echo 'L1 inst cache 8KB, n sets: 256'>> gcc_ans.txt
echo >> gcc_ans.txt

sed -n 150p assign.txt >> gcc_ans.txt
sed -n 146p assign.txt >> gcc_ans.txt
sed -n 147p assign.txt >> gcc_ans.txt
sed -n 198p assign.txt >> gcc_ans.txt
sed -n 208p assign.txt >> gcc_ans.txt
sed -n 210p assign.txt >> gcc_ans.txt
sed -n 218p assign.txt >> gcc_ans.txt
sed -n 220p assign.txt >> gcc_ans.txt
sed -n 149p assign.txt >> gcc_ans.txt

cd ../mcf #enter into the directory containing the mcf files and do the same as done for bzip

./sim-outorder -config ../default.cfg -redir:sim assign.txt -fastfwd 100000000 -max:inst 100000000 mcf00.peak.ev6 inp.in.mcf

echo >> mcf_ans.txt
echo >> mcf_ans.txt
echo 'L1 inst cache 8KB, n sets: 256'>> mcf_ans.txt
echo >> mcf_ans.txt

sed -n 149p assign.txt >> mcf_ans.txt
sed -n 197p assign.txt >> mcf_ans.txt
sed -n 207p assign.txt >> mcf_ans.txt
sed -n 209p assign.txt >> mcf_ans.txt
sed -n 217p assign.txt >> mcf_ans.txt
sed -n 219p assign.txt >> mcf_ans.txt
sed -n 145p assign.txt >> mcf_ans.txt
sed -n 146p assign.txt >> mcf_ans.txt
sed -n 148p assign.txt >> mcf_ans.txt


cd ../mesa #enter into the directory containing the mesa files and do the same as done for bzip

./sim-outorder -config ../default.cfg -redir:sim assign.txt -fastfwd 100000000 -max:inst 100000000 mesa00.peak.ev6 -frames 1000 -meshfile mesa.in -ppmfile mesa.ppm

echo >> mesa_ans.txt
echo >> mesa_ans.txt
echo 'L1 inst cache 8KB, n sets: 256'>> mesa_ans.txt
echo >> mesa_ans.txt

sed -n 149p assign.txt >> mesa_ans.txt
sed -n 197p assign.txt >> mesa_ans.txt
sed -n 207p assign.txt >> mesa_ans.txt
sed -n 209p assign.txt >> mesa_ans.txt
sed -n 217p assign.txt >> mesa_ans.txt
sed -n 219p assign.txt >> mesa_ans.txt
sed -n 145p assign.txt >> mesa_ans.txt
sed -n 146p assign.txt >> mesa_ans.txt
sed -n 148p assign.txt >> mesa_ans.txt

cd ../swim #enter into the directory containing the swim files and do the same as done for bzip

./sim-outorder -config ../default.cfg -redir:sim assign.txt -fastfwd 100000000 -max:inst 100000000 swim00.peak.ev6  < swim.in

echo >> swim_ans.txt
echo >> swim_ans.txt
echo 'L1 inst cache 8KB, n sets: 256'>> swim_ans.txt
echo >> swim_ans.txt

sed -n 152p assign.txt >> swim_ans.txt
sed -n 148p assign.txt >> swim_ans.txt
sed -n 149p assign.txt >> swim_ans.txt
sed -n 200p assign.txt >> swim_ans.txt
sed -n 210p assign.txt >> swim_ans.txt
sed -n 212p assign.txt >> swim_ans.txt
sed -n 220p assign.txt >> swim_ans.txt
sed -n 222p assign.txt >> swim_ans.txt
sed -n 151p assign.txt >> swim_ans.txt

cd ../wupwise #enter into the directory containing the wupwise files and do the same as done for bzip

./sim-outorder -config ../default.cfg -redir:sim assign.txt -fastfwd 100000000 -max:inst 100000000 wupwise00.peak.ev6 < wupwise.in

echo >> wupwise_ans.txt
echo >> wupwise_ans.txt
echo 'L1 inst cache 8KB, n sets: 256'>> wupwise_ans.txt
echo >> wupwise_ans.txt

sed -n 152p assign.txt >> wupwise_ans.txt
sed -n 148p assign.txt >> wupwise_ans.txt
sed -n 149p assign.txt >> wupwise_ans.txt
sed -n 200p assign.txt >> wupwise_ans.txt
sed -n 210p assign.txt >> wupwise_ans.txt
sed -n 212p assign.txt >> wupwise_ans.txt
sed -n 220p assign.txt >> wupwise_ans.txt
sed -n 222p assign.txt >> wupwise_ans.txt
sed -n 151p assign.txt >> wupwise_ans.txt