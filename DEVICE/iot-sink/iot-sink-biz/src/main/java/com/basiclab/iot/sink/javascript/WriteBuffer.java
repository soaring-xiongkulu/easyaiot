package com.basiclab.iot.sink.javascript;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * WriteBuffer
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

public class WriteBuffer {
    private final java.io.ByteArrayOutputStream outputStream;
    private ByteBuffer buffer;

    public WriteBuffer() {
        this(1024);
    }

    public WriteBuffer(int initialSize) {
        this.outputStream = new java.io.ByteArrayOutputStream(initialSize);
        this.buffer = ByteBuffer.allocate(initialSize);
        this.buffer.order(ByteOrder.BIG_ENDIAN);
    }

    /**
     * 写入 1 字节
     *
     * @param value 值
     */
    public void writeByte(int value) {
        ensureCapacity(1);
        buffer.put((byte) (value & 0xFF));
    }

    /**
     * 写入字节数组
     *
     * @param bytes 字节数组
     */
    public void writeBytes(byte[] bytes) {
        ensureCapacity(bytes.length);
        buffer.put(bytes);
    }

    /**
     * 写入 2 字节短整型（大端）
     *
     * @param value 值
     */
    public void writeShortBE(int value) {
        ensureCapacity(2);
        buffer.putShort((short) value);
    }

    /**
     * 写入 4 字节整型（大端）
     *
     * @param value 值
     */
    public void writeIntBE(int value) {
        ensureCapacity(4);
        buffer.putInt(value);
    }

    /**
     * 写入 8 字节长整型（大端）
     *
     * @param value 值
     */
    public void writeLongBE(long value) {
        ensureCapacity(8);
        buffer.putLong(value);
    }

    /**
     * 写入 4 字节单精度浮点数
     *
     * @param value 值
     */
    public void writeFloat(float value) {
        ensureCapacity(4);
        buffer.putFloat(value);
    }

    /**
     * 写入 8 字节双精度浮点数
     *
     * @param value 值
     */
    public void writeDouble(double value) {
        ensureCapacity(8);
        buffer.putDouble(value);
    }

    /**
     * 转换为字节数组
     *
     * @return 字节数组
     */
    public byte[] toArray() {
        buffer.flip();
        byte[] result = new byte[buffer.remaining()];
        buffer.get(result);
        return result;
    }

    /**
     * 确保缓冲区容量足够
     *
     * @param needed 需要的字节数
     */
    private void ensureCapacity(int needed) {
        if (buffer.remaining() < needed) {
            int newSize = Math.max(buffer.capacity() * 2, buffer.position() + needed);
            ByteBuffer newBuffer = ByteBuffer.allocate(newSize);
            newBuffer.order(ByteOrder.BIG_ENDIAN);
            buffer.flip();
            newBuffer.put(buffer);
            buffer = newBuffer;
        }
    }
}

