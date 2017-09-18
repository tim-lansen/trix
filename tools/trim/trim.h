#ifndef TRIM_H
#define TRIM_H

#define PASS_TAIL 0


static char* Error_Allocate = "Cannot allocate %d bytes of memory\n";
static char* Usage_String =
    "Usage: trim <operation> <options>\n"
    "  Operations:\n"
    "    scan  : calculate and store xxhash sequence for specified frames\n"
    "    trim  : trim input sequence\n"
    "  SCAN operation specific options:\n"
    "    -l, --pattern_length <frame count> : (int) pattern size, frames\n"
    "                                         default: 8\n"
    "    -a, --start_frame <start frame>    : (int) number of frames to pass before pattern capture\n"
    "                                         default: 0\n"
    "    -d, --scene <frame count>          : (int) number of frames to use in scene detection\n"
    "                                         default: 5\n"
    "    -o, --output <file path>           : (str)output file to store crc sequence\n"
    "                                         if not set, the sequence info will be written to STDERR\n"
    "  TRIM operation specific options:\n"
    "    --pin <file path|#content>         : (str) in-point manifest file path OR it's content ;-separated\n"
    "    --pout <file path|#content>        : (str) out-point sequence file\n"
    "  Common options:\n"
    "    -s, --size <width> <height>        : (int, int)width and height of frame\n"
    "    -p, --pix_fmt <pixel format>       : (str) pixel format\n"
    "              yuv420p, yuv422p, yuv420p10le, yuv422p10le, yuv420p10be, yuv422p10be\n"
    "    -r, --round <round value>          : (int) internal parameter used to calculate frame size\n"
    "                                         default: 1\n";
static char* Error_Wrong_Number = "ERROR: Wrong number of args (%s)\n";
static char* Error_Unknown_Pixel_Format = "ERROR: Unknown pix_fmt '%s'\n";
//static char* Error_Param_Not_Numeric = "ERROR: Parameter #%d must be numeric!\n";
static char* Error_Param_Out_Of_Range = "ERROR: Parameter #%d out of range!\n";
static char* Error_Param_Not_Compliant = "ERROR: Parameter #%d is not compliant!\n";
//static char* Error_Wrong_Number = "ERROR: Wrong number of args!\n";

#include "crc_pattern.h"

#endif