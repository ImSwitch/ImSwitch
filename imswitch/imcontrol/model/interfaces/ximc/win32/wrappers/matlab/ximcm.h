#ifndef INC_XIMCM_H
#define INC_XIMCM_H


#ifdef _MSC_VER

#define MATLAB_IMPORT

/* Matlab compiles a thunk using MSVC compiler on 64-bit systems.
 * Just pass through normal header*/

#elif defined(__APPLE__)

#include <time.h>
#include <wchar.h>

#elif defined(__GNUC__)

/* Usually it is Linux */

#include <time.h>
#include <wchar.h>

#else

#define MATLAB_IMPORT

/* It is a LCC compiler and so 32-bit system.
 * LCC does not speak C99 and needs 32-bit types */

typedef signed char int8_t;
typedef short int16_t;
typedef int int32_t;
typedef __int64 int64_t;
typedef unsigned char uint8_t;
typedef unsigned short uint16_t;
typedef unsigned int uint32_t;
typedef unsigned __int64 uint64_t;
typedef unsigned __int64 ulong_t;
typedef __int64 long_t;
typedef unsigned __int64 time_t;

#define XIMC_NO_STDINT

#endif

#include "ximc.h"

#endif

// vim: ts=4 shiftwidth=4
