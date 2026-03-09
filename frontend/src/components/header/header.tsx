'use client'

import ThemeOptionsDropdown from '@/components/theme/options-dropdown'
import ThemeToggle from '@/components/theme/toggle'
import { Button } from '@/components/ui/button'
import { useAppContext } from '@/contexts/app'
import type { LawRagLang, LawRagMode } from '@/services/law-rag'
import { PanelLeft } from 'lucide-react'
import { cn } from '@/lib/utils'

const MODES: { value: LawRagMode; label: string; title: string }[] = [
  { value: 'base', label: 'Base', title: 'Базовый режим: векторный поиск + LLM (~2–4 сек)' },
  { value: 'pro', label: 'Pro', title: 'Pro режим: LLM-запросы + поиск + LLM (~4–7 сек)' },
  { value: 'search', label: 'Search', title: 'Только поиск, без LLM (~0.2–0.5 сек)' }
]

const LANGS: { value: LawRagLang; label: string; title: string }[] = [
  { value: 'ru', label: 'RU', title: 'Ответы на русском' },
  { value: 'kg', label: 'KG', title: 'Ответы на кыргызском' }
]

export function Header(): React.JSX.Element {
  const {
    toggleSidebar,
    onToggleSidebar,
    lawRagMode,
    setLawRagMode,
    lawRagLang,
    setLawRagLang
  } = useAppContext()

  return (
    <header className="bg-background/95 border-border supports-[backdrop-filter]:bg-background/80 sticky top-0 z-20 w-full border-b pt-[env(safe-area-inset-top)] backdrop-blur-sm">
      <div className="flex items-center gap-2 px-3 py-2 sm:gap-3 sm:px-4 sm:py-3">
        {/* Left: sidebar toggle */}
        <div className="flex min-w-0 shrink-0 items-center">
          {!toggleSidebar && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onToggleSidebar}
              className="hover:bg-primary/5 size-11 rounded-lg transition-colors duration-200 md:size-9"
              title="Open Sidebar"
              aria-label="Open Sidebar"
            >
              <PanelLeft className="size-5" />
            </Button>
          )}
        </div>

        {/* Center: Law RAG controls */}
        <div className="flex flex-1 items-center justify-center gap-2 overflow-x-auto">
          {/* Mode selector */}
          <div
            className="bg-muted flex items-center rounded-lg p-0.5 gap-0.5"
            role="group"
            aria-label="Режим запроса"
          >
            {MODES.map(({ value, label, title }) => (
              <button
                key={value}
                type="button"
                onClick={() => setLawRagMode(value)}
                title={title}
                aria-pressed={lawRagMode === value}
                className={cn(
                  'rounded-md px-2.5 py-1 text-xs font-medium transition-all duration-150',
                  lawRagMode === value
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Lang selector */}
          <div
            className="bg-muted flex items-center rounded-lg p-0.5 gap-0.5"
            role="group"
            aria-label="Язык ответа"
          >
            {LANGS.map(({ value, label, title }) => (
              <button
                key={value}
                type="button"
                onClick={() => setLawRagLang(value)}
                title={title}
                aria-pressed={lawRagLang === value}
                className={cn(
                  'rounded-md px-2.5 py-1 text-xs font-medium transition-all duration-150',
                  lawRagLang === value
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Right: theme controls.
             ThemeOptionsDropdown is hidden on mobile — accessible via sidebar footer. */}
        <nav className="flex shrink-0 items-center gap-1 sm:gap-2">
          <div className="hidden md:flex items-center gap-1">
            <ThemeOptionsDropdown />
          </div>
          <ThemeToggle />
        </nav>
      </div>
    </header>
  )
}
