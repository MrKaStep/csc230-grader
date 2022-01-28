/**
   @file base.c
   @author Jack Ballard (jeballar)
   
   Reads in values in an arbitrary base, then writes them to output in 
   defined base.
   
*/

#include "base.h"
#include "operation.h"

#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <limits.h>

/** Conversion from a character that is a digit, to an int and vise versa */
#define CONVERSION_NUMBER '0'

/** Conversion from a character thats a letter, to an int and vise versa */
#define CONVERSION_LETTER '7'

/** Indicates that a number is negative */
#define NEGATIVE '-'

/** Positive value representing the largest long minimum value */
#define POSITIVE_LONG_MIN 9223372036854775808ul

// This preprocessor syntax makes it so we can override the value of BASE with
// a compiler option.   For some desired base, n, we can compile with: -DBASE=n
// Don't change these three lines of preprocessor directives.
#ifndef BASE
/** Base this program uses for input and output. */
#define BASE 7
#endif

/**
   Skips all non-whitespace characters or EOF and returns following character
   @return ch character after whitespace
*/
int skipSpace( void )
{

   int ch = getchar();
   
   while ( ch == ' ' ) {
	  ch = getchar();
   }
   return ch;
   
}

/**
   Reads a value from current base into base 10
   @return value the converted value
*/
long readValue( void )
{

 // Value we've parsed so far.
	long value = 0;
	
	// Get the next input character.
	int ch = getchar();
	
	bool isNeg = false;
	
	if ( ch == '-' ) {
		isNeg = true;
		ch = getchar();
	}
   
   // Keep reading as long as we're seeing digits.
   while ( (ch >= 48 && ch <= 57) || (ch >= 65 && ch <= 90) ) {
      // Convert from ASCII code for the next digit into the value
      // of that digit.   For example 'A' -> 10 or '7' -> 7
      int d = 0;
      
      if ( ch >= 48 && ch <= 57 ) {
         d = ch - CONVERSION_NUMBER;
      }
      else {
         d = ch - CONVERSION_LETTER;
      }
      
      if ( d > BASE ) {
         exit( FAIL_INPUT );
      }
      // Slide all digits we've read so far one place value to the
      // left.
      value = times( value, BASE );
   
      // Add this digit as a new, low-order digit.
      value = plus( value, d );
      
      // Get the next input character.
      ch = getchar();
   }

   if ( ch == '+' || ch == '-' || ch == '*' || ch == '/' || ch <= 32 || ch == -1 ) {
      
      // ch was one character past the end of the number.   Put it back on
      // the input stream so it's there for other code to parse (see notes
      // below about ungetc()).
      ungetc( ch, stdin );
      
      if ( isNeg ) {
         value = value - ( value + value );
      }
      return value;
   }
   else {
      exit( FAIL_INPUT );
   }
}

/**
   Recursively prints one value at a time with high-order digits first
	@param val value being printed
*/
void recursion ( unsigned long val )
{

		int d = val % BASE;
		
		char ch;
		// Convert it to a character, e.g, 13 -> 'D' or 3 -> '3'
		if ( d >= 0 && d <= 9 ) {
			 ch = d + CONVERSION_NUMBER;
		}
		else {
			ch = d + CONVERSION_LETTER;
		}
	
		// Slide remaining digits to the right.
		val =  val / BASE;
		
		if ( val == 0 ) {
			printf( "%c", ch );
		}
		else {
			recursion ( val );
			printf( "%c", ch );
		}
}

/**	
	Prints value in converted base while taking into consideration special cases
	@param val value being printed
*/
void writeValue ( long val )
{
	unsigned long recVal;
	
	if ( val == 0 ) {
		printf( "%ld\n", val );
	}
	else {
		if ( val == LONG_MIN ) {
			recVal = POSITIVE_LONG_MIN;
			printf( "%c", NEGATIVE ); 
		}	
		else {
			if ( val < 0 ) {
				recVal = 0 - val;
				printf( "%c", NEGATIVE ); 
			}
			else {
				recVal = val;
			}
		}
	
		recursion( recVal );
		printf( "\n" );
	}
}
