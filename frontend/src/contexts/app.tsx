'use client'

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction
} from 'react'
import { cacheGet, cacheGetJson, cacheSet, cacheSetJson } from '@/lib/cache'
import { getInitialPresetId } from '@/lib/themes'
import type { LawRagLang, LawRagMode } from '@/services/law-rag'
import { CacheKey } from '@/services/constant'

const SIDEBAR_STORAGE_KEY = 'sidebarToggle'

function getInitialThemePreset(): string {
  return getInitialPresetId(cacheGet(CacheKey.ThemePreset))
}

interface AppContextValue {
  themePreset: string
  setThemePreset: Dispatch<SetStateAction<string>>
  toggleSidebar: boolean
  onToggleSidebar: () => void
  /** Law RAG query mode */
  lawRagMode: LawRagMode
  setLawRagMode: Dispatch<SetStateAction<LawRagMode>>
  /** Law RAG response language */
  lawRagLang: LawRagLang
  setLawRagLang: Dispatch<SetStateAction<LawRagLang>>
}

const AppContext = createContext<AppContextValue | null>(null)

export function useAppContext(): AppContextValue {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useAppContext must be used within AppContextProvider')
  }
  return context
}

type AppContextProviderProps = {
  children: ReactNode
}

export function AppContextProvider({ children }: AppContextProviderProps): React.JSX.Element {
  const [themePreset, setThemePreset] = useState<string>(getInitialThemePreset)
  const [toggleSidebar, setToggleSidebarState] = useState<boolean>(false)
  const [lawRagMode, setLawRagMode] = useState<LawRagMode>('base')
  const [lawRagLang, setLawRagLang] = useState<LawRagLang>('ru')

  useEffect(() => {
    cacheSet(CacheKey.ThemePreset, themePreset)
  }, [themePreset])

  useEffect(() => {
    cacheSet(CacheKey.LawRagMode, lawRagMode)
  }, [lawRagMode])

  useEffect(() => {
    cacheSet(CacheKey.LawRagLang, lawRagLang)
  }, [lawRagLang])

  useEffect(() => {
    const defaultOpen = window.innerWidth >= 768
    setToggleSidebarState(cacheGetJson<boolean>(SIDEBAR_STORAGE_KEY, defaultOpen))

    const storedMode = cacheGet(CacheKey.LawRagMode) as LawRagMode | null
    if (storedMode === 'base' || storedMode === 'pro' || storedMode === 'search') {
      setLawRagMode(storedMode)
    }

    const storedLang = cacheGet(CacheKey.LawRagLang) as LawRagLang | null
    if (storedLang === 'ru' || storedLang === 'kg') {
      setLawRagLang(storedLang)
    }
  }, [])

  const onToggleSidebar = useCallback(() => {
    setToggleSidebarState((prev) => {
      const next = !prev
      cacheSetJson(SIDEBAR_STORAGE_KEY, next)
      return next
    })
  }, [])

  // Memoize context value to prevent unnecessary re-renders of consumers
  const contextValue = useMemo<AppContextValue>(
    () => ({
      themePreset,
      setThemePreset,
      toggleSidebar,
      onToggleSidebar,
      lawRagMode,
      setLawRagMode,
      lawRagLang,
      setLawRagLang
    }),
    [
      themePreset,
      toggleSidebar,
      onToggleSidebar,
      lawRagMode,
      lawRagLang
    ]
  )

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>
}
