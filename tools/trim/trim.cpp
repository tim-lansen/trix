// sudo apt-get install libavutil-dev


extern "C" {
#include <libavutil/imgutils.h>
}
#include "trim.h"
#include "support.h"


#ifdef WINDOWS
HANDLE stdIn = GetStdHandle(STD_INPUT_HANDLE), stdOut = GetStdHandle(STD_OUTPUT_HANDLE);
#else
int stdIn = 0, stdOut = 1;
#endif


int g_PipeBufferSize = 0;
char* g_Output = NULL;
char* g_Pin = NULL;
char* g_Pout = NULL;
u_int g_TrimStart = 0;
u_int g_TrimLength = 0;
u_int g_TrimEnd = 0;
int g_PatternOffset = 0;
//PIX_FMT_DESC* g_PixelFormat = NULL;
AVPixelFormat g_PixelFormat = AV_PIX_FMT_NONE;

typedef enum {
    op_scan,
    op_test,
    op_trim
}OPERATION;

OPERATION g_Operation;

__inline u_int _read_from_pipe_(char* buffer, int &frame_number, u_int buffer_capacity)
{
    u_int frame_size = cPattern::get_frame_size();
    u_int left = frame_size;
    buffer += (frame_number % buffer_capacity) * frame_size;
    DWORD nBytesRead = 0;
    for (; left > 0;)
    {
        if (ReadFile(stdIn, buffer, g_PipeBufferSize, &nBytesRead, NULL))
        {
            left -= nBytesRead;
            if (nBytesRead != g_PipeBufferSize && left)
            {
                fprintf(stderr, "frame size error (%08x)\n", frame_size - left);
                cPattern::set_frame_size(frame_size - left);
                break;
            }
            buffer += nBytesRead;
        }
        else
        {
            fprintf(stderr, "=== Read error ===\n");
            return 0;
        }
    }
    frame_number++;
    return 1;
}

__inline u_int _write_to_pipe_(char* buffer, int &frame_number, u_int buffer_capacity)
{
    u_int frame_size = cPattern::get_frame_size();
    buffer += (frame_number % buffer_capacity) * frame_size;
    DWORD nBytesWrite = 0;
    for (; frame_size > 0;)
    {
        if (WriteFile(stdOut, buffer, frame_size, &nBytesWrite, NULL))
        {
            frame_size -= nBytesWrite;
            buffer += nBytesWrite;
        }
        else
        {
            fprintf(stderr, "=== Write error ===\n");
            return 0;
        }
    }
    frame_number++;
    return 1;
}


int scan(int frame_skip, int pattern_length, char* output, int global_offset)
{
    // Read stdin
    // scan for sequence of 'pattern_length' unique frames
    u_int memory_capacity = pattern_length + 2;
    cPattern scanner;
    cPattern::init_scan(&scanner, frame_skip, pattern_length, memory_capacity);

    int frame_number = 0;

    for (;;)
    {
        fprintf(stderr, "frame #%d \r", frame_number);
        if (!_read_from_pipe_(frame_data, frame_number, memory_capacity))
            goto FALLOUT;
        if (scanner.data_lock())
            break;
    }
FALLOUT:
    fprintf(stderr, "\nScanned %d frames\n", frame_number);
#ifdef WINDOWS
    CloseHandle(stdIn);
#endif
    return scanner.data_write_out(output, global_offset);
}


int test(char* manifest)
{
    int stab;
    int feeding_frame_number;
    cPattern scanner, pattern;
    fprintf(stderr, "=== TEST ===\n");
    u_int ff = cPattern::init_trim(&pattern, manifest);
    u_int memory_capacity = ff;
    //char* frame_data = (char*)malloc((memory_capacity + (memory_capacity >> 1)) * cPattern::get_frame_size());
    int frame_read = 0;
    fprintf(stderr, "Memory capacity: %d frames\n", memory_capacity);

    cPattern::init_scan_trim(&scanner, pattern.get_pattern_length(), memory_capacity);

    pattern.dump();
    scanner.dump();

    fprintf(stderr, "=== Preload ===\n");
    for (; frame_read < pattern.get_pattern_length();)
    {
        fprintf(stderr, "Preload frame #%d\r", frame_read);
        if (!_read_from_pipe_(frame_data, frame_read, memory_capacity))
            return -1;
    }
    fprintf(stderr, "\n=== Search pattern ===\n");
    for (;;)
    {
        fprintf(stderr, "Scan: read frame #%d\r", frame_read);
        if (!_read_from_pipe_(frame_data, frame_read, memory_capacity))
            return -1;
        scanner.set_frame(frame_read);
        if (scanner == pattern)
            break;
    }
    fprintf(stderr, "\n=== Pattern found at %d ===\n", frame_read - pattern.get_pattern_length());
    return frame_read - pattern.get_pattern_length();
}


int trim(char* manifest_in, char* manifest_out)
{
    int stab;
    int feeding_frame_number;
    cPattern scanner, pattern_in, pattern_out;
    fprintf(stderr, "=== TRIM ===\n");
    u_int ff1 = cPattern::init_trim(&pattern_in, manifest_in);
    u_int ff2 = cPattern::init_trim(&pattern_out, manifest_out);
    u_int memory_capacity = max(ff1, ff2);

    char* frames = (char*)malloc((memory_capacity + (memory_capacity >> 1)) * cPattern::get_frame_size());
    int frame_read = 0, passed_frames = 0;

    fprintf(stderr, "Memory capacity: %d frames\n", memory_capacity);

    cPattern::init_scan_trim(&scanner, pattern_in.get_pattern_length(), memory_capacity, frames);
    //cPattern::init_scan_trim(&scanner_out, pattern_out.get_pattern_length(), memory_capacity, frame_data);

    pattern_in.dump();
    pattern_out.dump();
    scanner.dump();

    fprintf(stderr, "=== Preload ===\n");
    for (; frame_read < pattern_in.get_pattern_length();)
    {
        fprintf(stderr, "Preload frame #%d\r", frame_read);
        if(!_read_from_pipe_(frames, frame_read, memory_capacity))
            goto FALLOUT2;
        scanner.process(frame_read - 1);
    }
    fprintf(stderr, "\n=== Search In pattern ===\n");
    for (;;)
    {
        fprintf(stderr, "Scan: read frame #%d\r", frame_read);
        if (!_read_from_pipe_(frames, frame_read, memory_capacity))
            goto FALLOUT2;
        scanner.set_frame(frame_read);
        if (scanner == pattern_in)
            break;
    }
    fprintf(stderr, "\n=== In pattern found at %d ===\n", frame_read - pattern_in.get_pattern_length());

    // Re-init scanner
    cPattern::init_scan_trim(&scanner, pattern_out.get_pattern_length(), memory_capacity);

    // Start feeding frames
    // We have to get frame_number-feeding_frame_number == g_PatternOut.get_length() + g_PatternOut.get_offset()

    feeding_frame_number = frame_read - pattern_in.get_pattern_length();
    stab = pattern_out.get_pattern_length() - pattern_in.get_pattern_length();
    fprintf(stderr, "Stab: %d\n", stab);
    while (stab > 0)
    {
        // Read (-stab) more frames to buffer
        fprintf(stderr, "Stab: read frame #%d\r", frame_read);
        if (!_read_from_pipe_(frames, frame_read, memory_capacity))
            goto FALLOUT2;
        stab--;
    }
    while (stab < 0)
    {
        // Feed (stab) frames to stdout
        fprintf(stderr, "Stab: feed frame #%d\r", feeding_frame_number);
        if (!_write_to_pipe_(frame_data, feeding_frame_number, memory_capacity))
            goto FALLOUT2;
        stab++;
    }
    fprintf_s(stderr, "\n");
    if (feeding_frame_number != frame_read - pattern_out.get_pattern_length())
        fprintf_s(stderr, "**************************  feeding frame %d\n", feeding_frame_number);

    // Starting Read-N-Feed
    fprintf(stderr, "\n=== Read-N-Feed %d ===\n", feeding_frame_number);
    for (;;)
    {
        if (!_write_to_pipe_(frame_data, feeding_frame_number, memory_capacity))
            goto FALLOUT2;
        if (!_read_from_pipe_(frame_data, frame_read, memory_capacity))
            goto FALLOUT2;
        passed_frames++;
        scanner.set_frame(frame_read);
        if (scanner == pattern_out)
            break;
    }
    fprintf(stderr, "=== Out-pattern found at #%d ===\n", frame_read - pattern_out.get_pattern_length());
#if PASS_TAIL
    fprintf(stderr, "=== Out-pattern found, Reading tail ===\n");
    // Read tail
    for (;;)
    {
        frame_data_next = frame_data + (frame_number % memory_capacity) * cPattern::get_frame_size();
        pointer = 0;
        bytes2read = cPattern::get_frame_size();
        for (; bytes2read > 0;)
        {
            if (ReadFile(stdIn, frame_data_next + pointer, bytes2read, &nBytesRead, NULL))
            {
                if (!nBytesRead)
                    continue;
                bytes2read -= nBytesRead;
                //pointer += nBytesRead;
            }
            else
            {
                fprintf(stderr, "=== FIN ===\n");
                goto FALLOUT2;
            }
        }
        fprintf(stderr, "Tail: frame #%d\n", frame_number);
        frame_number++;
    }
#endif
    fprintf(stderr, "=== FIN ===\n");
FALLOUT2:
    //fprintf(stderr, "================= Have read (%lld) =================\n", readbytecounter / g_FrameSize);
    fprintf(stderr, "=== Have read %d frames ===\n", frame_read);
    fprintf(stderr, "=== Passed %d frames ===\n", passed_frames);
#ifdef WINDOWS
    CloseHandle(stdIn);
    CloseHandle(stdOut);
#endif
    return 0;
}


int Parse_Params(int argc, char **argv)
{
    if (argc < 4)
    {
        fprintf(stderr, Usage_String);
        return -1;
    }
    if (!strcmp(argv[1], "scan"))
    {
        g_Operation = op_scan;
    }
    else if (!strcmp(argv[1], "test"))
    {
        g_Operation = op_test;
    }
    else if (!strcmp(argv[1], "trim"))
    {
        g_Operation = op_trim;
    }
    else
    {
        fprintf(stderr, "ERROR: Unknown operation (%s)\n\n%s", argv[1], Usage_String);
        return -1;
    }

    u_int width = 0;
    u_int height = 0;
    u_int frame_start = 0;
    u_int frame_count = 0;
    u_int round = 16;
    int global_offset = -1;
    for (int i = 2; i < argc; i++)
    {
        if (!(strcmp("-o", argv[i]) && strcmp("--output", argv[i])))
        {
            if (g_Output)
            {
                fprintf(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }
            g_Output = argv[++i];
        }
        else if (!strcmp("--pin", argv[i]))
        {
            if (g_Pin)
            {
                fprintf(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }
            g_Pin = argv[++i];
        }
        else if (!strcmp("--pout", argv[i]))
        {
            if (g_Pout)
            {
                fprintf(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }
            g_Pout = argv[++i];
        }
        else if (!(strcmp("-s", argv[i]) && strcmp("--size", argv[i])))
        {
            if (width || height)
            {
                fprintf(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }
            width = atoi(argv[++i]);
            height = atoi(argv[++i]);
        }
        else if (!(strcmp("-p", argv[i]) && strcmp("--pix_fmt", argv[i])))
        {
            if (g_PixelFormat != AV_PIX_FMT_NONE)
            {
                fprintf(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }
            g_PixelFormat = av_get_pix_fmt(argv[++i]);
            if (g_PixelFormat == AV_PIX_FMT_NONE)
            {
                fprintf(stderr, Error_Unknown_Pixel_Format, argv[i]);
                return -1;
            }
        }
        else if (!(strcmp("-a", argv[i]) && strcmp("--start_frame", argv[i])))
        {
            if (frame_start)
            {
                fprintf(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }
            frame_start = atoi(argv[++i]);
        }
        else if (!(strcmp("-c", argv[i]) && strcmp("--frame_count", argv[i])))
        {
            if (frame_count)
            {
                fprintf(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }
            frame_count = atoi(argv[++i]);
        }
        else if (!(strcmp("-r", argv[i]) && strcmp("--round", argv[i])))
        {
            round = atoi(argv[++i]);
        }
        else if (!(strcmp("-g", argv[i]) && strcmp("--global_offset", argv[i])))
        {
            if (global_offset != -1)
            {
                fprintf(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }
            global_offset = atoi(argv[++i]);
            if (global_offset < 0)
            {
                fprintf(stderr, "ERROR: Bad value (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }
        }
        else
        {
            fprintf(stderr, "ERROR: Unknown option (%s)\n\n%s", argv[i], Usage_String);
            return -1;
        }
    }
    g_TrimStart = frame_start;
    g_TrimLength = frame_count;
    if (frame_count)
    {
        g_TrimEnd = g_TrimStart + frame_count;
    }

    // Check params
    if (!(width && height))
    {
        fprintf(stderr, "ERROR: Zero frame size\n");
        exit(-1);
    }
    // Get pipe buffer size and calculate frame size
#ifdef WINDOWS
    g_PipeBufferSize = 0x8000;
#else
    g_PipeBufferSize = fcntl(stdIn, F_GETPIPE_SZ);
    fprintf(stderr, "Pipe buffer size: 0x%08X\n", g_PipeBufferSize);
    if(g_PipeBufferSize > 0x8000)
        g_PipeBufferSize = 0x8000;
#endif
    int frame_size = av_image_get_buffer_size(g_PixelFormat, width, height, round);
    fprintf(stderr, "Frame size (align=%d): %d (0x%X)\n", round, frame_size, frame_size);
    cPattern::set_frame_size(frame_size);
    if (g_Operation == op_scan)
    {
        if (!g_Output)
        {
            fprintf(stderr, "ERROR: No output set for scan operation\n");
            return -1;
        }
        return scan(frame_start, frame_count, g_Output, global_offset);
    }
    else if (g_Operation == op_trim)
    {
        return trim(g_Pin, g_Pout);
    }
    else if (g_Operation == op_test)
    {
        return test(g_Pin);
    }
    return 0;
}


void Usage()
{
    fprintf(stderr, Usage_String);
}


int main(int argc, char **argv)
{
    return Parse_Params(argc, argv);
}

