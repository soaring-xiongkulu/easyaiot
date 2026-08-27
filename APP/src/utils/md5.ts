/**
 * 流式 MD5（RFC 1321）
 *
 * update 分块喂入、digest 补位输出，全程不持有全量大缓冲：
 * 升级包可能几十 MB，一次性拉成 ArrayBuffer 会造成内存峰值过高，
 * 因此配合 md5FromNetwork 按 Range 分块取流计算。
 */
/** 轮函数常量 T 表：floor(|sin(i+1)| * 2^32)，模块加载时生成一次 */
const K: number[] = (() => {
  const table = new Array<number>(64)
  for (let i = 0; i < 64; i++) {
    table[i] = Math.floor(Math.abs(Math.sin(i + 1)) * 4294967296)
  }
  return table
})()

// prettier-ignore
const S = [
  7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22,
  5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20,
  4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23,
  6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21,
]

const M = new Uint32Array(16)

export interface Md5Stream {
  update(chunk: Uint8Array): void
  digest(): string
}

export function createMd5Stream(): Md5Stream {
  let a0 = 0x67452301
  let b0 = 0xefcdab89
  let c0 = 0x98badcfe
  let d0 = 0x10325476
  let totalLen = 0
  // 不足 64 字节的尾部残留，避免跨块重排
  const tail = new Uint8Array(64)
  let tailLen = 0

  const compress = (block: Uint8Array) => {
    for (let i = 0; i < 16; i++) {
      M[i] = block[i * 4] | (block[i * 4 + 1] << 8) | (block[i * 4 + 2] << 16) | (block[i * 4 + 3] << 24)
    }
    let A = a0
    let B = b0
    let C = c0
    let D = d0
    for (let i = 0; i < 64; i++) {
      let F: number
      let g: number
      if (i < 16) {
        F = (B & C) | (~B & D)
        g = i
      } else if (i < 32) {
        F = (D & B) | (~D & C)
        g = (5 * i + 1) % 16
      } else if (i < 48) {
        F = B ^ C ^ D
        g = (3 * i + 5) % 16
      } else {
        F = C ^ (B | ~D)
        g = (7 * i) % 16
      }
      F = (F + A + K[i] + M[g]) | 0
      A = D
      D = C
      C = B
      B = (B + ((F << S[i]) | (F >>> (32 - S[i])))) | 0
    }
    a0 = (a0 + A) | 0
    b0 = (b0 + B) | 0
    c0 = (c0 + C) | 0
    d0 = (d0 + D) | 0
  }

  return {
    update(chunk: Uint8Array) {
      totalLen += chunk.length
      let offset = 0
      if (tailLen > 0) {
        const take = Math.min(64 - tailLen, chunk.length)
        tail.set(chunk.subarray(0, take), tailLen)
        tailLen += take
        offset += take
        if (tailLen === 64) {
          compress(tail)
          tailLen = 0
        }
      }
      while (offset + 64 <= chunk.length) {
        compress(chunk.subarray(offset, offset + 64))
        offset += 64
      }
      if (offset < chunk.length) {
        tail.set(chunk.subarray(offset))
        tailLen = chunk.length - offset
      }
    },
    digest(): string {
      // 尾部补位：0x80 + 0 填充 + 64 位小端比特长度（RFC 1321）
      const padded = new Uint8Array(tailLen < 56 ? 64 : 128)
      padded.set(tail.subarray(0, tailLen))
      padded[tailLen] = 0x80
      const bitLen = totalLen * 8
      const low32 = bitLen % 0x100000000
      const high32 = Math.floor(bitLen / 0x100000000)
      for (let i = 0; i < 4; i++) {
        padded[padded.length - 8 + i] = (low32 >>> (8 * i)) & 0xff
        padded[padded.length - 4 + i] = (high32 >>> (8 * i)) & 0xff
      }
      compress(padded.subarray(0, 64))
      if (padded.length === 128) {
        compress(padded.subarray(64, 128))
      }
      // 状态字按小端输出 16 字节十六进制
      const out = new Uint8Array(16)
      const set32 = (o: number, v: number) => {
        out[o] = v & 0xff
        out[o + 1] = (v >>> 8) & 0xff
        out[o + 2] = (v >>> 16) & 0xff
        out[o + 3] = (v >>> 24) & 0xff
      }
      set32(0, a0)
      set32(4, b0)
      set32(8, c0)
      set32(12, d0)
      return Array.from(out, b => b.toString(16).padStart(2, '0')).join('')
    },
  }
}

/**
 * 从网络地址流式计算 MD5：Range 分块重取，避免全量缓冲。
 * 对象存储 GET 一般支持 Range（206）；不支持时服务端会整包 200 一次返回，同样可算。
 */
export function md5FromNetwork(
  url: string,
  onProgress?: (percent: number) => void,
  chunkSize = 2 * 1024 * 1024,
): Promise<string> {
  const stream = createMd5Stream()
  let start = 0
  let total = 0

  const requestRange = (startByte: number, endByte: number): Promise<{ bytes: Uint8Array, done: boolean }> =>
    new Promise((resolve, reject) => {
      uni.request({
        url,
        method: 'GET',
        responseType: 'arraybuffer',
        timeout: 120000,
        header: { Range: `bytes=${startByte}-${endByte}` },
        success: (res) => {
          if (res.statusCode === 416) {
            // 起始已越过文件末尾（恰好整块倍数时发生），视为完成
            resolve({ bytes: new Uint8Array(0), done: true })
            return
          }
          if (res.statusCode !== 200 && res.statusCode !== 206) {
            reject(new Error(`fetch status ${res.statusCode}`))
            return
          }
          const bytes = new Uint8Array(res.data as ArrayBuffer)
          ;(res as any).data = null
          if (res.statusCode === 200) {
            // 服务端未支持 Range：整包一次返回
            resolve({ bytes, done: true })
            return
          }
          const cr = String(res.header?.['Content-Range'] || res.header?.['content-range'] || '')
          const m = /^bytes\s+\d+-\d+\/(\d+)$/.exec(cr)
          if (m) {
            total = Number(m[1])
          }
          if (total > 0 && onProgress) {
            onProgress(Math.min(99, Math.floor(((startByte + bytes.length) / total) * 100)))
          }
          resolve({ bytes, done: bytes.length < chunkSize })
        },
        fail: err => reject(new Error(`fetch fail: ${JSON.stringify(err)}`)),
      })
    })

  return (async () => {
    for (;;) {
      const { bytes, done } = await requestRange(start, start + chunkSize - 1)
      stream.update(bytes)
      if (done) {
        break
      }
      start += bytes.length
    }
    onProgress?.(100)
    return stream.digest()
  })()
}
