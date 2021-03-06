
#include "support.h"
#include "crc_pattern.h"
#include <vector>


void clog(_IO_FILE *std, const char *format, ...);


char* cut_line_z(char * b, char sep=0)
{
    if(!sep) {
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
    } else {
        char c = *b;
        for(;; b++) {
            c = *b;
            if(!c) {
                return NULL;
            }
            if(c == sep) {
                break;
            }
        }
        for(;;) {
            *b++ = 0;
            c = *b;
            if(!c) {
                return NULL;
            }
            if(c != sep) {
                return b;
            }
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


u_int32_t adler32(void * buffer, u_int count, u_int step, u_int32_t buf_size)
{
    unsigned char * buf = (unsigned char *)buffer;
    u_int32_t s1 = 1;
    u_int32_t s2 = 0;

    u_int n = 0;
    for(; count; --count) {
        s1 = (s1 + buf[n]) % 65521;
        s2 = (s2 + s1) % 65521;
        n = (n + step) % buf_size;
    }
    return (s2 << 16) + s1;
}


// Calculate content difference using sum of squares of absolute differences per pixel
// for 8-bit formats
u_int64_t diff_08(void * buffer1, void * buffer2, u_int count, u_int step, u_int32_t buf_size)
{
    u_int8_t * b1 = (unsigned char *)buffer1;
    u_int8_t * b2 = (unsigned char *)buffer2;
    u_int64_t diff = 0;

    u_int n = 0;
    for(; count; --count) {
        u_int16_t d;
        u_int16_t d1 = b1[n];
        u_int16_t d2 = b2[n];
        if(d1 > d2)
            d = (d1 - d2);
        else
            d = (d2 - d1);
        diff += d*d;
        n = (n + step) % buf_size;
    }
    return diff;
}


// Calculate content difference using sum of squares of absolute differences per pixel
// for >8 bit formats
u_int64_t diff_16(void * buffer1, void * buffer2, u_int count, u_int step, u_int32_t buf_size)
{
    u_int16_t * b1 = (u_int16_t *)buffer1;
    u_int16_t * b2 = (u_int16_t *)buffer2;
    u_int64_t diff = 0;
    buf_size = buf_size >> 1;
    step = step >> 1;

    u_int n = 0;
    for(; count; --count) {
        u_int32_t d;
        u_int32_t d1 = b1[n];
        u_int32_t d2 = b2[n];
        if(d1 > d2)
            d = (d1 - d2);
        else
            d = (d2 - d1);
        diff += d*d;
        n = (n + step) % buf_size;
    }
    return diff;
}


unsigned int FrameBuffer::frameSize = 0;
unsigned int FrameBuffer::scanStep = 127;
bool FrameBuffer::frameSizeChanged = false;


FrameBuffer::FrameBuffer()
    : m_capacity(0)
    , m_buffer(0)
{}
FrameBuffer::~FrameBuffer()
{
    safe_free(m_buffer);
    m_buffer_size = 0;
}
void FrameBuffer::init(unsigned int capacity)
{
    m_capacity = capacity;
    if(!frameSize) {
        /*if(frameSize != frame_size) {
            clog(stderr, "Error: initializing FrameBuffer with different frame size\nPrevious: %d (0x%X)\nNew:      %d (0x%X)\n", frameSize, frameSize, frame_size, frame_size);
        }*/
        clog(stderr, "FrameBuffer::frameSize is not initialized\n");
        throw(-1);
    }
    //frameSize = frame_size;
    m_buffer_size = frameSize * capacity;
    m_buffer_size = (m_buffer_size + (m_buffer_size >> 1) + 0x100) & 0x7FFFFF00;
    m_buffer = (unsigned char *)malloc(m_buffer_size);
}
void FrameBuffer::set_frame_size(unsigned int size)
{
    if(frameSize) {
        if(frameSizeChanged) {
            clog(stderr, "Error: DataPattern::FrameSize is already changed to %d (0x%x)\n", frameSize, frameSize);
            return;
        }
        clog(stderr, "Warning: DataPattern::FrameSize is already set to %d (0x%x), changing to %d (0x%x)\n", frameSize, frameSize, size, size);
        frameSizeChanged = true;
    }
    frameSize = size;
    u_int bs = frameSize * m_capacity;
    if(bs > m_buffer_size) {
        m_buffer_size = (bs + 0x100) & 0x7FFFFF00;
        m_buffer = (unsigned char *)realloc(m_buffer, m_buffer_size);
    }
}
void FrameBuffer::init_frame_size(unsigned int size)
{
    if(frameSize) {
        clog(stderr, "Error: FrameBuffer::frameSize is already set to %d (0x%x)\n", frameSize, frameSize);
        return;
    }
    frameSize = size;
    scanStep = 1;
    if(frameSize > (MAX_CRC_SCAN_SIZE << 1)) {
        unsigned int s = frameSize / MAX_CRC_SCAN_SIZE;
        do {
            scanStep = scanStep << 1;
        } while(scanStep < s);
        scanStep--;
    }
    clog(stderr, "FrameBuffer::frameSize init to %d (0x%x), scanStep is %d\n", frameSize, frameSize, scanStep);
}
unsigned int FrameBuffer::get_frame_size()
{
    return frameSize;
}
unsigned char * FrameBuffer::get_frame_pointer(unsigned int i)
{
    if(m_buffer && frameSize && m_capacity)
        return m_buffer + frameSize * (i % m_capacity);
    return 0;
}


CRCPattern::CRCPattern()
    : m_type(pattern_undefined)
    , m_pattern_length(0x7FFFFFFF)
    , m_frame(0)
    , m_skip(0), m_iskip(0)
    , m_scan_end(false)
    , m_bitdepth(8)
{
    memset(crc, 0, sizeof(crc));
}
CRCPattern::~CRCPattern()
{}

bool CRCPattern::operator == (CRCPattern &b)
{
    if(m_type == pattern_undefined || b.m_type == pattern_undefined)
        return true;
    if(m_pattern_length != b.m_pattern_length) {
        clog(stderr, "Sequence lengths are not equal.\n");
        return false;
    }
    if(m_pattern_length == 0) {
        clog(stderr, "Validate fake pattern.\n");
        return true;
    }
    if(m_frame < m_pattern_length || b.m_frame < m_pattern_length) {
        return false;
    }
    unsigned int idxa = (m_frame - m_pattern_length) % m_frame_buffer.m_capacity;
    unsigned int idxb = (b.m_frame - m_pattern_length) % b.m_frame_buffer.m_capacity;
    for(int i = 0; i < m_pattern_length; ++i) {
        if(crc[idxa++] != b.crc[idxb++])
            return false;
        if(idxa >= m_frame_buffer.m_capacity)
            idxa -= m_frame_buffer.m_capacity;
        if(idxb >= b.m_frame_buffer.m_capacity)
            idxb -= b.m_frame_buffer.m_capacity;
    }
    return true;
}


// Calculate difference between two frames
void CRCPattern::dif_frame()
{
    if(m_frame) {
        u_int idx = m_frame % m_frame_buffer.m_capacity;
        if(m_bitdepth <= 8) {
            dif[idx] = diff_08(
                m_frame_buffer.get_frame_pointer(m_frame - 1),
                m_frame_buffer.get_frame_pointer(m_frame),
                MAX_CRC_SCAN_SIZE,
                m_frame_buffer.scanStep,
                m_frame_buffer.frameSize
            );
        } else {
            dif[idx] = diff_16(
                m_frame_buffer.get_frame_pointer(m_frame - 1),
                m_frame_buffer.get_frame_pointer(m_frame),
                MAX_CRC_SCAN_SIZE,
                m_frame_buffer.scanStep,
                m_frame_buffer.frameSize
            );
        }
    }
}


// Scene detection
bool CRCPattern::is_scene()
{
    if(m_frame <= m_frame_buffer.m_capacity)
        return false;
    u_int64_t d0 = dif[(m_frame - m_pattern_length) % m_frame_buffer.m_capacity];
    d0 -= d0 >> 2;
    for(int i = m_frame - m_pattern_length + 1; i < m_frame - m_pattern_length + m_scenedetect_length; ++i) {
        u_int64_t dx = dif[i % m_frame_buffer.m_capacity];
        if(dx > d0) {
            return false;
        }
    }
    return true;
}


// Calculate CRC for part of frame
void CRCPattern::crc_frame()
{
    // Calculate CRCs for given frame number
    u_int idx = m_frame % m_frame_buffer.m_capacity;
    unsigned char * fstart = m_frame_buffer.get_frame_pointer(m_frame);
    crc[idx] = adler32(fstart, MAX_CRC_SCAN_SIZE, m_frame_buffer.scanStep, m_frame_buffer.frameSize);
#ifdef DEBUG
    char *bb = m_crc_str;
    for(int i = 0; i < m_frame_buffer.m_capacity; ++i) {
        bb += sprintf(bb, "%08X ", crc[i]);
    }
#endif
    m_frame++;
}


bool CRCPattern::data_lock()
{
    int i, j;
    if(!m_scan_end) {
        dif_frame();
        crc_frame();
        if(m_iskip) {
            m_iskip--;
        } else {
            if(m_frame >= m_pattern_length + m_skip) {
                // Check frames for duplications
                m_scan_end = true;
                for(i = 0; i < m_pattern_length - 1; ++i) {
                    for(j = i + 1; j < m_pattern_length; ++j) {
                        if(crc[i] == crc[j]) {
                            m_scan_end = false;
                            break;
                        }
                    }
                    if(!m_scan_end)
                        break;
                }
                if(m_scan_end) {
                    // Check dif: first frame's diff must be greater any other's
                    u_int64_t d0 = dif[(m_frame - m_pattern_length) % m_frame_buffer.m_capacity];
                    d0 -= d0 >> 2;
                    for(i = m_frame - m_pattern_length + 1; i < m_frame - m_pattern_length + m_scenedetect_length; ++i) {
                        u_int64_t dx = dif[i % m_frame_buffer.m_capacity];
                        if(dx > d0) {
                            clog(stderr, "Skip pattern at %d\n", m_frame - m_pattern_length);
                            m_scan_end = false;
                            break;
                        }
                    }
                }
            }
        }
    }
    return m_scan_end;
}

int CRCPattern::data_write_out(char* manifest_file)
{
    if(!m_scan_end) {
        clog(stderr, "Data is not locked!\n");
        return ERROR_PATTERN_IS_NOT_LOCKED;
    }
    char b[1024];
    // Write manifest
    //char *bb = b + sprintf(b, "{\"pattern_offset\": %d, \"length\": %d, \"crc\": [", m_frame - m_pattern_length, m_pattern_length);
    char *bb = b + sprintf(b, "pattern_offset=%d;length=%d;crc=", m_frame - m_pattern_length, m_pattern_length);
    unsigned int idx = (m_frame - m_pattern_length) % m_frame_buffer.m_capacity;
    for(int i = 0; i < m_pattern_length; ++i) {
        bb += sprintf(bb, "%u,", crc[idx++]);
        if(idx >= m_frame_buffer.m_capacity)
            idx -= m_frame_buffer.m_capacity;
    }
    //bb -= 2;
    //strcpy(bb, "]}\n");
    bb -= 1;
    *bb = '\n';
    if(manifest_file) {
        int f = _open(manifest_file, _O_CREAT | _O_TRUNC | _O_BINARY | _O_WRONLY, _S_IREAD | _S_IWRITE);
        if(f == -1) {
            DWORD error = GetLastError();
            clog(stderr, "Error opening %s (%08X)\n", b, GetLastError());
            return error;
        }
        _write(f, b, strlen(b));
        _close(f);
    } else {
        fprintf(stderr, b);
    }
    return 0;
}

bool CRCPattern::init_scan(int frame_skip, int pattern_length, int scene_size, u_int capacity, u_int bitdepth)
{
    // Initialize pattern for scan
    m_frame_buffer.init(capacity);
    m_type = pattern_scan;
    m_pattern_length = pattern_length;
    m_scenedetect_length = scene_size;
    m_iskip = frame_skip;
    m_skip = frame_skip;
    memset(dif, 0, sizeof(dif));
    m_bitdepth = bitdepth;
    return true;
}

bool CRCPattern::init_scan_trim(int pattern_length, u_int capacity)
{
    // Initialize pattern for scan-trim
    m_frame_buffer.init(capacity);
    m_type = pattern_scan_trim;
    m_pattern_length = pattern_length;
    return true;
}

u_int CRCPattern::init_trim(char* man)
{
    // Initialize pattern with arg
    // Example:
    // length=4;pattern_offset=112;crc=1020394,556345,2345678,4443
    // return 0 if error, else - required frame feed length (including negative offset)
    m_type = pattern_trim;
    if(!man) {
        // Special case
        clog(stderr, "Special case: absent pattern.\n");
        m_pattern_length = 0;
        return 0;
    }
    char *next;
    for(; man;) {
        next = cut_line_z(man, ';');
        char *val = split(man, '=');
        if(val) {
            if(!strcmp("length", man)) {
                m_pattern_length = atoi(val);
            } else if(!strcmp("crc", man)) {
                // Read CRCs
                int i = 0;
                do {
                    man = val;
                    val = split(man, ',');
                    crc[i++] = atoi(man);
                } while(val);
                if(i != m_pattern_length) {
                    clog(stderr, "CRC count differs from pattern length: %d vs %d\n", i, m_pattern_length);
                }
            }
        }
        man = next;
    }
    //clog(stderr, "parsed: length=%d, data=%s\n", p->pattern_length, data);
    if(m_pattern_length == 0x7FFFFFFF) {
        clog(stderr, "ERROR: Pattern length is not set\n");
        return 0;
    }
    //m_frame_buffer.init(m_pattern_length);
    m_frame_buffer.m_capacity = m_pattern_length;
    m_frame = m_pattern_length;
    return m_pattern_length;
}

#ifdef DEBUG
void CRCPattern::dump()
{
    char *bb = m_crc_str;
    for(int i = 0; i < m_pattern_length; ++i) {
        bb += sprintf(bb, "%08X ", crc[i]);
    }
    clog(stderr,
        "Object 0x%08X\n"
        "  type           : %s\n"
        "  pattern_length : %d\n"
        "  scene_length   : %d\n"
        "  mem_capacity   : %d\n"
        "  skip           : %d\n"
        "  iskip          : %d\n"
        "  frame          : %d\n"
        "  CRC            : %s\n"
        "  scan_end       : %s\n",
        this,
        pattern_type_names[m_type],
        m_pattern_length,
        m_scenedetect_length,
        m_frame_buffer.m_capacity,
        m_skip,
        m_iskip,
        m_frame,
        m_crc_str,
        m_scan_end ? "true" : "false");
    //dump_hashes();
}
#endif
