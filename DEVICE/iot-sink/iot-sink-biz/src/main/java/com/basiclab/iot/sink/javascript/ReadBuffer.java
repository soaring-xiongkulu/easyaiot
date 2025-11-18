package com.basiclab.iot.sink.javascript;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * ReadBuffer
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

public class ReadBuffer {
    private final ByteBuffer buffer;

    public ReadBuffer(byte[] data) {
        this.buffer = ByteBuffer.wrap(data);
        this.buffer.order(ByteOrder.BIG_ENDIAN);
    }

    /**
     * 读取 1 字节无符号大端
     *
     * @return short
     */
    public short readUB1() {
        return (short) (buffer.get() & 0xFF);
    }

    /**
     * 读取 2 字节无符号大端
     *
     * @return int
     */
    public int readUB2() {
        return buffer.getShort() & 0xFFFF;
    }

    /**
     * 读取 4 字节无符号大端
     *
     * @return long
     */
    public long readUB4() {
        return buffer.getInt() & 0xFFFFFFFFL;
    }

    /**
     * 读取 8 字节无符号大端
     *
     * @return long
     */
    public long readUB8() {
        return buffer.getLong();
    }

    /**
     * 读取 1 字节无符号小端
     *
     * @return short
     */
    public short readUL1() {
        return (short) (buffer.get() & 0xFF);
    }

    /**
     * 读取 2 字节无符号小端
     *
     * @return int
     */
    public int readUL2() {
        short value = buffer.getShort();
        return ((value & 0xFF) << 8) | ((value >> 8) & 0xFF);
    }

    /**
     * 读取 4 字节无符号小端
     *
     * @return long
     */
    public long readUL4() {
        int value = buffer.getInt();
        return Integer.reverseBytes(value) & 0xFFFFFFFFL;
    }

    /**
     * 读取 8 字节无符号小端
     *
     * @return long
     */
    public long readUL8() {
        return Long.reverseBytes(buffer.getLong());
    }

    /**
     * 读取 4 字节，单精度浮点数
     *
     * @return float
     */
    public float readFloat() {
        return buffer.getFloat();
    }

    /**
     * 读取 8 字节，双精度浮点数
     *
     * @return double
     */
    public double readDouble() {
        return buffer.getDouble();
    }

    /**
     * 跳过 count 个字节
     *
     * @param count 跳过的字节数
     */
    public void skip(int count) {
        buffer.position(buffer.position() + count);
    }

    /**
     * 标记当前位置
     */
    public void mark() {
        buffer.mark();
    }

    /**
     * 重置到标记位置
     */
    public void reset() {
        buffer.reset();
    }

    /**
     * 读取 count 个 byte
     *
     * @param count 读取的字节数
     * @return byte array
     */
    public byte[] readBytes(int count) {
        byte[] bytes = new byte[count];
        buffer.get(bytes);
        return bytes;
    }

    /**
     * 读取文本（UTF-8）
     *
     * @param count 长度
     * @return 文本
     */
    public String readString(int count) {
        byte[] bytes = new byte[count];
        buffer.get(bytes);
        return new String(bytes, java.nio.charset.StandardCharsets.UTF_8);
    }

    /**
     * 读取文本（指定字符集）
     *
     * @param count   长度
     * @param charSet 字符集
     * @return 文本
     */
    public String readString(int count, String charSet) {
        byte[] bytes = new byte[count];
        buffer.get(bytes);
        return new String(bytes, java.nio.charset.Charset.forName(charSet));
    }

    /**
     * 读取 hex 1个字节
     *
     * @return hex 字符串
     */
    public String readHex() {
        return Integer.toHexString(readUB1() & 0xFF);
    }

    /**
     * 读取 hex count 个字节
     *
     * @param count 字节数
     * @return hex 字符串
     */
    public String readHex(int count) {
        byte[] bytes = readBytes(count);
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02x", b & 0xFF));
        }
        return sb.toString();
    }
}

