'use client'

import { Suspense } from 'react'
import Chat from '@/components/chat/chat'
import { SideBar } from '@/components/chat/sidebar'
import useChatHook from '@/components/chat/useChatHook'
import ChatContext from '@/components/chat/chatContext'
import { Header } from '@/components/header/header'

function ChatProvider(): React.JSX.Element {
  const provider = useChatHook()

  return (
    <ChatContext.Provider value={provider}>
      <div className="bg-background flex min-h-0 flex-1 overflow-hidden">
        <SideBar />
        <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden">
          <Header />
          <Chat ref={provider.chatRef} />
        </div>
      </div>
    </ChatContext.Provider>
  )
}

export default function ChatPage(): React.JSX.Element {
  return (
    <Suspense>
      <ChatProvider />
    </Suspense>
  )
}
