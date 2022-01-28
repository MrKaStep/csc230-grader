#!/bin/bash
FAIL=0

# Function to run a single test of the calc7 program.
testCalc7() {
  TESTNO=$1
  ESTATUS=$2

  rm -f output.txt
  
  echo "Test $TESTNO: ./calc7 < input-$TESTNO.txt > output.txt"
  ./calc7 < input-$TESTNO.txt > output.txt
  STATUS=$?

  # Make sure the program exited with the right exit status.
  if [ $STATUS -ne $ESTATUS ]; then
      echo "**** FAILED - Expected an exit status of $ESTATUS, but got: $STATUS"
      FAIL=1
      return 1
  fi

  # Make sure output matches expected output.
  if ! diff -q expected-$TESTNO.txt output.txt >/dev/null 2>&1 ; then
      echo "**** FAILED - output didn't match expected output."
      FAIL=1
      return 1
  fi

  echo "PASS"
  return 0
}

# Function to run a single test of the calc20 program.
testCalc20() {
  TESTNO=$1
  ESTATUS=$2

  rm -f output.txt
  
  echo "Test $TESTNO: ./calc20 < input-$TESTNO.txt > output.txt"
  ./calc20 < input-$TESTNO.txt > output.txt
  STATUS=$?

  # Make sure the program exited with the right exit status.
  if [ $STATUS -ne $ESTATUS ]; then
      echo "**** FAILED - Expected an exit status of $ESTATUS, but got: $STATUS"
      FAIL=1
      return 1
  fi

  # Make sure output matches expected output.
  if ! diff -q expected-$TESTNO.txt output.txt >/dev/null 2>&1 ; then
      echo "**** FAILED - output didn't match expected output."
      FAIL=1
      return 1
  fi

  echo "PASS"
  return 0
}

# Try to get a fresh compile of the project.
make clean

make calc7
if [ $? -ne 0 ]; then
    echo "**** Make didn't run succesfully when trying to build your calc7 program."
    FAIL=1
fi

# Run tests for calc7
if [ -x calc7 ] ; then
    testCalc7 01 0
    testCalc7 02 0
    testCalc7 03 0
    testCalc7 04 0
    testCalc7 05 0
    testCalc7 06 0
    testCalc7 07 0
    testCalc7 08 0
    testCalc7 09 0
    testCalc7 10 0
    testCalc7 11 102
    testCalc7 12 102
    testCalc7 13 100
    testCalc7 14 100
    testCalc7 15 101
else
    echo "**** Your calc7 program couldn't be tested since it didn't compile successfully."
    FAIL=1

fi

make calc20
if [ $? -ne 0 ]; then
    echo "**** Make didn't run succesfully when trying to build your calc20 program."
    FAIL=1
fi

# Run tests for calc7
if [ -x calc20 ] ; then
    testCalc20 16 0
    testCalc20 17 0
    testCalc20 18 0
    testCalc20 19 100
    testCalc20 20 102
    testCalc20 21 100
else
    echo "**** Your calc20 program couldn't be tested since it didn't compile successfully."
    FAIL=1

fi

if [ $FAIL -ne 0 ]; then
  echo "**** There were failing tests"
  exit 1
else 
  echo "Tests successful"
  exit 0
fi
