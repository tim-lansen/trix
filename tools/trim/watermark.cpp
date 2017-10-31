#include <unordered_set>
#include <stdarg.h>

#include "watermark.h"


enum Direction
{
    up,
    up_right,
    right,
    right_down,
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
    int planesize = ch * frame->linesize[plane];
    m_overlay_data = (char *)av_mallocz(planesize);
    av_free(frame);
}

Overlay::~Overlay()
{
    av_free(m_overlay_data);
}




