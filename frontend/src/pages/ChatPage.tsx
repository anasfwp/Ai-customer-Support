import { useCallback } from 'react';
import Layout from '../components/layout/Layout';
import ChatWindow from '../components/chat/ChatWindow';
import ChatInput from '../components/chat/ChatInput';
import { FullPageSpinner } from '../components/ui/Spinner';
import { useChat } from '../hooks/useChat';

export default function ChatPage() {
  const {
    messages,
    isLoadingHistory,
    isSending,
    send,
    newChat,
    setFeedback,
  } = useChat();

  const handleSuggestion = useCallback(
    (text: string) => {
      send(text);
    },
    [send],
  );

  return (
    <Layout title="Chat" onNewChat={newChat}>
      <div className="flex h-[calc(100vh-4rem)] flex-col">
        {isLoadingHistory ? (
          <div className="flex flex-1 items-center justify-center">
            <FullPageSpinner label="Loading chat history…" />
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto">
            <ChatWindow
              messages={messages}
              onFeedback={setFeedback}
              onSuggestionClick={handleSuggestion}
            />
          </div>
        )}

        <ChatInput onSend={send} disabled={isSending} />
      </div>
    </Layout>
  );
}