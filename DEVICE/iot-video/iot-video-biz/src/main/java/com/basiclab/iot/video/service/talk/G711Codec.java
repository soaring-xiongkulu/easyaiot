package com.basiclab.iot.video.service.talk;

/**
 * G.711 A-law (PCMA) and μ-law (PCMU) PCM16 → companded encoding.
 * Mirrors Python {@code AudioEncoder} in {@code onvif_audio_backchannel.py}.
 */
final class G711Codec {

    private static final int BIAS = 0x84;
    private static final int CLIP = 32635;

    private G711Codec() {
    }

    static byte[] encodePcm16(byte[] pcmData, String codec) {
        if (pcmData == null || pcmData.length < 2) {
            return new byte[0];
        }
        boolean ulaw = "PCMU".equalsIgnoreCase(codec);
        int samples = pcmData.length / 2;
        byte[] out = new byte[samples];
        for (int i = 0; i < samples; i++) {
            int lo = pcmData[i * 2] & 0xFF;
            int hi = pcmData[i * 2 + 1];
            short sample = (short) ((hi << 8) | lo);
            out[i] = ulaw ? linearToMuLaw(sample) : linearToALaw(sample);
        }
        return out;
    }

    private static byte linearToALaw(short pcm) {
        int mask = 0xD5;
        int sign = (~pcm) & 0x80;
        int value = pcm;
        if (sign != 0) {
            value = -value;
            if (value < 0) {
                value = CLIP;
            }
        }
        if (value > CLIP) {
            value = CLIP;
        }
        value += BIAS;
        int exponent = 7;
        for (int expMask = 0x4000; (value & expMask) == 0 && exponent > 0; exponent--, expMask >>= 1) {
            // find segment
        }
        int mantissa = (value >> (exponent + 3)) & 0x0F;
        int alaw = (exponent << 4) | mantissa;
        return (byte) (alaw ^ mask ^ sign);
    }

    private static byte linearToMuLaw(short pcm) {
        int sign = (pcm >> 8) & 0x80;
        int value = pcm;
        if (sign != 0) {
            value = -value;
        }
        if (value > CLIP) {
            value = CLIP;
        }
        value += BIAS;
        int exponent = 7;
        for (int expMask = 0x4000; (value & expMask) == 0 && exponent > 0; exponent--, expMask >>= 1) {
            // find segment
        }
        int mantissa = (value >> (exponent + 3)) & 0x0F;
        int ulaw = ~(sign | (exponent << 4) | mantissa);
        return (byte) ulaw;
    }
}
