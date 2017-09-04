#ifndef HEADERS_H
#define HEADERS_H


#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
//#include <limits.h>
#include <string.h>
#include <memory.h>
#include <math.h>
#include <fcntl.h>
#include <sys/types.h>

#ifdef WINDOWS
    #include <io.h>
    #include <Windows.h>
#else
    #ifdef LINUX
        #include <sys/stat.h>
        #include <sys/io.h>
        #include <unistd.h>
        #ifndef fprintf_s
            #define fprintf_s clog
        #endif
        #ifndef sprintf_s
            #define sprintf_s sprintf
        #endif
        #ifndef _open
            #define _open open
            #define _lseek lseek
            #define _read read
            #define _write write
            #define _close close
        #endif
        #ifndef _O_CREAT
            #define _O_CREAT O_CREAT
            #define _O_RDONLY O_RDONLY
            #define _O_TRUNC O_TRUNC
            #define _O_BINARY 0
            #define _O_WRONLY O_WRONLY
            #define _S_IREAD S_IREAD
            #define _S_IWRITE S_IWRITE
        #endif
        #ifndef GetLastError
            #define GetLastError(x) 0x1111
        #endif
        #ifndef DWORD
            typedef unsigned int DWORD;
        #endif
        #ifndef max
            #define max(a, b) (a) > (b) ? (a) : (b)
        #endif
        #ifndef min
            #define min(a, b) (a) < (b) ? (a) : (b)
        #endif
        //#define sprintf_s snprintf
        #define __inline inline

        bool ReadFile(int file, void * buffer, DWORD number_of_bytes, DWORD *number_of_bytes_read, void *dummy);
        
        bool WriteFile(int file, const void * buffer, DWORD number_of_bytes, DWORD *number_of_bytes_written, void *dummy);

    #else
        #error 'Operating system is not supported'
    #endif
#endif

#define safe_free(x) if (x) { free(x); x = NULL; }

#endif //HEADERS_H