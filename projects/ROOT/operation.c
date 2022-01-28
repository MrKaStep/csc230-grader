/**
   @file operation.c
   @author John Doe (jdoe)
   
   Performs one of the four basic arithmetic operations and
   detects overflow or divide-by-zero errors.
*/

#include <stdlib.h>
#include <limits.h>
#include "operation.h"

/** 
   Adds two values while checking for overflow
   @param a first value being added
   @param b second value being added
   @return result sum of a and b
*/
long plus( long a, long b )
{
   
	long result = a + b;
	
	// Both a and b are positive and sum is negative
	if( a > 0 && b > 0 && result < 0) {
		exit( OVERFLOW );
	}
	
	// Both a and b are negative and the sum is positive
	else if( a < 0 && b < 0 && result > 0) {
		exit( OVERFLOW );
	}
	
	// a is negative and the absolute value is less than b but sum is negative
	else if( a < 0 && ( 0 - a ) < b && result < 0) {
		exit( OVERFLOW );
	}
	
	// b is negative and the absolute value is less than a but sum is negative
	else if ( b < 0 && ( 0 - b) < a && result < 0) {
		exit( OVERFLOW );
	}
	
	// a is negative and the absolute value is greater than b but sum is positive
	else if( a < 0 && ( 0 - a ) > b && result > 0) {
		exit( OVERFLOW );
	}
	
	// b is negative and the absolute value is greater than a but sum is positive
	else if ( b < 0 && ( 0 - b ) > a && result > 0) {
		exit( OVERFLOW );
	}
	
	// Difference is larger than the largest long value or smaller than the smallest long value
	else if ( result < LONG_MIN || result > LONG_MAX ) {
		exit( OVERFLOW );
	}
	// If sum passes these tests, there is no overflow
	else {
		return result;
	}	 
}

/** 
   Subtracts two values while checking for overflow
   @param a first value 
   @param b second value being subtracted from a
   @return result difference of a and b
*/
long minus( long a, long b )
{
   long result = a - b;
   
   // Both a and b are positive where a is larger than b but the difference is negative
   if ( a > 0 && b > 0 && a > b && result < 0 ) {
      exit( OVERFLOW );
   }
   
   // Both a and b are positive where a is smaller than b but the difference is positive
   else if ( a > 0 && b > 0 && a < b && result > 0 ) {
      exit( OVERFLOW );
   }
   
   // a is negative and b is positive but the difference is positive
   else if( a < 0 && b > 0 && result > 0 ) {
      exit( OVERFLOW );
   }
   
   // a is positive and b is negative but the difference is negative
   else if( a > 0 && b < 0 && result < 0 ) {
      exit( OVERFLOW );
   }
   
   // Both a and b are negative where the absolute value of a is smaller than that of b but the difference is negative 
   else if( a < 0 && b < 0 && ( 0 - a ) < ( 0 - b ) && result < 0 ) {
      exit( OVERFLOW );
   }
   
   // Both a and b are negative where the absolute value of a is larger than that of b but the difference is positive
   else if( a < 0 && b < 0 && ( 0 - a ) > ( 0 - b ) && result > 0 ) {
      exit( OVERFLOW );
   }
   
   // Difference is larger than the largest long value or smaller than the smallest long value
   else if ( result > LONG_MAX || result < LONG_MIN ) {
      exit( OVERFLOW );
   }
   
   // If difference passes these tests, there is no overflow
   else {
      return result;
   }
}

/** 
   Multiplies two values while checking for overflow
   @param a first value being multiplied
   @param b second value being multiplied
   @return result product of a and b
*/
long times( long a, long b )
{
   
   long x = 0;
   long result = 0;
   
   // Both a and b are positive
   if ( a > 0 && b > 0 ) {
      x = LONG_MAX / b;
      if ( a > x ) {
         exit( OVERFLOW );
      }
      else {
         result = a * b;
      }
   }
   
   // a is negative and b is positive
   else if ( a < 0 && b > 0 ) {
      x = LONG_MIN / a;
      if ( b > x ) {
         exit( OVERFLOW );
      }
      else {
         result = a * b;
      }
   }
   
   // a is positive and b is negative
   else if ( a > 0 && b < 0 ) {
      x = LONG_MIN / b;
      if ( a > x ) {
         exit( OVERFLOW );
      }
      else {
         result = a * b;
      }
   }
   
   // Both a and b are negative
   else if ( a < 0 && b < 0 ) {
      x = LONG_MAX / b;
      if ( ( 0 - a ) > ( 0 - x) ) {
         exit( OVERFLOW );
      }
      else {
         result = a * b;
      }
   }
   
   return result;
   
}

/** 
   Divides two values while checking for overflow
   @param a first value, numerator
   @param b second value, denominator
   @return result dividend of a and b
*/
long divide( long a, long b )
{

   // Divide by 0
   if( b == 0 ) {
      exit( DIVIDE_BY_ZERO );
   }

   long result =   a / b;
   
   // Dividend is larger than largest long value or smaller than the smallest long value
   if ( result > LONG_MAX || result < LONG_MIN ) {
      exit( OVERFLOW );
   }
   
   return result; 
   
}
