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
    void apply(void *dst, uint8_t code);
private:
    unsigned int m_overlay_size;
    unsigned int m_overlay_count;
    uint8_t *m_overlay_data;
    uint8_t *m_plane_offset;
};


class Watermark
{
public:
    Watermark(uint32_t width, uint32_t height, AVPixelFormat fmt, void *msg, uint32_t msg_size);
    Watermark::~Watermark();
    void apply(void *dst)
    {
        uint8_t symbol = mp_encoded_message[m_frame % m_encoded_message_size];
        mp_overlay->apply(dst, symbol);
    }
private:
    uint32_t m_frame;
    Overlay *mp_overlay;
    // Original message and it's size
    uint8_t *mp_message;
    uint32_t m_message_size;
    // Encoded message ends with 0xFF
    uint8_t *mp_encoded_message;
    uint32_t m_encoded_message_size;
    unsigned int w, h;

};
