import { computed, ref } from 'vue'
import type { Language, Locale } from '../types/settings'
import { SUPPORTED_LOCALES } from '../types/settings'

import zhCN from './locales/zh-CN.json'
import zhTW from './locales/zh-TW.json'
import en from './locales/en.json'
import ja from './locales/ja.json'
import ko from './locales/ko.json'
import de from './locales/de.json'
import es from './locales/es.json'
import fr from './locales/fr.json'
import ru from './locales/ru.json'

const messages: Record<Locale, Record<string, string>> = {
  'zh-CN': zhCN,
  'zh-TW': zhTW,
  en,
  ja,
  ko,
  de,
  es,
  fr,
  ru,
}

const currentLocale = ref<Locale>('en')

export const locale = computed(() => currentLocale.value)

const localePrefixMap: Record<string, Locale> = Object.fromEntries(
  SUPPORTED_LOCALES.filter((loc) => loc !== 'zh-CN' && loc !== 'zh-TW').map((loc) => [loc, loc])
)

function resolveLocale(lang: Language): Locale {
  if (lang !== 'system') {
    if (SUPPORTED_LOCALES.includes(lang as Locale)) return lang as Locale
    return 'en'
  }

  if (typeof navigator === 'undefined' || !navigator.language) return 'en'

  const nav = navigator.language.toLowerCase()

  if (nav.startsWith('zh')) {
    if (nav.includes('tw') || nav.includes('hk') || nav.includes('mo')) return 'zh-TW'
    return 'zh-CN'
  }

  for (const [prefix, loc] of Object.entries(localePrefixMap)) {
    if (nav.startsWith(prefix)) return loc
  }

  return 'en'
}

export function setLocale(lang: Language) {
  currentLocale.value = resolveLocale(lang)
}

function translate(loc: Locale, key: string, params?: Record<string, string | number>): string {
  const msg = messages[loc]?.[key] ?? messages['en']?.[key] ?? key
  if (!params) return msg
  return msg.replace(/\{(\w+)\}/g, (_, k) => String(params[k] ?? `{${k}}`))
}

export function useI18n() {
  function t(key: string, params?: Record<string, string | number>): string {
    return translate(currentLocale.value, key, params)
  }
  return { t, locale }
}

export function t(key: string, params?: Record<string, string | number>): string {
  return translate(currentLocale.value, key, params)
}
