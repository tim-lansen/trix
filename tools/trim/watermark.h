#pragma once

extern "C" {
#include <libavutil/imgutils.h>
#include <libavutil/frame.h>
}


class Overlay
{
public:
    Overlay(uint32_t width, uint32_t height, AVPixelFormat fmt, uint8_t component);
    ~Overlay();
    void apply(char *dst, uint8_t code);
private:
    unsigned int m_size;
    char *m_overlay_data;
    uint8_t *m_plane_offset;
};


class Watermark
{
public:
    Watermark();
private:
    unsigned int w, h;
};
