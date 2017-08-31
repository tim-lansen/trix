
#include "support.h"
#include "crc_pattern.h"
#include <vector>


char* cut_line_z(char * b)
{
    char c = *b;
    for(;; b++) {
        c = *b;
        if(!c) {
            return NULL;
        }
        if(c == '\r' || c == '\n') {
            break;
        }
    }
    for(;;) {
        *b++ = 0;
        c = *b;
        if(!c) {
            return NULL;
        }
        if(!(c == '\r' || c == '\n')) {
            return b;
        }
    }
}

char* split(char * b, char spl)
{
    char c;
    for(;;) {
        c = *b;
        if(c == 0) {
            return NULL;
        }
        if(c == spl) {
            *b = 0;
            b++;
            return b;
        }
        b++;
    }
}


u_int32_t adler32(void * buffer, u_int32_t buf_length)
{
    unsigned char * buf = (unsigned char *)buffer;
    u_int32_t s1 = 1;
    u_int32_t s2 = 0;

    for(unsigned int n = 0; n < buf_length; n++) {
        s1 = (s1 + buf[n]) % 65521;
        s2 = (s2 + s1) % 65521;
    }
    return (s2 << 16) + s1;
}


u_int DataPattern::FrameSize = 0;
bool  DataPattern::FrameSizeChanged = false;

void DataPattern::set_frame_size(u_int frame_size)
{
    if(FrameSize) {
        if(FrameSizeChanged) {
            fprintf_s(stderr, "Error: DataPattern::FrameSize is already changed to %d (0x%x)\n", FrameSize, FrameSize);
            return;
        }
        fprintf_s(stderr, "Warning: DataPattern::FrameSize is already set to %d (0x%x), changing to %d (0x%x)\n",
            FrameSize, FrameSize,
            frame_size, frame_size);
        FrameSizeChanged = true;
    }
    FrameSize = frame_size;
}


DataPattern::DataPattern()
    : type(pattern_undefined)
    , pattern_length(0x7FFFFFFF)
    , mem_capacity(0)
    , frame(0)
    , data(NULL)
    , skip(0), iskip(0)
    , scan_end(false)
{}
DataPattern::~DataPattern()
{
    safe_free(data);
}

bool DataPattern::operator == (DataPattern &b)
{
    if(type == pattern_undefined || b.type == pattern_undefined)
        return true;
    if(pattern_length != b.pattern_length) {
        fprintf(stderr, "Sequence lengths are not equal.\n");
        return false;
    }
    if(frame < pattern_length || b.frame < pattern_length) {
        return false;
    }
    for(int i = 0; i < pattern_length; i++) {
        if(memcmp(get_pattern_frame(i), b.get_pattern_frame(i), FrameSize) != 0)
            return false;
    }
    return true;
}

bool DataPattern::data_lock()
{
    int i, j;
    if(!scan_end) {
        frame++;
        if(iskip) {
            iskip--;
        } else {
            if(frame >= pattern_length + skip) {
                // Check frames for duplications
                scan_end = true;
                for(i = 0; i < pattern_length - 1; i++) {
                    for(j = i + 1; j < pattern_length; j++) {
                        if(memcmp(get_pattern_frame(i), get_pattern_frame(j), FrameSize) == 0) {
                            scan_end = false;
                            break;
                        }
                    }
                    if(!scan_end)
                        break;
                }
            }
        }
    }
    return scan_end;
}

int DataPattern::data_write_out(char* manifest_file, int global_offset)
{
    if(!scan_end) {
        fprintf_s(stderr, "Data is not locked!\n");
        return ERROR_PATTERN_IS_NOT_LOCKED;
    }
    char b[1024];
    // Store data
    fprintf_s(stderr, "writing %s\n", manifest_file);
    sprintf(b, "%s.data", manifest_file);
    int f = _open(b, _O_CREAT | _O_TRUNC | _O_BINARY | _O_WRONLY, _S_IREAD | _S_IWRITE);
    if(f == -1) {
        DWORD error = GetLastError();
        fprintf_s(stderr, "Error opening %s (%08X)\n", b, GetLastError());
        return error;
    }
    //_write(f, lock, FrameSize * pattern_length);
    for(int i = 0; i < pattern_length; i++) {
        _write(f, get_pattern_frame(i), FrameSize);
    }
    _close(f);
    // Write manifest
    sprintf(b, "global_offset=%d\npattern_offset=%d\nlength=%d\ndata=%s.data\n", global_offset, frame - pattern_length, pattern_length, manifest_file);
    f = _open(manifest_file, _O_CREAT | _O_TRUNC | _O_BINARY | _O_WRONLY, _S_IREAD | _S_IWRITE);
    if(f == -1) {
        DWORD error = GetLastError();
        fprintf_s(stderr, "Error opening %s (%08X)\n", b, GetLastError());
        return error;
    }
    _write(f, b, strlen(b));
    _close(f);
    return 0;
}

bool DataPattern::init_scan(DataPattern* p, u_int frame_skip, u_int pattern_length, u_int mem_capacity)
{
    // Initialize pattern for scan
    if(!FrameSize) {
        fprintf_s(stderr, "Error: FrameSize is not set.\n");
        return false;
    }
    p->type = pattern_scan;
    p->pattern_length = pattern_length;
    p->mem_capacity = mem_capacity;
    p->iskip = frame_skip;
    p->skip = frame_skip;
    //p->data = frame_data;
    p->data = (char*)malloc(FrameSize * (mem_capacity + (mem_capacity >> 1)));
    return true;
}

bool DataPattern::init_scan_trim(DataPattern* p, u_int pattern_length, u_int mem_capacity)
{
    // Initialize pattern for scan-trim
    if(!FrameSize) {
        fprintf_s(stderr, "Error: FrameSize is not set.\n");
        return false;
    }
    p->type = pattern_scan_trim;
    p->pattern_length = pattern_length;
    p->mem_capacity = mem_capacity;
    //p->data = frame_data;
    p->data = (char*)malloc(FrameSize * (mem_capacity + (mem_capacity >> 1)));
    return true;
}

u_int DataPattern::init_trim(DataPattern* p, char* filename)
{
    // Initialize pattern via file
    // return 0 if error, else - required frame feed length (including negative offset)
    if(!filename) {
        // Special case
        fprintf_s(stderr, "Special case: absent pattern.\n");
        p->pattern_length = 0;
        return 0;
    }
    if(!FrameSize) {
        fprintf_s(stderr, "Error: FrameSize is not set.\n");
        return 0;
    }
    if(!p) {
        fprintf_s(stderr, "Error: pattern pointer is NULL.\n");
        return 0;
    }
    int f = _open(filename, _O_RDONLY | _O_BINARY, _S_IREAD);
    if(f == -1) {
        fprintf_s(stderr, "Error: failed to open '%s'.\n", filename);
        return 0;
    }
    p->type = pattern_trim;
    long size = _lseek(f, 0, SEEK_END);
    std::vector <char> cbuf;
    cbuf.reserve(size + 1);
    //char* buf = (char*)malloc((size + 256) & 0x7FFFFF00);
    _lseek(f, 0, SEEK_SET);
    size = _read(f, cbuf.data(), size);
    _close(f);
    char *current = cbuf.data(), *next;
    current[size] = 0;
    char *data = NULL;
    for(; current;) {
        next = cut_line_z(current);
        if(current[0] != '#') {
            // Process non-comments
            char *val = split(current, '=');
            if(val) {
                if(!strcmp("length", current)) {
                    if(p->pattern_length != -1) {
                        //warning
                    }
                    p->pattern_length = atoi(val);
                    p->mem_capacity = p->pattern_length;
                } else if(!strcmp("data", current)) {
                    if(data) {
                        //warning
                    }
                    data = val;
                }
            }
        }
        current = next;
    }
    fprintf_s(stderr, "parsed: length=%d, data=%s\n", p->pattern_length, data);
    if(p->pattern_length == 0x7FFFFFFF) {
        fprintf(stderr, "ERROR: Pattern length is not set\n");
        return 0;
    }
    if(p->pattern_length <= 0) {
        fprintf(stderr, "ERROR: Pattern length is %d\n", p->pattern_length);
        return 0;
    }
    int r, memsize = p->mem_capacity * FrameSize;
    //free(buf);
    f = _open(data, _O_RDONLY | _O_BINARY, _S_IREAD);
    if(f == -1) {
        fprintf_s(stderr, "Error: failed to open '%s'.\n", data);
        return 0;
    }
    size = _lseek(f, 0, SEEK_END);
    _lseek(f, 0, SEEK_SET);
    p->data = (char*)malloc(size);
    r = _read(f, p->data, memsize);
    if(memsize != r) {
        fprintf_s(stderr, "Warning: have read %d (%x) bytes vs %d (%x) required\n", r, r, memsize, memsize);
    }
    _close(f);
    p->frame = p->pattern_length;
    return p->pattern_length;
}

void DataPattern::dump()
{
    fprintf_s(stderr,
        "Object 0x%08X\n"
        "  type           : %s\n"
        "  pattern_length : %d\n"
        "  mem_capacity   : %d\n"
        "  skip           : %d\n"
        "  iskip          : %d\n"
        "  frame          : %d\n"
        "  data           : %08X\n"
        "  scan_end       : %s\n",
        this,
        pattern_type_names[type],
        pattern_length,
        mem_capacity,
        skip,
        iskip,
        frame,
        data,
        scan_end ? "true" : "false");
    //dump_hashes();
}



u_int CRCPattern::FrameSize = 0;
bool  CRCPattern::FrameSizeChanged = false;

void CRCPattern::set_frame_size(u_int frame_size)
{
    if(FrameSize) {
        if(FrameSizeChanged) {
            fprintf_s(stderr, "Error: DataPattern::FrameSize is already changed to %d (0x%x)\n", FrameSize, FrameSize);
            return;
        }
        fprintf_s(stderr, "Warning: DataPattern::FrameSize is already set to %d (0x%x), changing to %d (0x%x)\n",
            FrameSize, FrameSize,
            frame_size, frame_size);
        FrameSizeChanged = true;
    }
    FrameSize = frame_size;
}



CRCPattern::CRCPattern()
    : type(pattern_undefined)
    , pattern_length(0x7FFFFFFF)
    , mem_capacity(0)
    , frame(0)
    , fdata(NULL)
    , skip(0), iskip(0)
    , scan_end(false)
{}
CRCPattern::~CRCPattern()
{
    safe_free(fdata);
}

bool CRCPattern::operator == (CRCPattern &b)
{
    if(type == pattern_undefined || b.type == pattern_undefined)
        return true;
    if(pattern_length != b.pattern_length) {
        fprintf(stderr, "Sequence lengths are not equal.\n");
        return false;
    }
    if(frame < pattern_length || b.frame < pattern_length) {
        return false;
    }
    if(memcmp(crc, b.crc, pattern_length*sizeof(unsigned int)) != 0)
        return false;
    return true;
}

void CRCPattern::process(u_int i)
{
    // Calculate CRC for given frame number
    u_int idx = i % mem_capacity;
    char* fstart = fdata + idx * FrameSize;
    crc[idx] = adler32(fstart, FrameSize < MAX_CRC_SCAN_SIZE ? FrameSize : MAX_CRC_SCAN_SIZE);
}

bool CRCPattern::data_lock()
{
    int i, j;
    if(!scan_end) {
        frame++;
        if(iskip) {
            iskip--;
        } else {
            if(frame >= pattern_length + skip) {
                // Check frames for duplications
                scan_end = true;
                for(i = 0; i < pattern_length - 1; i++) {
                    for(j = i + 1; j < pattern_length; j++) {
                        if(crc[i] == crc[j]) {
                            scan_end = false;
                            break;
                        }
                    }
                    if(!scan_end)
                        break;
                }
            }
        }
    }
    return scan_end;
}

int CRCPattern::data_write_out(char* manifest_file, int global_offset)
{
    if(!scan_end) {
        fprintf_s(stderr, "Data is not locked!\n");
        return ERROR_PATTERN_IS_NOT_LOCKED;
    }
    char b[1024];
    // Write manifest
    char *bb = b + sprintf(b, "global_offset=%d\npattern_offset=%d\nlength=%d\ncrc=", global_offset, frame - pattern_length, pattern_length);
    for(int i = 0; i < pattern_length; ++i) {
        bb += sprintf(bb, "%d ", crc[i]);
    }
    bb--;
    *bb = '\n';
    int f = _open(manifest_file, _O_CREAT | _O_TRUNC | _O_BINARY | _O_WRONLY, _S_IREAD | _S_IWRITE);
    if(f == -1) {
        DWORD error = GetLastError();
        fprintf_s(stderr, "Error opening %s (%08X)\n", b, GetLastError());
        return error;
    }
    _write(f, b, strlen(b));
    _close(f);
    return 0;
}

bool CRCPattern::init_scan(CRCPattern* p, u_int frame_skip, u_int pattern_length, u_int mem_capacity)
{
    // Initialize pattern for scan
    if(!FrameSize) {
        fprintf_s(stderr, "Error: FrameSize is not set.\n");
        return false;
    }
    p->type = pattern_scan;
    p->pattern_length = pattern_length;
    p->mem_capacity = mem_capacity;
    p->iskip = frame_skip;
    p->skip = frame_skip;
    //p->data = frame_data;
    return true;
}

bool CRCPattern::init_scan_trim(CRCPattern* p, u_int pattern_length, u_int mem_capacity, char * frames_data)
{
    // Initialize pattern for scan-trim
    if(!FrameSize) {
        fprintf_s(stderr, "Error: FrameSize is not set.\n");
        return false;
    }
    p->type = pattern_scan_trim;
    p->pattern_length = pattern_length;
    p->mem_capacity = mem_capacity;
    p->fdata = frames_data;
    return true;
}

u_int CRCPattern::init_trim(CRCPattern* p, char* filename)
{
    // Initialize pattern via file
    // return 0 if error, else - required frame feed length (including negative offset)
    if(!filename) {
        // Special case
        fprintf_s(stderr, "Special case: absent pattern.\n");
        p->pattern_length = 0;
        return 0;
    }
    if(!FrameSize) {
        fprintf_s(stderr, "Error: FrameSize is not set.\n");
        return 0;
    }
    if(!p) {
        fprintf_s(stderr, "Error: pattern pointer is NULL.\n");
        return 0;
    }
    int f = _open(filename, _O_RDONLY | _O_BINARY, _S_IREAD);
    if(f == -1) {
        fprintf_s(stderr, "Error: failed to open '%s'.\n", filename);
        return 0;
    }
    p->type = pattern_trim;
    long size = _lseek(f, 0, SEEK_END);
    std::vector <char> cbuf;
    cbuf.reserve(size + 1);
    //char* buf = (char*)malloc((size + 256) & 0x7FFFFF00);
    _lseek(f, 0, SEEK_SET);
    size = _read(f, cbuf.data(), size);
    _close(f);
    char *current = cbuf.data(), *next;
    current[size] = 0;

    for(; current;) {
        next = cut_line_z(current);
        if(current[0] != '#') {
            // Process non-comments
            char *val = split(current, '=');
            if(val) {
                if(!strcmp("length", current)) {
                    if(p->pattern_length != -1) {
                        //warning
                    }
                    p->pattern_length = atoi(val);
                    p->mem_capacity = p->pattern_length;
                } else if(!strcmp("crc", current)) {
                    // Read CRCs
                    int i = 0;
                    do {
                        current = val;
                        val = split(current, ' ');
                        p->crc[i++] = atoi(current);
                    } while(val);
                    if(i != p->pattern_length) {
                        fprintf(stderr, "CRC count differs from pattern length: %d vs %d\n", i, p->pattern_length);
                    }
                }
            }
        }
        current = next;
    }
    //fprintf_s(stderr, "parsed: length=%d, data=%s\n", p->pattern_length, data);
    if(p->pattern_length == 0x7FFFFFFF) {
        fprintf(stderr, "ERROR: Pattern length is not set\n");
        return 0;
    }
    if(p->pattern_length <= 0) {
        fprintf(stderr, "ERROR: Pattern length is %d\n", p->pattern_length);
        return 0;
    }
    p->frame = p->pattern_length;
    return p->pattern_length;
}

void CRCPattern::dump()
{
    char crc_str[512];
    char *bb = crc_str;
    for(int i = 0; i < pattern_length; ++i) {
        bb += sprintf(bb, "%08X ", crc[i]);
    }
    fprintf_s(stderr,
        "Object 0x%08X\n"
        "  type           : %s\n"
        "  pattern_length : %d\n"
        "  mem_capacity   : %d\n"
        "  skip           : %d\n"
        "  iskip          : %d\n"
        "  frame          : %d\n"
        "  CRC            : %s\n"
        "  scan_end       : %s\n",
        this,
        pattern_type_names[type],
        pattern_length,
        mem_capacity,
        skip,
        iskip,
        frame,
        crc_str,
        scan_end ? "true" : "false");
    //dump_hashes();
}
