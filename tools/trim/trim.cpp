// sudo apt-get install libavutil-dev

#include <unordered_set>
#include <stdarg.h>

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

#include "watermark.h"

Watermark *gp_Watermark = 0;

int g_PipeBufferSize = 0;
AVPixelFormat g_PixelFormat = AV_PIX_FMT_NONE;
std::unordered_set <int> g_8bit_formats = {
    AV_PIX_FMT_YUV420P,   ///< planar YUV 4:2:0, 12bpp, (1 Cr & Cb sample per 2x2 Y samples)
    AV_PIX_FMT_YUYV422,   ///< packed YUV 4:2:2, 16bpp, Y0 Cb Y1 Cr
    AV_PIX_FMT_RGB24,     ///< packed RGB 8:8:8, 24bpp, RGBRGB...
    AV_PIX_FMT_BGR24,     ///< packed RGB 8:8:8, 24bpp, BGRBGR...
    AV_PIX_FMT_YUV422P,   ///< planar YUV 4:2:2, 16bpp, (1 Cr & Cb sample per 2x1 Y samples)
    AV_PIX_FMT_YUV444P,   ///< planar YUV 4:4:4, 24bpp, (1 Cr & Cb sample per 1x1 Y samples)
    AV_PIX_FMT_YUV410P,   ///< planar YUV 4:1:0,  9bpp, (1 Cr & Cb sample per 4x4 Y samples)
    AV_PIX_FMT_YUV411P,   ///< planar YUV 4:1:1, 12bpp, (1 Cr & Cb sample per 4x1 Y samples)
    AV_PIX_FMT_GRAY8,     ///<        Y        ,  8bpp
    AV_PIX_FMT_MONOWHITE, ///<        Y        ,  1bpp, 0 is white, 1 is black, in each byte pixels are ordered from the msb to the lsb
    AV_PIX_FMT_MONOBLACK, ///<        Y        ,  1bpp, 0 is black, 1 is white, in each byte pixels are ordered from the msb to the lsb
    AV_PIX_FMT_PAL8,      ///< 8 bit with AV_PIX_FMT_RGB32 palette
    AV_PIX_FMT_YUVJ420P,  ///< planar YUV 4:2:0, 12bpp, full scale (JPEG), deprecated in favor of AV_PIX_FMT_YUV420P and setting color_range
    AV_PIX_FMT_YUVJ422P,  ///< planar YUV 4:2:2, 16bpp, full scale (JPEG), deprecated in favor of AV_PIX_FMT_YUV422P and setting color_range
    AV_PIX_FMT_YUVJ444P,  ///< planar YUV 4:4:4, 24bpp, full scale (JPEG), deprecated in favor of AV_PIX_FMT_YUV444P and setting color_range
};

typedef enum {
    op_scan,
    op_test,
    op_trim
}OPERATION;

bool g_Log2console = true;
bool g_Jitter = false;



void clog(_IO_FILE *std, const char *format, ...)
{
    if(g_Log2console) {
        va_list arglist;
        va_start(arglist, format);
        vfprintf(std, format, arglist);
        va_end(arglist);
    }
}


__inline u_int read_from_pipe(FrameBuffer &fb, int &frame_number)
{
    u_int frame_size = fb.get_frame_size();
    u_int left = frame_size;
    unsigned char * buffer = fb.get_frame_pointer(frame_number);
    DWORD nBytesRead = 0;
    for(; left > 0;) {
        if(ReadFile(stdIn, buffer, g_PipeBufferSize, &nBytesRead, NULL)) {
            left -= nBytesRead;
            if(nBytesRead != g_PipeBufferSize && left) {
                clog(stderr, "frame size error (%08x)\n", frame_size - left);
                fb.set_frame_size(frame_size - left);
                break;
            }
            buffer += nBytesRead;
        } else {
            clog(stderr, "=== Read error ===\n");
            return 0;
        }
    }
    frame_number++;
    return 1;
}
__inline u_int write_to_pipe(FrameBuffer &fb, int &frame_number)
{
    u_int frame_size = fb.get_frame_size();
    unsigned char * buffer = fb.get_frame_pointer(frame_number);
    DWORD nBytesWrite = 0;
    for(; frame_size > 0;) {
        if(WriteFile(stdOut, buffer, frame_size, &nBytesWrite, NULL)) {
            frame_size -= nBytesWrite;
            buffer += nBytesWrite;
        } else {
            clog(stderr, "=== Write error ===\n");
            return 0;
        }
    }
    frame_number++;
    return 1;
}


int scan(int frame_skip, int pattern_length, int scene_size, char* output)
{
    // Read stdin
    // scan for sequence of 'pattern_length' unique frames
    u_int memory_capacity = max(pattern_length, scene_size) + 3;
    cPattern scanner;
    
    u_int bitdepth = 8;
    auto search = g_8bit_formats.find(g_PixelFormat);
    if(search == g_8bit_formats.end()) {
        bitdepth = 16;
    }
    //printf("Using %d bits data\n", bitdepth);
    
    scanner.init_scan(frame_skip, pattern_length, scene_size, memory_capacity, bitdepth);
    scanner.dump();

    int frame_number = 0;
    bool locked = false;
    for (; !locked;)
    {
        clog(stderr, "frame #%d \r", frame_number);
        if (!read_from_pipe(scanner.m_frame_buffer, frame_number))
            goto FALLOUT;
        locked = scanner.data_lock();
    }
FALLOUT:
    clog(stderr, "\nScanned %d frames\n", frame_number);
#ifdef WINDOWS
    CloseHandle(stdIn);
#endif
    return scanner.data_write_out(output);
}


int test(char* manifest)
{
    int stab;
    int feeding_frame_number;
    cPattern scanner, pattern;
    clog(stderr, "=== TEST ===\n");
    u_int ff = pattern.init_trim(manifest);
    u_int memory_capacity = ff + 5;
    int frame_read = 0;
    clog(stderr, "Memory capacity: %d frames\n", memory_capacity);

    scanner.init_scan_trim(pattern.get_pattern_length(), memory_capacity);

    pattern.dump();
    scanner.dump();

    clog(stderr, "=== Preload ===\n");
    for (; frame_read < pattern.get_pattern_length();)
    {
        clog(stderr, "Preload frame #%d \r", frame_read);
        if (!read_from_pipe(scanner.m_frame_buffer, frame_read))
            return -1;
        scanner.crc_frame();
    }
    clog(stderr, "\n=== Search pattern ===\n");
    for (;;)
    {
        if(scanner == pattern)
            break;
        clog(stderr, "Scan: read frame #%d \r", frame_read);
        if (!read_from_pipe(scanner.m_frame_buffer, frame_read))
            return -1;
        scanner.crc_frame();
    }
    clog(stderr, "\n=== Pattern found at %d ===\n", frame_read - pattern.get_pattern_length());
    return 0;
}


int trim(char* manifest_in, char* manifest_out)
{
    int stab;
    int feeding_frame_number;
    cPattern scanner, pattern_in, pattern_out;
    clog(stderr, "=== TRIM ===\n");
    u_int ff1 = pattern_in.init_trim(manifest_in);
    u_int ff2 = pattern_out.init_trim(manifest_out);
    if(ff1 != ff2 && ff1 && ff2) {
        clog(stderr, "Different pattern sizes are not supported (%d, %d)\n", ff1, ff2);
        return -1;
    }
    u_int memory_capacity = max(ff1, ff2);

    //char* frames = (char*)malloc((memory_capacity + (memory_capacity >> 1)) * cPattern::get_frame_size());
    int frame_read = 0, passed_frames = 0;

    clog(stderr, "Memory capacity: %d frames\n", memory_capacity);

    scanner.init_scan_trim(ff1, memory_capacity);

    pattern_in.dump();
    pattern_out.dump();
    scanner.dump();

    clog(stderr, "=== Preload ===\n");
    for (; frame_read < pattern_in.get_pattern_length();)
    {
        clog(stderr, "Preload frame #%d\r", frame_read);
        if(!read_from_pipe(scanner.m_frame_buffer, frame_read))
            goto FALLOUT2;
        scanner.crc_frame();
    }
    clog(stderr, "\n=== Search In pattern ===\n");
    for (;;)
    {
        if(scanner == pattern_in)
            break;
        clog(stderr, "Scan: read frame #%d\r", frame_read);
        if(!read_from_pipe(scanner.m_frame_buffer, frame_read))
            goto FALLOUT2;
        scanner.dif_frame();
        scanner.crc_frame();
    }
    clog(stderr, "\n=== In pattern found at %d ===\n", frame_read - pattern_in.get_pattern_length());

    // Re-init scanner only if in-pattern is empty
    if(!ff1) {
        scanner.init_scan_trim(ff2, memory_capacity);
    }
    

    // Start feeding frames
    // We have to get frame_number-feeding_frame_number == g_PatternOut.get_length() + g_PatternOut.get_offset()

    feeding_frame_number = frame_read - ff1;
    stab = ff2 - ff1;
    clog(stderr, "Stab: %d\n", stab);
    while (stab > 0)
    {
        // Read (-stab) more frames to buffer
        clog(stderr, "Stab: read frame #%d\r", frame_read);
        if(!read_from_pipe(scanner.m_frame_buffer, frame_read))
            goto FALLOUT2;
        scanner.dif_frame();
        scanner.crc_frame();
        stab--;
    }
    while (stab < 0)
    {
        // Feed (stab) frames to stdout
        clog(stderr, "Stab: feed frame #%d\r", feeding_frame_number);
        if (!write_to_pipe(scanner.m_frame_buffer, feeding_frame_number))
            goto FALLOUT2;
        stab++;
    }
    clog(stderr, "\n");
    if (feeding_frame_number != frame_read - ff2)
        clog(stderr, "**************************  feeding frame %d\n", feeding_frame_number);

    if(g_Jitter) {

        int jitter_count = 2;
        int pass_frames[] = {100, 500};
        int frame_dup = -1;
        bool frame_skip = false;

        // Starting Read-N-Feed
        clog(stderr, "\n=== Read-N-Feed %d ===\n", feeding_frame_number);
        for(;;) {
            if(ff2 && scanner == pattern_out)
                break;
            if(feeding_frame_number == frame_dup) {
                clog(stderr, "=== Duplicating frame %d ===\n", feeding_frame_number);
                frame_dup = -1;
                if(!write_to_pipe(scanner.m_frame_buffer, feeding_frame_number))
                    goto FALLOUT2;
                feeding_frame_number--;
            }
            if(!write_to_pipe(scanner.m_frame_buffer, feeding_frame_number))
                goto FALLOUT2;
            if(frame_skip) {
                clog(stderr, "=== Skipping frame %d ===\n", feeding_frame_number);
                frame_skip = false;
                frame_read--;
                if(!read_from_pipe(scanner.m_frame_buffer, frame_read))
                    goto FALLOUT2;
            }
            if(!read_from_pipe(scanner.m_frame_buffer, frame_read))
                goto FALLOUT2;
            if(jitter_count) {
                scanner.dif_frame();
                if(pass_frames[jitter_count & 1]) {
                    pass_frames[jitter_count & 1]--;
                } else {
                    if(scanner.is_scene()) {
                        if(jitter_count % 2 == 0) {
                            // Duplicate frame
                            frame_dup = feeding_frame_number + ff2;
                        } else {
                            // Skip frame
                            frame_skip = true;
                        }
                        jitter_count--;
                    }
                }

            }
            scanner.crc_frame();
            passed_frames++;
        }
    } else {
        // Starting Read-N-Feed
        clog(stderr, "\n=== Read-N-Feed %d ===\n", feeding_frame_number);
        for(;;) {
            if(ff2 && scanner == pattern_out)
                break;
            if(!write_to_pipe(scanner.m_frame_buffer, feeding_frame_number))
                goto FALLOUT2;
            if(!read_from_pipe(scanner.m_frame_buffer, frame_read))
                goto FALLOUT2;
            scanner.crc_frame();
            passed_frames++;
        }
    }
    clog(stderr, "=== Out-pattern found at #%d ===\n", frame_read - pattern_out.get_pattern_length());
#if PASS_TAIL
    clog(stderr, "=== Out-pattern found, Reading tail ===\n");
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
                clog(stderr, "=== FIN ===\n");
                goto FALLOUT2;
            }
        }
        clog(stderr, "Tail: frame #%d\n", frame_number);
        frame_number++;
    }
#endif
    clog(stderr, "=== FIN ===\n");
FALLOUT2:
    //clog(stderr, "================= Have read (%lld) =================\n", readbytecounter / g_FrameSize);
    clog(stderr, "=== Have read %d frames ===\n", frame_read);
    clog(stderr, "=== Passed %d frames ===\n", passed_frames);
#ifdef WINDOWS
    CloseHandle(stdIn);
    CloseHandle(stdOut);
#endif
    return 0;
}


int parse_params_run(int argc, char **argv)
{
    OPERATION op;
    int result = 0;
    if (argc < 4)
    {
        clog(stderr, Usage_String);
        return -1;
    }
    if (!strcmp(argv[1], "scan"))
    {
        op = op_scan;
    }
    else if (!strcmp(argv[1], "test"))
    {
        op = op_test;
    }
    else if (!strcmp(argv[1], "trim"))
    {
        op = op_trim;
    }
    else
    {
        clog(stderr, "ERROR: Unknown operation (%s)\n\n%s", argv[1], Usage_String);
        return -1;
    }

    u_int width = 0;
    u_int height = 0;
    u_int frame_start = 0;
    u_int scene_size = 5;
    u_int pattern_length = 8;
    u_int round = 1;

    char *pin = 0;
    char *pout = 0;
    char *watermark = 0;
    char *output = NULL;

    for (int i = 2; i < argc; i++)
    {
        if (!(strcmp("-o", argv[i]) && strcmp("--output", argv[i])))
        {
            if (output)
            {
                clog(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }
            output = argv[++i];
        }
        else if (!strcmp("--pin", argv[i]))
        {
            if (pin)
            {
                clog(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }
            pin = argv[++i];
        }
        else if (!strcmp("--pout", argv[i]))
        {
            if (pout)
            {
                clog(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }
            pout = argv[++i];
        }
        else if (!strcmp("--watermark", argv[i])) {
            if(watermark) {
                clog(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }
            watermark = argv[++i];
        } else if(!strcmp("--jitter", argv[i])) {
            g_Jitter = true;
        }
        else if (!(strcmp("-s", argv[i]) && strcmp("--size", argv[i])))
        {
            if (width || height)
            {
                clog(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }
            width = atoi(argv[++i]);
            height = atoi(argv[++i]);
        }
        else if (!(strcmp("-p", argv[i]) && strcmp("--pix_fmt", argv[i])))
        {
            if (g_PixelFormat != AV_PIX_FMT_NONE)
            {
                clog(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }
            g_PixelFormat = av_get_pix_fmt(argv[++i]);
            if (g_PixelFormat == AV_PIX_FMT_NONE)
            {
                clog(stderr, Error_Unknown_Pixel_Format, argv[i]);
                return -1;
            }
        }
        else if (!(strcmp("-a", argv[i]) && strcmp("--start_frame", argv[i])))
        {
            if (frame_start)
            {
                clog(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }
            frame_start = atoi(argv[++i]);
        }
        else if(!(strcmp("-d", argv[i]) && strcmp("--scene", argv[i]))) {
            /*if(frame_start) {
                clog(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }*/
            scene_size = atoi(argv[++i]);
        }
        else if(!(strcmp("-l", argv[i]) && strcmp("--pattern_length", argv[i])))
        {
            /*if (pattern_length)
            {
                clog(stderr, "ERROR: Duplicated option (%s)\n\n%s", argv[i], Usage_String);
                return -1;
            }*/
            pattern_length = atoi(argv[++i]);
        }
        else if (!(strcmp("-r", argv[i]) && strcmp("--round", argv[i])))
        {
            round = atoi(argv[++i]);
        }
        else
        {
            clog(stderr, "ERROR: Unknown option (%s)\n\n%s", argv[i], Usage_String);
            return -1;
        }
    }
    //g_TrimStart = frame_start;
    //g_TrimLength = frame_count;
    /*if (frame_count)
    {
        g_TrimEnd = g_TrimStart + frame_count;
    }*/

    // Check params
    if (!(width && height && g_PixelFormat != AV_PIX_FMT_NONE))
    {
        fprintf(stderr, "ERROR: Zero frame size\n");
        exit(-1);
    }
    if(!output)
        g_Log2console = false;

    // Get pipe buffer size and calculate frame size
#ifdef WINDOWS
    g_PipeBufferSize = 0x8000;
#else
    g_PipeBufferSize = fcntl(stdIn, F_GETPIPE_SZ);
    //clog(stderr, "Pipe buffer size: 0x%08X\n", g_PipeBufferSize);
    if(g_PipeBufferSize > 0x8000)
        g_PipeBufferSize = 0x8000;
#endif
    int frame_size = av_image_get_buffer_size(g_PixelFormat, width, height, round);
    clog(stderr, "Frame size (align=%d): %d (0x%X)\n", round, frame_size, frame_size);
    FrameBuffer::init_frame_size(frame_size);
    
    if(watermark) {
        gp_Watermark = new Watermark(width, height, g_PixelFormat, watermark, strlen(watermark));
    }

    if (op == op_scan)
    {
        return scan(frame_start, pattern_length, scene_size, output);
    }
    else if (op == op_trim)
    {
        return trim(pin, pout);
    }
    else if (op == op_test)
    {
        result = test(pin);
    }
    delete gp_Watermark;
    return result;
}


void usage()
{
    fprintf(stderr, Usage_String);
}


int main(int argc, char **argv)
{
    int result = parse_params_run(argc, argv);
    clog(stderr, "Done\n");
    return result;
}

