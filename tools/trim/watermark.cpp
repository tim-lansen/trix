#include <vector>
#include <unordered_set>
#include <unordered_map>
#include <stdarg.h>

#include "watermark.h"

void clog(_IO_FILE *std, const char *format, ...);

std::unordered_map<uint8_t, char> g_MapFormToB64symbol;
//std::vector<uint8_t> g_Forms;
std::unordered_map<char, uint8_t> g_MapB64symbolToForm;

const char *g_Base64symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/[]()<>?.";

enum Direction
{
    up = 1,
    up_right = 2,
    right = 4,
    right_down = 8,
    down,
    down_left,
    left,
    left_up
};


void line(char *plane, int w, int h, Direction direction, int size, char val)
{
    // Draw a line on plane from center
    // Line width = 'size', color = 'val'
}

void generate_overlay_8bit(uint8_t *plane, uint32_t width, uint32_t height, uint8_t alter)
{

}


// Generate map for decode, and vector (for encode)
void generate_forms()
{
    size_t symbols_count = strlen(g_Base64symbols);
    uint8_t code = 0;
    for(uint8_t i0 = 0; i0 < 6; ++i0) {
        for(uint8_t i1 = i0 + 1; i1 < 7; ++i1) {
            for(uint8_t i2 = i1 + 1; i2 < 8; ++i2) {
                // form is a designation of 3-directional blot
                uint8_t form = (1 << i0) | (1 << i1) | (1 << i2);
                char b64symbol = g_Base64symbols[g_MapB64symbolToForm.size()];
                g_MapB64symbolToForm[b64symbol] = form;
                g_MapFormToB64symbol[form] = b64symbol;
                if(g_MapB64symbolToForm.size() >= symbols_count)
                    return;
            }
        }
    }
    for(uint8_t i0 = 0; i0 < 5; ++i0) {
        for(uint8_t i1 = i0 + 1; i1 < 6; ++i1) {
            for(uint8_t i2 = i1 + 1; i2 < 7; ++i2) {
                for(uint8_t i3 = i2 + 1; i3 < 8; ++i3) {
                    // now form is a designation of 4-directional blot
                    uint8_t form = (1 << i0) | (1 << i1) | (1 << i2) | (1 << i3);
                    char b64symbol = g_Base64symbols[g_MapB64symbolToForm.size()];
                    g_MapB64symbolToForm[b64symbol] = form;
                    g_MapFormToB64symbol[form] = b64symbol;
                    if(g_MapB64symbolToForm.size() >= symbols_count)
                        return;
                }
            }
        }
    }
}

uint32_t encode_message(uint8_t *dst, uint8_t *msg, uint32_t size)
{
    uint32_t ep = 0;
    for(uint32_t i = 0; i < size; ++i) {
        // encode every 3 source bytes with 5 symbols
        ep += 2;    // encode_byte()
    }
    return ep;
}

Overlay::Overlay(uint32_t width, uint32_t height, AVPixelFormat fmt, uint8_t component)
{
    AVFrame *frame = av_frame_alloc();
    frame->width = width;
    frame->height = height;
    frame->format = fmt;
    const AVPixFmtDescriptor *pd = av_pix_fmt_desc_get(fmt);
    if(component >= pd->nb_components)
        component = pd->nb_components - 1;
    const AVComponentDescriptor *avcd = &pd->comp[component];
    int plane = avcd->plane;
    //int size = av_image_get_buffer_size(fmt, width, height, 1);
    //const uint8_t *data = (const uint8_t *)av_malloc(size);
    av_image_fill_arrays(frame->data, frame->linesize, 0, fmt, width, height, 1);
    m_plane_offset = frame->data[plane];
    int cw, ch;
    if(plane) {
        cw = width >> pd->log2_chroma_w;
        ch = height >> pd->log2_chroma_h;
    } else {
        cw = width;
        ch = height;
    }
    // Calculate plane size
    m_overlay_size = ch * frame->linesize[plane];
    m_overlay_count = 56; // 21 + 15 + 10 + 6 + 3 + 1;
    m_overlay_data = (uint8_t *)av_mallocz(m_overlay_count * m_overlay_size);
    av_free(frame);
}

void Overlay::apply(void* dst, uint8_t code)
{
    uint32_t c = code % m_overlay_count;
    uint8_t *overlay = m_overlay_data + c * m_overlay_size;
    uint8_t *plane = (uint8_t*)dst;
    // Applying overlay
    for(uint32_t i = 0; i < m_overlay_size; ++i, plane++, overlay++) {
        *plane += *overlay;
    }
}

Overlay::~Overlay()
{
    av_free(m_overlay_data);
}


Watermark::Watermark(uint32_t width, uint32_t height, AVPixelFormat fmt, void *msg, uint32_t msg_size)
{
    mp_overlay = new Overlay(width, height, fmt, 2);
    mp_message = (uint8_t*)malloc(4 * msg_size);
    mp_encoded_message = mp_message + msg_size;
    m_message_size = msg_size;
    memcpy(mp_message, msg, msg_size);
    m_encoded_message_size = encode_message(mp_encoded_message, mp_message, msg_size);
    generate_forms();
    clog(stderr, "Generated %d forms\n", g_MapB64symbolToForm.size());
}

Watermark::~Watermark()
{
    free(mp_message);
    mp_message = 0;
    mp_encoded_message = 0;
    m_message_size = 0;
    delete mp_overlay;
}

