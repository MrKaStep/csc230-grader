calc7: calc.o base7.o operation.o
	gcc calc.o base7.o operation.o -o calc7

calc20: calc.o base20.o operation.o
	gcc calc.o base20.o operation.o -o calc20

base20.o: base.c base.h
	gcc -Wall -std=c99 -DBASE=20 -c base.c -o base20.o
  
calc.o: calc.c 
	gcc -Wall -std=c99 -c calc.c
	
base7.o: base.c base.h
	gcc -Wall -std=c99 -c base.c -o base7.o
  
operation.o: operation.c operation.h
	gcc -Wall -std=c99 -c operation.c

clean:
	rm -f calc.o base7.o operation.o base20.o
	rm -f output.txt

all: calc7 calc20