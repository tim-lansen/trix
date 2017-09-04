#ifndef CRC_PATTERN_H
#define CRC_PATTERN_H

#define cPattern CRCPattern
#define MAX_CRC_SCAN_SIZE 0x1000

#define ERROR_PATTERN_IS_NOT_LOCKED 0xA0000001

typedef enum
{
    pattern_scan = 0,
    pattern_trim,
    pattern_scan_trim,
    pattern_undefined
}PATTERN_TYPE;

static char *pattern_type_names[] = {
    "Scanner", "Trimmer", "Scanner for trim", "Undefined"
};


class FrameBuffer
{
    friend class CRCPattern;
public:
    FrameBuffer();
    ~FrameBuffer();
    void init(unsigned int capacity);
    void set_frame_size(unsigned int size);
    static void init_frame_size(unsigned int size);
    static unsigned int get_frame_size();
    unsigned char * get_frame_pointer(unsigned int i);
private:
    static unsigned int frameSize;
    static unsigned int scanStep;
    static bool frameSizeChanged;
    unsigned int m_capacity;
    unsigned int m_buffer_size;
    unsigned char * m_buffer;
};

class DataPattern
{
public:
    DataPattern();

    ~DataPattern();

    bool operator == (DataPattern &b);

    int next_hash_check(u_int hash);
    
    void data_append(const void* data, u_int size);
    
    bool data_lock();
    
    int data_write_out(char* manifest_file);
    
    void set_frame(int f) { frame = f; }
    
    void* get_pattern_frame(u_int i)
    {
        return (data + FrameSize * ((frame + i - pattern_length) % mem_capacity));
    }

    static void set_frame_size(u_int frame_size);

    static u_int get_frame_size() { return FrameSize; }

    static bool init_scan(DataPattern* p, u_int frame_skip, u_int pattern_length, u_int buffer_length);

    static bool init_scan_trim(DataPattern* p, u_int pattern_length, u_int buffer_length);

    static u_int init_trim(DataPattern* p, char* filename);

    int get_pattern_length()
    {
        return pattern_length;
    }

    void dump();
    void dump_hashes();

private:
    PATTERN_TYPE type;
    int pattern_length, mem_capacity;
    //int pattern_offset;
    int skip, iskip;
    int frame;
    static u_int FrameSize;
    static bool FrameSizeChanged;
    bool scan_end;
protected:
    char *data;
};


class CRCPattern
{
public:
    CRCPattern();

    ~CRCPattern();

    bool operator == (CRCPattern &b);

    bool data_lock();
    int data_write_out(char* manifest_file);
    void crc_frame();
    unsigned int get_frame_crc(u_int i)
    {
        return crc[i];
    }
    //void calc();

    bool init_scan(u_int frame_skip, u_int pattern_length, u_int buffer_length);

    bool init_scan_trim(u_int pattern_length, u_int buffer_length);

    u_int init_trim(char* filename);

    int get_pattern_length()
    {
        return m_pattern_length;
    }
    void dump();
    void dump_hashes();


    FrameBuffer m_frame_buffer;
#ifdef DEBUG
    char m_crc_str[1024];
#endif
private:
    PATTERN_TYPE m_type;
    int m_pattern_length;
    int m_skip, m_iskip;
    int m_frame;
    bool m_scan_end;
protected:
    unsigned int crc[64];
    //bool calc[64];
};





#endif //CRC_PATTERN_H
