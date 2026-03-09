import type { LawRagLang } from '@/services/law-rag'

export const UI_STRINGS = {
  ru: {
    welcomeTitle: 'Задайте юридический вопрос',
    welcomeSubtitle: 'Поиск по законодательству Кыргызской Республики',
    composerPlaceholder: 'Введите вопрос…',
    preparingWorkspace: 'Подготовка рабочего пространства…',
    composerHelperText:
      'Нажмите Enter для отправки. Shift + Enter — новая строка.',
    newChat: 'Новый чат',
    clearChat: 'Очистить чат',
    sendMessage: 'Отправить',
    attachFile: 'Прикрепить файл',
    startVoice: 'Начать голосовой ввод',
    stopVoice: 'Остановить голосовой ввод',
    removeImage: 'Удалить изображение',
    removeDocument: 'Удалить документ',
  },
  kg: {
    welcomeTitle: 'Юридикалык суроо бериңиз',
    welcomeSubtitle: 'Кыргыз Республикасынын мыйзамдары боюнча издөө',
    composerPlaceholder: 'Суроңузду жазыңыз…',
    preparingWorkspace: 'Жумуш аянтча даярдалууда…',
    composerHelperText:
      'Жөнөтүү үчүн Enter басыңыз. Shift + Enter — жаңы сап.',
    newChat: 'Жаңы чат',
    clearChat: 'Чатты тазалоо',
    sendMessage: 'Жөнөтүү',
    attachFile: 'Файл тиркөө',
    startVoice: 'Үн киргизүүнү баштоо',
    stopVoice: 'Үн киргизүүнү токтотуу',
    removeImage: 'Сүрөттү жок кылуу',
    removeDocument: 'Документти жок кылуу',
  },
} as const satisfies Record<LawRagLang, Record<string, string>>

export type UIStrings = (typeof UI_STRINGS)[LawRagLang]

export function useUIStrings(lang: LawRagLang): UIStrings {
  return UI_STRINGS[lang]
}
