// Tiny runtime type-checks for validating LLM tool input payloads at the
// dispatch boundary. Hand-rolled (no zod) to keep the bundle minimal and
// avoid a new dependency. Each validator returns either the narrowed value
// or throws InputValidationError so the caller can convert the failure
// into an error event sent back to the model.

export class InputValidationError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'InputValidationError'
  }
}

export function validateString(value: unknown, field: string): string {
  if (typeof value !== 'string') {
    throw new InputValidationError(`${field} must be a string, got ${typeof value}`)
  }
  return value
}

export function validateRequiredString(value: unknown, field: string): string {
  const s = validateString(value, field)
  if (s.length === 0) {
    throw new InputValidationError(`${field} must be a non-empty string`)
  }
  return s
}

export function validateObject(value: unknown, field: string): Record<string, unknown> {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new InputValidationError(`${field} must be an object`)
  }
  return value as Record<string, unknown>
}

export function validateNumber(value: unknown, field: string): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new InputValidationError(`${field} must be a finite number`)
  }
  return value
}

export function validateBoolean(value: unknown, field: string): boolean {
  if (typeof value !== 'boolean') {
    throw new InputValidationError(`${field} must be a boolean`)
  }
  return value
}

export function validateLiteral<T extends string>(
  value: unknown,
  field: string,
  allowed: readonly T[]
): T {
  if (typeof value !== 'string' || !(allowed as readonly string[]).includes(value)) {
    throw new InputValidationError(`${field} must be one of ${allowed.join(', ')}`)
  }
  return value as T
}