import { useEffect, useRef, useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/chat'

const WELCOME_MESSAGE = {
  role: 'assistant',
  content:
    'היי! אני העוזר האישי שלך לניהול משימות 🤖\nספרי לי בטקסט חופשי מה צריך להוסיף, לעדכן, למחוק או לבדוק.',
}

function App() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const sendMessage = async () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading) return

    setMessages((prev) => [...prev, { role: 'user', content: trimmed }])
    setInput('')
    setIsLoading(true)
    setError(null)

    let res
    try {
      res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed }),
      })
    } catch {
      setError('הייתה בעיה בתקשורת עם השרת. ודאי שהוא רץ ונסי שוב.')
      setIsLoading(false)
      return
    }

    try {
      const data = await res.json()

      if (!res.ok) {
        setError(data.error || 'אירעה שגיאה בעיבוד הבקשה.')
        return
      }

      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }])
    } catch {
      setError('אירעה שגיאה בעיבוד התגובה מהשרת.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>עוזר המשימות שלי 🤖</h1>
        <p>נהלי את היום שלך בטקסט חופשי</p>
      </header>

      <main className="chat">
        {messages.map((msg, i) => (
          <div key={i} className={`bubble-row ${msg.role}`}>
            <div className={`bubble ${msg.role}`}>{msg.content}</div>
          </div>
        ))}

        {isLoading && (
          <div className="bubble-row assistant">
            <div className="bubble assistant typing">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}

        {error && <div className="error-banner">{error}</div>}

        <div ref={messagesEndRef} />
      </main>

      <footer className="composer">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="מה תרצי לעשות? לדוגמה: תזכירי לי מחר להתקשר לרופא"
          rows={1}
        />
        <button onClick={sendMessage} disabled={isLoading || !input.trim()}>
          שליחה
        </button>
      </footer>
    </div>
  )
}

export default App
