import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import DebugPanel from './components/DebugPanel';
import useChatStore from './store/chatStore';

export default function App() {
  const sidebarOpen = useChatStore((s) => s.sidebarOpen);

  return (
    <div
      id="app-container"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
      }}
    >
      <Header />

      <div
        style={{
          display: 'flex',
          flex: 1,
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <Sidebar />

        <main
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            background: 'var(--bg-chat)',
            minWidth: 0,
          }}
        >
          <ChatWindow />
        </main>
      </div>

      <DebugPanel />
    </div>
  );
}
