#ifndef CRC_PATTERN_H
#define CRC_PATTERN_H

#define cPattern CRCPattern
#define MAX_CRC_SCAN_SIZE 0x10000

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


class DataPattern
{
public:
    DataPattern();

    ~DataPattern();

    bool operator == (DataPattern &b);

    int next_hash_check(u_int hash);
    
    void data_append(const void* data, u_int size);
    
    bool data_lock();
    
    int data_write_out(char* manifest_file, int global_offset);
    
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

    //int next_hash_check(u_int hash);
    //void data_append(const void* data, u_int size);
    bool data_lock();
    int data_write_out(char* manifest_file, int global_offset);
    //void data_next() { frame++; }
    void set_frame(int f)
    {
        process(frame);
        frame = f;
    }
    unsigned int get_frame_crc(u_int i)
    {
        return crc[i];
    }
    void process(u_int i);

    static void set_frame_size(u_int frame_size);

    static u_int get_frame_size() { return FrameSize; }

    static bool init_scan(CRCPattern* p, u_int frame_skip, u_int pattern_length, u_int buffer_length);

    static bool init_scan_trim(CRCPattern* p, u_int pattern_length, u_int buffer_length, char * frames_data);

    static u_int init_trim(CRCPattern* p, char* filename);

    int get_pattern_length()
    {
        return pattern_length;
    }
    //int get_pattern_offset() { return pattern_offset; }
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
    char *fdata;
    unsigned int crc[64];
};

#endif //CRC_PATTERN_H
