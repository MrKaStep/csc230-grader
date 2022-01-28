/**
   @file calc.c
   @author Jack Ballard (jeballar)
   
   Top-level component that reads and evaluates expressions and prints the result

*/

#include "operation.h"
#include "base.h"
#include <stdlib.h>
#include <stdio.h>

/** Represents addition */
#define ADD '+'

/** Represents subtraction */
#define SUBTRACT '-'

/** Represents multiplication */
#define MULTIPLY '*'

/** Represents division */
#define DIVIDE '/'

/**
   Help method determining if character is an operator
   @param ch character being determined to be an operator or not
*/
void isOperator ( int ch ) {
   if ( ch == ADD || ch == MULTIPLY || ch == DIVIDE || ch == SUBTRACT + ' ' ) {
      exit( FAIL_INPUT );
   }
}

/**
   Reads in expression, determines values and operators, and returns result
   @return exit status
*/
int main ( void ) 
{
   long val = 0;
   int ch = skipSpace();
   ungetc( ch, stdin );
   long result = readValue();
   ch = skipSpace();
   while ( ch != '\n' ) {
      if ( ch == ADD ) {
         ch = skipSpace();
         isOperator( ch );
         ungetc ( ch, stdin );
         val = readValue();
         result = plus( result, val );
      }
      else if ( ch == SUBTRACT ){
         ch = skipSpace();
         isOperator( ch );
         ungetc ( ch, stdin );
         val = readValue();
         result = minus( result, val );
      }
      else if ( ch == MULTIPLY ) {
         ch = skipSpace();
         isOperator( ch );
         ungetc ( ch, stdin );
         val = readValue();
         result = times( result, val );
      }
      else if ( ch == DIVIDE ) {
         ch = skipSpace();
         isOperator( ch );
         ungetc ( ch, stdin );
         val = readValue();
         result = divide( result, val );
      }
      ch = skipSpace();
   }
   
   writeValue ( result );
   return 0;
}
