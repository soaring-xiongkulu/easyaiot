declare module 'zmodem.js/src/zmodem_browser' {
  export interface Detection {
    confirm(): Session
  }

  export interface Offer {
    get_filename(): string
    get_size(): number
    skip(): void
    accept(): Promise<number[]>
    on(event: 'input', handler: (payload: number[]) => void): void
  }

  export class Sentry {
    constructor(options: {
      to_terminal?: (octets: number[]) => void
      sender?: (octets: number[]) => void
      on_detect?: (detection: Detection) => void
      on_retract?: () => void
    })
    consume(data: Uint8Array | number[]): void
  }

  export class Session {
    type: 'receive' | 'send'
    on(event: 'offer', handler: (offer: Offer) => void): void
    on(event: 'session_end', handler: () => void): void
    start(): Promise<void>
    abort(): void
    close(): Promise<void>
    send_offer(options: {
      name: string
      size: number
      mode?: number
      mtime?: Date
    }): Promise<void>
  }

  export namespace Browser {
    function send_files(
      session: Session,
      files: File[],
      options: {
        on_progress?: (obj: any, xfer: any) => void
        on_file_complete?: (obj: any) => void
      }
    ): Promise<void>
  }

  const Zmodem: {
    Sentry: typeof Sentry
    Session: typeof Session
    Browser: typeof Browser
  }

  export default Zmodem
}
