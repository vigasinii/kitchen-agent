/* =============================================================
   Kitchen Agent - Frontend Application
   React 18 + Babel JSX, all API calls to http://localhost:8888
   ============================================================= */

const { useState, useEffect, useRef, useCallback, useMemo, createContext, useContext } = React;

const API = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
  ? "http://localhost:8888"
  : "https://kitchen-agent-1sqb.onrender.com";

/* ===================================================================
   INLINE SVG ICONS
   Paths sourced from Lucide icon set (https://lucide.dev)
   Rendered as inline SVG so no runtime DOM manipulation needed.
   =================================================================== */
const ICON_PATHS = {
  LayoutDashboard: `<rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/>`,
  MessageSquare: `<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>`,
  ChefHat: `<path d="M6 13.87A4 4 0 0 1 7.41 6a5.11 5.11 0 0 1 1.05-1.54 5 5 0 0 1 7.08 0A5.11 5.11 0 0 1 16.59 6 4 4 0 0 1 18 13.87V21H6Z"/><line x1="6" x2="18" y1="17" y2="17"/>`,
  CalendarDays: `<rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/><path d="M8 18h.01"/><path d="M12 18h.01"/><path d="M16 18h.01"/>`,
  ShoppingCart: `<circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/>`,
  Users: `<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>`,
  Settings: `<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>`,
  Mic: `<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/>`,
  MicOff: `<line x1="2" x2="22" y1="2" y2="22"/><path d="M18.89 13.23A7.12 7.12 0 0 0 19 12v-2"/><path d="M5 10v2a7 7 0 0 0 12 5"/><path d="M15 9.34V5a3 3 0 0 0-5.68-1.33"/><path d="M9 9v3a3 3 0 0 0 5.12 2.12"/><line x1="12" x2="12" y1="19" y2="22"/>`,
  Send: `<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>`,
  Check: `<path d="M20 6 9 17l-5-5"/>`,
  CheckCircle: `<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>`,
  X: `<path d="M18 6 6 18"/><path d="m6 6 12 12"/>`,
  ChevronDown: `<path d="m6 9 6 6 6-6"/>`,
  ChevronRight: `<path d="m9 18 6-6-6-6"/>`,
  AlertTriangle: `<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>`,
  AlertCircle: `<circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>`,
  Package: `<path d="M16.5 9.4 7.55 4.24"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.29 7 12 12 20.71 7"/><line x1="12" x2="12" y1="22" y2="12"/>`,
  Loader2: `<path d="M21 12a9 9 0 1 1-6.219-8.56"/>`,
  Clock: `<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>`,
  Utensils: `<path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/>`,
  Sparkles: `<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>`,
  Info: `<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>`,
  RefreshCw: `<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>`,
  Minus: `<path d="M5 12h14"/>`,
};

function Icon({ name, size = 18, strokeWidth = 1.75, className = '', style = {} }) {
  const paths = ICON_PATHS[name] || ICON_PATHS.AlertCircle;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`icon ${className}`}
      style={style}
      dangerouslySetInnerHTML={{ __html: paths }}
      aria-hidden="true"
    />
  );
}

/* ===================================================================
   TOAST SYSTEM
   =================================================================== */
const ToastContext = createContext(null);

function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info', duration = 3500) => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={addToast}>
      {children}
      <div className="toast-container">
        {toasts.map(t => (
          <div
            key={t.id}
            className={`toast ${t.type}`}
            onClick={() => removeToast(t.id)}
            style={{ cursor: 'pointer' }}
          >
            {t.type === 'success' && <Icon name="CheckCircle" size={15} />}
            {t.type === 'error' && <Icon name="AlertCircle" size={15} />}
            {t.type === 'info' && <Icon name="Info" size={15} />}
            <span>{t.message}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function useToast() {
  return useContext(ToastContext);
}

/* ===================================================================
   VOICE HOOK
   =================================================================== */
function useVoice(onResult) {
  const [voiceState, setVoiceState] = useState('idle'); // idle | listening | processing
  const recognitionRef = useRef(null);

  const transcriptRef = useRef('');

  const startRecording = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Your browser does not support voice input. Try Chrome.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    transcriptRef.current = '';

    recognition.onresult = (e) => {
      let final = '';
      for (let i = 0; i < e.results.length; i++) {
        if (e.results[i].isFinal) final += e.results[i][0].transcript + ' ';
      }
      if (final.trim()) {
        transcriptRef.current = final.trim();
        onResult(transcriptRef.current);
      }
    };

    recognition.onerror = (e) => {
      if (e.error !== 'no-speech') setVoiceState('idle');
    };
    recognition.onend = () => {
      // Restart if still in listening state (handles browser auto-stop on pause)
      if (recognitionRef.current && recognitionRef.current._active) {
        try { recognition.start(); } catch {}
      }
    };

    recognitionRef.current = recognition;
    recognitionRef.current._active = true;
    recognition.start();
    setVoiceState('listening');
  }, [onResult]);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current._active = false;
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setVoiceState('idle');
  }, []);

  const toggle = useCallback(() => {
    if (voiceState === 'listening') stopRecording();
    else startRecording();
  }, [voiceState, startRecording, stopRecording]);

  return { voiceState, toggle };
}

let currentAudio = null;
let isSpeaking = false;
const speakingListeners = new Set();

function setSpeaking(val) {
  isSpeaking = val;
  speakingListeners.forEach(fn => fn(val));
}

function cleanForTTS(text) {
  return text
    .replace(/\*\*/g, '')
    .replace(/\*/g, '')
    .replace(/#+ /g, '')
    .replace(/^\s*[-•]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    .trim();
}

async function speak(text) {
  if (currentAudio) { currentAudio.pause(); currentAudio = null; }
  if (window.speechSynthesis) window.speechSynthesis.cancel();

  const clean = cleanForTTS(text);

  try {
    setSpeaking(true);
    const res = await fetch(`${API}/tts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: clean, voice: 'hannah' }),
    });
    if (!res.ok) throw new Error('TTS failed');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    currentAudio = new Audio(url);
    currentAudio.play();
    currentAudio.onended = () => { URL.revokeObjectURL(url); currentAudio = null; setSpeaking(false); };
  } catch (err) {
    console.warn('Groq TTS failed:', err);
    setSpeaking(false);
  }
}

function stopSpeaking() {
  if (currentAudio) { currentAudio.pause(); currentAudio.currentTime = 0; currentAudio = null; }
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  setSpeaking(false);
}

/* ===================================================================
   HELPERS
   =================================================================== */
function formatTime(ts) {
  if (!ts) return "";
  try {
    return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch { return ""; }
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

function getDateString() {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
  });
}

function getTodayName() {
  return new Date().toLocaleDateString('en-US', { weekday: 'long' });
}

function getInitials(name) {
  return name.split(' ').map(p => p[0]).join('').toUpperCase().slice(0, 2);
}

// Detect if markdown content has a meal plan table and render as cards
function renderMessageContent(content) {
  const html = marked.parse(content);
  return html;
}

/* ===================================================================
   CHAT MESSAGE COMPONENT
   =================================================================== */
function ChatMessage({ message, onRetry }) {
  const isUser = message.role === 'user';
  const contentHtml = useMemo(() => {
    if (isUser) return null;
    return renderMessageContent(message.content);
  }, [message.content, isUser]);

  return (
    <div className={`message-row ${message.role}`}>
      <div style={{ width: '100%' }}>
        <div className="message-bubble">
          {isUser ? (
            <span>{message.content}</span>
          ) : (
            <div
              className="message-content"
              dangerouslySetInnerHTML={{ __html: contentHtml }}
            />
          )}
        </div>
        {message.retryMsg && onRetry && (
          <button
            onClick={() => onRetry(message.retryMsg)}
            style={{
              marginTop: 8, padding: '6px 14px', fontSize: '.8rem',
              background: 'var(--primary)', color: '#fff', border: 'none',
              borderRadius: 6, cursor: 'pointer', fontWeight: 600,
            }}
          >
            Retry
          </button>
        )}
        {message.time && (
          <div className="message-time">{formatTime(message.time)}</div>
        )}
      </div>
    </div>
  );
}

/* ===================================================================
   VOICE COMPOSER COMPONENT
   =================================================================== */
function VoiceComposer({ onSend, loading, placeholder, chips }) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  const handleVoiceResult = useCallback((transcript) => {
    setInput(transcript);
  }, []);

  const { voiceState, toggle: toggleVoice } = useVoice(handleVoiceResult);

  const handleSend = () => {
    const msg = input.trim();
    if (!msg || loading) return;
    onSend(msg);
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleChip = (chip) => {
    const msg = typeof chip === 'object' ? chip.message : chip;
    onSend(msg);
  };

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
  }, [input]);

  return (
    <div>
      {chips && chips.length > 0 && (
        <div className="chips-row">
          {chips.map(chip => {
            const label = typeof chip === 'object' ? chip.label : chip;
            return (
              <button key={label} className="chip" onClick={() => handleChip(chip)}>
                {label}
              </button>
            );
          })}
        </div>
      )}
      <div className="composer-area">
        <div className="composer-inner">
          <button
            className={`mic-btn ${voiceState !== 'idle' ? voiceState : ''}`}
            onClick={toggleVoice}
            title={voiceState === 'listening' ? 'Stop listening' : 'Start voice input'}
          >
            {voiceState === 'processing' ? (
              <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
            ) : voiceState === 'listening' ? (
              <Icon name="MicOff" size={15} />
            ) : (
              <Icon name="Mic" size={15} />
            )}
          </button>

          <textarea
            ref={textareaRef}
            className="composer-textarea"
            rows={1}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={voiceState === 'listening' ? 'Listening...' : placeholder || 'Type a message...'}
          />

          <button
            className="stop-voice-btn"
            onClick={stopSpeaking}
            title="Stop speaking"
          >
            <Icon name="VolumeX" size={14} />
          </button>

          <button
            className="send-btn-composer"
            onClick={handleSend}
            disabled={loading || !input.trim()}
          >
            {loading ? (
              <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
            ) : (
              <Icon name="Send" size={14} />
            )}
          </button>
        </div>
        {voiceState === 'listening' && (
          <div className="voice-banner">Listening... speak now</div>
        )}
      </div>
    </div>
  );
}

/* ===================================================================
   SIDEBAR COMPONENT
   =================================================================== */
const NAV_ITEMS = [
  { id: 'overview',   label: 'Overview',          icon: 'LayoutDashboard' },
  { id: 'planner',    label: 'AI Meal Planner',    icon: 'MessageSquare'  },
  { id: 'cook',       label: 'Cook Assistant',     icon: 'ChefHat'        },
  { id: 'mealplan',   label: 'Weekly Meal Plan',   icon: 'CalendarDays'   },
  { id: 'grocery',    label: 'Grocery List',       icon: 'ShoppingCart'   },
  { id: 'household',  label: 'Household',          icon: 'Users'          },
  { id: 'analytics',  label: 'Analytics',          icon: 'BarChart2'      },
];

function Sidebar({ activeScreen, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-wordmark">Kitchen Agent</div>
        <div className="sidebar-tagline">Your kitchen, thoughtfully managed</div>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            className={`nav-item ${activeScreen === item.id ? 'active' : ''}`}
            onClick={() => onNavigate(item.id)}
          >
            <Icon name={item.icon} size={16} strokeWidth={1.75} />
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button
          className={`nav-item ${activeScreen === 'settings' ? 'active' : ''}`}
          style={{ width: '100%' }}
          onClick={() => onNavigate('settings')}
        >
          <Icon name="Settings" size={16} strokeWidth={1.75} />
          Settings
        </button>
      </div>
    </aside>
  );
}

/* ===================================================================
   MOBILE NAV COMPONENT
   =================================================================== */
const MOBILE_NAV_ITEMS = [
  { id: 'overview',  label: 'Home',    icon: 'LayoutDashboard' },
  { id: 'planner',   label: 'Planner', icon: 'MessageSquare'  },
  { id: 'cook',      label: 'Cook',    icon: 'ChefHat'        },
  { id: 'mealplan',  label: 'Plan',    icon: 'CalendarDays'   },
  { id: 'grocery',   label: 'Grocery', icon: 'ShoppingCart'   },
];

function MobileNav({ activeScreen, onNavigate }) {
  return (
    <nav className="mobile-nav">
      <div className="mobile-nav-inner">
        {MOBILE_NAV_ITEMS.map(item => (
          <button
            key={item.id}
            className={`mobile-nav-item ${activeScreen === item.id ? 'active' : ''}`}
            onClick={() => onNavigate(item.id)}
          >
            <Icon name={item.icon} size={20} />
            {item.label}
          </button>
        ))}
      </div>
    </nav>
  );
}

/* ===================================================================
   OVERVIEW SCREEN
   =================================================================== */
function OverviewScreen({ onNavigate }) {
  const [members, setMembers] = useState([]);
  const [activePlan, setActivePlan] = useState(null);
  const [groceryStatus, setGroceryStatus] = useState('');
  const [loading, setLoading] = useState(true);
  const addToast = useToast();
  const today = getTodayName();

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/household`).then(r => r.data).catch(() => []),
      axios.get(`${API}/meal-plans`).then(async r => {
        if (r.data.length > 0) {
          const plan = await axios.get(`${API}/meal-plans/${r.data[0].id}`).then(r2 => r2.data);
          // Try to get grocery status
          try {
            const g = await axios.get(`${API}/grocery-lists/${r.data[0].id}`);
            return { plan, groceryStatus: g.data.status || 'pending' };
          } catch {
            return { plan, groceryStatus: 'not generated' };
          }
        }
        return { plan: null, groceryStatus: '' };
      }).catch(() => ({ plan: null, groceryStatus: '' })),
    ]).then(([membersData, planData]) => {
      setMembers(membersData);
      setActivePlan(planData.plan);
      setGroceryStatus(planData.groceryStatus);
      setLoading(false);
    });
  }, []);

  const handleApprove = async () => {
    if (!activePlan) return;
    try {
      await axios.put(`${API}/meal-plans/${activePlan.id}/approve`);
      setActivePlan(p => ({ ...p, status: 'approved' }));
      addToast('Meal plan approved', 'success');
    } catch {
      addToast('Failed to approve plan', 'error');
    }
  };

  const todayMeals = activePlan?.meals?.[today] || {};
  const totalMeals = activePlan ? Object.values(activePlan.meals || {}).reduce((sum, day) => {
    return sum + Object.values(day).filter(Boolean).length;
  }, 0) : 0;

  const MEAL_ICONS = { breakfast: '🌅', lunch: '☀️', dinner: '🌙' };
  const MEMBER_COLORS = ['#234c3c', '#4a7c59', '#7fb069', '#b5d99c'];

  if (loading) {
    return (
      <div className="screen overview-screen">
        <div className="overview-hero skeleton" style={{ height: 120, borderRadius: 16, marginBottom: 28 }} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 28 }}>
          {[0,1,2].map(i => <div key={i} className="skeleton" style={{ height: 110, borderRadius: 14 }} />)}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 14 }}>
          {[0,1].map(i => <div key={i} className="skeleton" style={{ height: 80, borderRadius: 14 }} />)}
        </div>
      </div>
    );
  }

  return (
    <div className="screen overview-screen">

      {/* Hero */}
      <div className="overview-hero">
        <div className="overview-hero-left">
          <div className="overview-greeting-line">{getGreeting()}</div>
          <div className="overview-date-line">{getDateString()}</div>
          <div className="overview-members-row">
            {members.map((m, i) => (
              <div key={m.id} className="member-avatar" style={{ background: MEMBER_COLORS[i % MEMBER_COLORS.length] }} title={m.name}>
                {m.name[0]}
              </div>
            ))}
            <span className="overview-members-label">{members.map(m => m.name.split(' ')[0]).join(', ')}</span>
          </div>
        </div>
        <div className="overview-hero-right">
          <div className="overview-plan-badge" style={{ background: activePlan?.status === 'approved' ? '#e8f5e9' : '#fff8e1', color: activePlan?.status === 'approved' ? '#2e7d32' : '#f57f17' }}>
            <Icon name={activePlan?.status === 'approved' ? 'CheckCircle' : 'Clock'} size={13} />
            {activePlan ? (activePlan.status === 'approved' ? 'Plan approved' : 'Awaiting approval') : 'No active plan'}
          </div>
          <div className="overview-total-meals">{totalMeals} <span>meals this week</span></div>
        </div>
      </div>

      {/* Today's meals */}
      <div className="section-label">Today — {today}</div>
      <div className="overview-today-grid">
        {['breakfast', 'lunch', 'dinner'].map(mealType => {
          const name = todayMeals[mealType];
          return (
            <div className={`overview-meal-card ${!name ? 'empty' : ''}`} key={mealType} onClick={() => onNavigate('planner')}>
              <div className="overview-meal-icon">{MEAL_ICONS[mealType]}</div>
              <div className="overview-meal-type">{mealType}</div>
              <div className="overview-meal-name">{name || 'Not planned yet'}</div>
              {name && <div className="overview-meal-cta">Cook this <Icon name="ChevronRight" size={11} /></div>}
            </div>
          );
        })}
      </div>

      {/* Quick actions */}
      <div className="section-label">Quick actions</div>
      <div className="overview-actions-grid">
        <button className="overview-action-card" onClick={() => onNavigate('planner')}>
          <div className="overview-action-icon" style={{ background: '#e8f0ec' }}><Icon name="MessageSquare" size={20} color="#234c3c" /></div>
          <div className="overview-action-label">Chat with Riya</div>
          <div className="overview-action-sub">Plan or adjust meals</div>
        </button>
        <button className="overview-action-card" onClick={() => onNavigate('cook')}>
          <div className="overview-action-icon" style={{ background: '#fef3e2' }}><Icon name="ChefHat" size={20} color="#e65100" /></div>
          <div className="overview-action-label">Start Cooking</div>
          <div className="overview-action-sub">Step-by-step with Arjun</div>
        </button>
        <button className="overview-action-card" onClick={() => onNavigate('grocery')}>
          <div className="overview-action-icon" style={{ background: '#e3f2fd' }}><Icon name="ShoppingCart" size={20} color="#1565c0" /></div>
          <div className="overview-action-label">Grocery List</div>
          <div className="overview-action-sub">{groceryStatus === 'ordered' ? 'Order placed' : 'View or order'}</div>
        </button>
        <button className="overview-action-card" onClick={() => onNavigate('mealplan')}>
          <div className="overview-action-icon" style={{ background: '#f3e5f5' }}><Icon name="Calendar" size={20} color="#6a1b9a" /></div>
          <div className="overview-action-label">Weekly Plan</div>
          <div className="overview-action-sub">{activePlan?.status === 'approved' ? 'Approved' : 'Review plan'}</div>
        </button>
      </div>

      {/* Approve nudge */}
      {activePlan && activePlan.status !== 'approved' && (
        <div className="attention-card" style={{ marginTop: 20 }}>
          <div className="attention-icon"><Icon name="AlertTriangle" size={18} /></div>
          <div className="attention-text">
            <div className="attention-title">This week's plan needs your approval</div>
            <div className="attention-desc">Week of {activePlan.week_start}</div>
          </div>
          <button className="btn btn-primary btn-sm" onClick={handleApprove}>
            <Icon name="Check" size={13} /> Approve
          </button>
        </div>
      )}
    </div>
  );
}

/* ===================================================================
   PLANNER SCREEN
   =================================================================== */
const PLANNER_CHIPS = [];

function SpeakingBanner() {
  const [speaking, setSpeaking] = useState(isSpeaking);
  useEffect(() => {
    speakingListeners.add(setSpeaking);
    return () => speakingListeners.delete(setSpeaking);
  }, []);
  if (!speaking) return null;
  return (
    <div className="speaking-banner" onClick={stopSpeaking}>
      <span className="speaking-wave">
        <span /><span /><span /><span />
      </span>
      Riya is speaking — tap to stop
    </div>
  );
}

function PlannerScreen() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const addToast = useToast();

  useEffect(() => {
    axios.get(`${API}/conversations/planner`)
      .then(r => {
        setMessages(r.data.map(m => ({
          role: m.role,
          content: m.content,
          time: m.timestamp,
        })));
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendMessage = async (text) => {
    const msg = text.trim();
    if (!msg || loading) return;

    setMessages(prev => [...prev, { role: 'user', content: msg, time: new Date().toISOString() }]);
    setLoading(true);

    try {
      const res = await axios.post(`${API}/chat/planner`, { message: msg });
      const reply = res.data.response;
      setMessages(prev => [...prev, { role: 'assistant', content: reply, time: new Date().toISOString() }]);
      speak(reply);
    } catch (err) {
      const status = err.response?.status;
      const isProviderDown = status === 503 || status === 502;
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: isProviderDown
          ? 'The AI service is temporarily unavailable. You can retry your message.'
          : 'Connection error. Is the backend running?',
        retryMsg: isProviderDown ? msg : null,
        time: new Date().toISOString(),
      }]);
      addToast(isProviderDown ? 'AI provider unavailable' : 'Failed to send message', 'error');
    } finally {
      setLoading(false);
    }
  };

  const clearChat = async () => {
    try {
      await axios.delete(`${API}/conversations/planner`);
      setMessages([]);
      addToast('Chat cleared', 'success');
    } catch {
      addToast('Failed to clear chat', 'error');
    }
  };

  return (
    <div className="chat-screen">
      <div className="chat-screen-header" style={{ padding: '24px 40px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div className="chat-screen-title">Kitchen Planner</div>
          <div className="chat-screen-subtitle">Ready to plan your week</div>
        </div>
        {messages.length > 0 && (
          <button className="clear-chat-btn" onClick={clearChat} title="Clear conversation">
            <Icon name="Trash2" size={14} /> Clear chat
          </button>
        )}
      </div>

      <div className="messages-area">
        {messages.length === 0 && !loading && (
          <div className="empty-state">
            <div className="empty-icon">
              <Icon name="MessageSquare" size={22} />
            </div>
            <div className="empty-title">Start a conversation</div>
            <div className="empty-sub">Ask Kitchen Agent to plan meals, swap a dish, or check dietary restrictions for your household.</div>
          </div>
        )}
        {messages.map((m, i) => (
          <ChatMessage key={i} message={m} onRetry={sendMessage} />
        ))}
        {loading && (
          <div className="typing-indicator">
            <div className="typing-dot" />
            <div className="typing-dot" />
            <div className="typing-dot" />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <SpeakingBanner />

      <VoiceComposer
        onSend={sendMessage}
        loading={loading}
        placeholder="Ask Kitchen Agent to plan meals, swap a dish, check allergies..."
        chips={PLANNER_CHIPS}
      />
    </div>
  );
}

/* ===================================================================
   COOK SCREEN
   =================================================================== */
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const MEAL_TYPES = ['breakfast', 'lunch', 'dinner'];

function CookScreen() {
  const [day, setDay] = useState(getTodayName() || 'Monday');
  const [mealType, setMealType] = useState('dinner');
  const [cookSession, setCookSession] = useState(null);
  const [mealPlanId, setMealPlanId] = useState(null);
  const [starting, setStarting] = useState(false);
  const [mealName, setMealName] = useState('');
  const [plan, setPlan] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const addToast = useToast();

  useEffect(() => {
    axios.get(`${API}/meal-plans`).then(async r => {
      if (r.data.length > 0) {
        const id = r.data[0].id;
        setMealPlanId(id);
        const pd = await axios.get(`${API}/meal-plans/${id}`);
        setPlan(pd.data.meals || {});
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (plan && plan[day] && plan[day][mealType]) {
      setMealName(plan[day][mealType]);
    } else {
      setMealName('');
    }
  }, [plan, day, mealType]);

  useEffect(() => {
    if (cookSession) {
      axios.get(`${API}/conversations/cook_${cookSession.id}`)
        .then(r => {
          setMessages(r.data.map(m => ({
            role: m.role,
            content: m.content,
            time: m.timestamp,
          })));
        })
        .catch(() => {});
    }
  }, [cookSession]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const startSession = async () => {
    if (!mealPlanId) { addToast('No meal plan found', 'error'); return; }
    setStarting(true);
    try {
      const r = await axios.post(`${API}/cook-sessions`, {
        meal_plan_id: mealPlanId,
        day,
        meal_name: mealName || `${mealType} on ${day}`,
      });
      setCookSession(r.data);
      setMessages([]);
      addToast('Cook session started', 'success');
    } catch {
      addToast('Failed to start cook session', 'error');
    }
    setStarting(false);
  };

  const sendMessage = async (text) => {
    const msg = text.trim();
    if (!msg || loading) return;
    if (!cookSession) {
      addToast('Please start a cook session first', 'error');
      return;
    }

    setMessages(prev => [...prev, { role: 'user', content: msg, time: new Date().toISOString() }]);
    setLoading(true);

    try {
      const res = await axios.post(`${API}/chat/cook`, {
        message: msg,
        cook_session_id: cookSession.id,
      });
      const reply = res.data.response;
      setMessages(prev => [...prev, { role: 'assistant', content: reply, time: new Date().toISOString() }]);
      speak(reply);
    } catch (err) {
      const status = err.response?.status;
      const isProviderDown = status === 503 || status === 502;
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: isProviderDown
          ? 'The AI service is temporarily unavailable. You can retry your message.'
          : 'Connection error. Is the backend running?',
        retryMsg: isProviderDown ? msg : null,
        time: new Date().toISOString(),
      }]);
      addToast(isProviderDown ? 'AI provider unavailable' : 'Failed to send message', 'error');
    } finally {
      setLoading(false);
    }
  };

  const sendActionMessage = (prefix) => {
    const base = mealName ? `[${prefix} for ${mealName}] ` : `[${prefix}] `;
    sendMessage(base);
  };

  return (
    <div className="cook-screen">
      <div className="screen-header">
        <div className="screen-title">Cook Assistant</div>
        <div className="screen-subtitle">Step-by-step guidance for any meal in your plan</div>
      </div>

      <div className="cook-selector-row">
        <select
          className="cook-select"
          value={day}
          onChange={e => { setDay(e.target.value); setCookSession(null); }}
        >
          {DAYS.map(d => <option key={d} value={d}>{d}</option>)}
        </select>

        <select
          className="cook-select"
          value={mealType}
          onChange={e => { setMealType(e.target.value); setCookSession(null); }}
        >
          {MEAL_TYPES.map(m => <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>)}
        </select>

        <button
          className={`btn ${cookSession ? 'btn-secondary' : 'btn-primary'}`}
          onClick={startSession}
          disabled={starting || !!cookSession}
        >
          {cookSession ? (
            <><Icon name="CheckCircle" size={14} /> Session Active</>
          ) : starting ? (
            <><span className="spinner" style={{ width: 13, height: 13, borderWidth: 2 }} /> Starting...</>
          ) : (
            <><Icon name="ChefHat" size={14} /> Start Cook Session</>
          )}
        </button>
      </div>

      {mealName && (
        <div className="session-banner">
          <div>
            <div className="session-meal-name">{mealName}</div>
            <div className="session-meta">{day} / {mealType}</div>
          </div>
          {cookSession && (
            <div className="session-id-badge">Session #{cookSession.id}</div>
          )}
        </div>
      )}

      {cookSession && (
        <div className="cook-actions-row">
          <button className="btn btn-ghost btn-sm" onClick={() => sendActionMessage('Ingredient unavailable')}>
            <Icon name="Minus" size={13} />
            Ingredient Unavailable
          </button>
          <button className="btn btn-ghost btn-sm" onClick={() => sendActionMessage('Request substitution')}>
            <Icon name="RefreshCw" size={13} />
            Request Substitution
          </button>
          <button className="btn btn-secondary btn-sm" onClick={() => sendActionMessage('Mark complete')}>
            <Icon name="CheckCircle" size={13} />
            Mark Complete
          </button>
        </div>
      )}

      {!cookSession ? (
        <div className="empty-state">
          <div className="empty-icon">
            <Icon name="ChefHat" size={22} />
          </div>
          <div className="empty-title">Ready to cook?</div>
          <div className="empty-sub">Select a day and meal above, then start a session to get real-time cooking guidance from Kitchen Agent.</div>
        </div>
      ) : (
        <div className="cook-chat-container">
          <div className="cook-messages">
            {messages.length === 0 && !loading && (
              <div className="empty-state" style={{ padding: '32px 16px' }}>
                <div className="empty-icon">
                  <Icon name="MessageSquare" size={18} />
                </div>
                <div className="empty-title">Session started</div>
                <div className="empty-sub">Ask for step-by-step instructions, timings, or substitutions.</div>
              </div>
            )}
            {messages.map((m, i) => (
              <ChatMessage key={i} message={m} onRetry={sendMessage} />
            ))}
            {loading && (
              <div className="typing-indicator">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="cook-composer">
            <VoiceComposerInline
              onSend={sendMessage}
              loading={loading}
              placeholder="Ask for step-by-step help, substitutions, timing..."
            />
          </div>
        </div>
      )}
    </div>
  );
}

// Inline composer for cook chat (no chips, compact)
function VoiceComposerInline({ onSend, loading, placeholder }) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  const handleVoiceResult = useCallback((transcript) => {
    setInput(transcript);
  }, []);
  const { voiceState, toggle: toggleVoice } = useVoice(handleVoiceResult);

  const handleSend = () => {
    const msg = input.trim();
    if (!msg || loading) return;
    onSend(msg);
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', flex: 1 }}>
      <button
        className={`mic-btn ${voiceState !== 'idle' ? voiceState : ''}`}
        onClick={toggleVoice}
        title={voiceState === 'listening' ? 'Stop' : 'Voice input'}
      >
        {voiceState === 'processing' ? (
          <span className="spinner" style={{ width: 13, height: 13, borderWidth: 2 }} />
        ) : voiceState === 'listening' ? (
          <Icon name="MicOff" size={14} />
        ) : (
          <Icon name="Mic" size={14} />
        )}
      </button>
      <textarea
        ref={textareaRef}
        className="cook-input"
        rows={1}
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={voiceState === 'listening' ? 'Listening...' : placeholder}
      />
      <button
        className="send-btn-composer"
        onClick={handleSend}
        disabled={loading || !input.trim()}
      >
        {loading ? (
          <span className="spinner" style={{ width: 13, height: 13, borderWidth: 2 }} />
        ) : (
          <Icon name="Send" size={14} />
        )}
      </button>
    </div>
  );
}

/* ===================================================================
   MEAL PLAN SCREEN
   =================================================================== */
function MealPlanScreen() {
  const [activePlan, setActivePlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const addToast = useToast();

  useEffect(() => {
    axios.get(`${API}/meal-plans`).then(async r => {
      if (r.data.length > 0) {
        const plan = await axios.get(`${API}/meal-plans/${r.data[0].id}`);
        setActivePlan(plan.data);
      }
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const approvePlan = async () => {
    if (!activePlan || approving) return;
    setApproving(true);
    try {
      await axios.put(`${API}/meal-plans/${activePlan.id}/approve`);
      setActivePlan(p => ({ ...p, status: 'approved' }));
      addToast('Meal plan approved', 'success');
    } catch {
      addToast('Failed to approve plan', 'error');
    }
    setApproving(false);
  };

  const generateGrocery = async () => {
    if (!activePlan || generating) return;
    setGenerating(true);
    try {
      await axios.post(`${API}/grocery-lists/${activePlan.id}/generate`);
      addToast('Grocery list generated', 'success');
    } catch {
      addToast('Failed to generate grocery list', 'error');
    }
    setGenerating(false);
  };

  if (loading) {
    return (
      <div className="meal-plan-screen">
        <div className="skeleton skeleton-title" style={{ marginBottom: 28 }} />
        <div className="skeleton" style={{ height: 400, borderRadius: 12 }} />
      </div>
    );
  }

  if (!activePlan) {
    return (
      <div className="meal-plan-screen">
        <div className="screen-header">
          <div className="screen-title">Weekly Meal Plan</div>
        </div>
        <div className="empty-state">
          <div className="empty-icon"><Icon name="CalendarDays" size={22} /></div>
          <div className="empty-title">No meal plan yet</div>
          <div className="empty-sub">Ask the AI Planner to create a meal plan for the week.</div>
        </div>
      </div>
    );
  }

  const meals = activePlan.meals || {};

  // Compute dates for each day (starting Monday of this week)
  const today = new Date();
  const dayOfWeek = today.getDay(); // 0=Sun, 1=Mon,...
  const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
  const monday = new Date(today);
  monday.setDate(today.getDate() + mondayOffset);

  const dayDates = DAYS.map((_, i) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });

  return (
    <div className="meal-plan-screen">
      <div className="meal-plan-toolbar">
        <div className="meal-plan-info">
          <div className="week-label">Week of {activePlan.week_start}</div>
          <span className={`status-badge ${activePlan.status || 'planning'}`}>
            {activePlan.status === 'approved' && <Icon name="Check" size={11} />}
            {activePlan.status || 'Planning'}
          </span>
        </div>
        <div className="toolbar-actions">
          <button
            className="btn btn-ghost btn-sm"
            onClick={generateGrocery}
            disabled={generating}
          >
            {generating ? (
              <span className="spinner" style={{ width: 12, height: 12, borderWidth: 2 }} />
            ) : (
              <Icon name="ShoppingCart" size={13} />
            )}
            Generate Grocery List
          </button>
          <button
            className="btn btn-primary btn-sm"
            onClick={approvePlan}
            disabled={approving || activePlan.status === 'approved'}
          >
            {activePlan.status === 'approved' ? (
              <><Icon name="CheckCircle" size={13} /> Approved</>
            ) : approving ? (
              <><span className="spinner" style={{ width: 12, height: 12, borderWidth: 2 }} /> Approving...</>
            ) : (
              <><Icon name="Check" size={13} /> Approve Plan</>
            )}
          </button>
        </div>
      </div>

      <div className="week-grid">
        {/* Header row */}
        <div className="grid-corner" />
        {DAYS.map((day, i) => (
          <div key={day} className="grid-day-header">
            <div className="grid-day-name">{day.slice(0, 3)}</div>
            <div className="grid-day-date">{dayDates[i]}</div>
          </div>
        ))}

        {/* Meal rows */}
        {MEAL_TYPES.map((mealType, rowIdx) => (
          <div key={mealType} className="grid-row" style={{ display: 'contents' }}>
            <div className={`grid-meal-label ${rowIdx === MEAL_TYPES.length - 1 ? '' : ''}`}>
              <div className="meal-label-text">{mealType}</div>
            </div>
            {DAYS.map(day => (
              <div key={day} className="grid-cell">
                <div className={`cell-meal-name ${!meals[day]?.[mealType] ? 'empty' : ''}`}>
                  {meals[day]?.[mealType] || 'Not set'}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ===================================================================
   GROCERY SCREEN
   =================================================================== */
const CATEGORY_ICONS = {
  grains: 'Package', produce: 'Sparkles', meat: 'Utensils', seafood: 'Utensils',
  'dairy/eggs': 'Package', pantry: 'Package', bakery: 'Package',
  legumes: 'Package', deli: 'Utensils', cereal: 'Package', other: 'Package',
};

function GroceryScreen() {
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState('');
  const [planId, setPlanId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [ordering, setOrdering] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [orderResult, setOrderResult] = useState(null);
  const [checkedItems, setCheckedItems] = useState({});
  const [collapsed, setCollapsed] = useState({});
  const addToast = useToast();

  const fetchGrocery = async (id) => {
    try {
      const g = await axios.get(`${API}/grocery-lists/${id}`);
      setItems(g.data.items || []);
      setStatus(g.data.status || '');
      return true;
    } catch {
      return false;
    }
  };

  useEffect(() => {
    axios.get(`${API}/meal-plans`).then(async r => {
      if (r.data.length > 0) {
        const id = r.data[0].id;
        setPlanId(id);
        const found = await fetchGrocery(id);
        if (!found) {
          try {
            const g2 = await axios.post(`${API}/grocery-lists/${id}/generate`);
            setItems(g2.data.items || []);
            setStatus(g2.data.status || '');
          } catch {}
        }
      }
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const handleGenerate = async () => {
    if (!planId || generating) return;
    setGenerating(true);
    try {
      const g = await axios.post(`${API}/grocery-lists/${planId}/generate`);
      setItems(g.data.items || []);
      setStatus(g.data.status || '');
      addToast('Grocery list generated', 'success');
    } catch {
      addToast('Failed to generate list', 'error');
    }
    setGenerating(false);
  };

  const placeOrder = async () => {
    if (!planId || ordering) return;
    setOrdering(true);
    try {
      const r = await axios.post(`${API}/grocery-lists/${planId}/order`);
      setOrderResult(r.data);
      setStatus('ordered');
      addToast('Order placed via Instamart', 'success');
    } catch {
      addToast('Order failed. Please try again.', 'error');
    }
    setOrdering(false);
  };

  const toggleCheck = (idx) => {
    setCheckedItems(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const toggleCollapse = (cat) => {
    setCollapsed(prev => ({ ...prev, [cat]: !prev[cat] }));
  };

  if (loading) {
    return (
      <div className="grocery-screen">
        <div className="skeleton skeleton-title" style={{ marginBottom: 28 }} />
        {[0,1,2].map(i => (
          <div key={i} className="skeleton" style={{ height: 60, marginBottom: 12, borderRadius: 10 }} />
        ))}
      </div>
    );
  }

  // Group by category
  const grouped = {};
  items.forEach((item, i) => {
    const cat = item.category || 'other';
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push({ ...item, _idx: i });
  });

  return (
    <div className="grocery-screen">
      <div className="grocery-toolbar">
        <div className="grocery-info">
          <div className="item-count">{items.length} items</div>
          {status && (
            <span className={`status-badge ${status === 'ordered' ? 'approved' : 'planning'}`}>
              {status === 'ordered' && <Icon name="Check" size={11} />}
              {status === 'ordered' ? 'Ordered' : status}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost btn-sm" onClick={handleGenerate} disabled={generating}>
            {generating ? (
              <span className="spinner" style={{ width: 12, height: 12, borderWidth: 2 }} />
            ) : (
              <Icon name="RefreshCw" size={13} />
            )}
            Generate List
          </button>
          <button
            className="btn btn-accent btn-sm"
            onClick={placeOrder}
            disabled={ordering || status === 'ordered'}
          >
            {ordering ? (
              <span className="spinner" style={{ width: 12, height: 12, borderWidth: 2, borderTopColor: '#fff' }} />
            ) : (
              <Icon name="ShoppingCart" size={13} />
            )}
            {status === 'ordered' ? 'Ordered' : 'Simulate Instamart Order'}
            {status === 'ordered' && (
              <span style={{
                background: 'rgba(255,255,255,0.25)',
                fontSize: 9,
                padding: '1px 5px',
                borderRadius: 8,
                fontWeight: 700,
              }}>Simulated</span>
            )}
          </button>
        </div>
      </div>

      {items.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon"><Icon name="ShoppingCart" size={22} /></div>
          <div className="empty-title">No grocery list yet</div>
          <div className="empty-sub">Approve the meal plan and generate a grocery list to get started.</div>
        </div>
      )}

      {items.length > 0 && (
        <div className="grocery-categories">
          {Object.entries(grouped).sort().map(([cat, catItems]) => (
            <div key={cat} className="grocery-category">
              <button className="category-toggle" onClick={() => toggleCollapse(cat)}>
                <Icon name={CATEGORY_ICONS[cat] || 'Package'} size={14} />
                <span className="category-name">{cat}</span>
                <span className="category-count">{catItems.length} items</span>
                <Icon
                  name="ChevronDown"
                  size={14}
                  className={`category-chevron ${!collapsed[cat] ? 'open' : ''}`}
                />
              </button>
              {!collapsed[cat] && (
                <div className="grocery-items">
                  {catItems.map((item) => (
                    <div key={item._idx} className="grocery-item">
                      <div
                        className={`item-checkbox ${checkedItems[item._idx] ? 'checked' : ''}`}
                        onClick={() => toggleCheck(item._idx)}
                      >
                        {checkedItems[item._idx] && <Icon name="Check" size={10} strokeWidth={3} />}
                      </div>
                      <span
                        className="item-name-text"
                        style={{ textDecoration: checkedItems[item._idx] ? 'line-through' : 'none', opacity: checkedItems[item._idx] ? 0.5 : 1 }}
                      >
                        {item.name}
                      </span>
                      <span className="item-qty-badge">{item.qty} {item.unit}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Order confirmation modal */}
      {orderResult && (
        <div className="modal-overlay" onClick={() => setOrderResult(null)}>
          <div className="modal-box" onClick={e => e.stopPropagation()} style={{maxWidth: 420}}>
            {/* Header */}
            <div style={{background:'#0d7a4e',borderRadius:'12px 12px 0 0',margin:'-28px -28px 20px -28px',padding:'24px 28px',color:'#fff',textAlign:'center'}}>
              <div style={{width:48,height:48,borderRadius:'50%',background:'rgba(255,255,255,0.2)',display:'flex',alignItems:'center',justifyContent:'center',margin:'0 auto 10px'}}>
                <Icon name="CheckCircle" size={26} />
              </div>
              <div style={{fontWeight:700,fontSize:'1.15rem',letterSpacing:'.01em'}}>Order Confirmed!</div>
              <div style={{fontSize:'.82rem',opacity:.85,marginTop:3}}>Your groceries are on the way</div>
            </div>

            {/* Order ID pill */}
            <div style={{textAlign:'center',marginBottom:18}}>
              <span style={{background:'#f0faf5',border:'1px solid #b7e4ce',borderRadius:8,padding:'5px 16px',fontFamily:'monospace',fontWeight:700,fontSize:'.9rem',color:'#0d7a4e',letterSpacing:'.05em'}}>
                {orderResult.order_id}
              </span>
            </div>

            {/* Stats grid */}
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:10,marginBottom:18}}>
              {[
                {label:'Items', value: orderResult.item_count},
                {label:'Total', value: orderResult.total_cost},
                {label:'ETA', value: orderResult.estimated_delivery},
              ].map(s => (
                <div key={s.label} style={{background:'#f7f9f8',borderRadius:10,padding:'10px 8px',textAlign:'center'}}>
                  <div style={{fontWeight:700,fontSize:'1rem',color:'#111'}}>{s.value}</div>
                  <div style={{fontSize:'.72rem',color:'#888',marginTop:2}}>{s.label}</div>
                </div>
              ))}
            </div>

            {/* Delivery status bar */}
            <div style={{marginBottom:20}}>
              <div style={{display:'flex',justifyContent:'space-between',fontSize:'.73rem',color:'#888',marginBottom:5}}>
                <span>Order Placed</span><span>Picking</span><span>On the way</span><span>Delivered</span>
              </div>
              <div style={{height:5,borderRadius:3,background:'#e5e7eb',overflow:'hidden'}}>
                <div style={{height:'100%',width:'25%',background:'#0d7a4e',borderRadius:3,transition:'width .5s'}} />
              </div>
            </div>

            {/* Footer note */}
            <div style={{fontSize:'.78rem',color:'#888',textAlign:'center',marginBottom:16}}>
              You will receive an SMS update when your order is out for delivery.
            </div>

            <button className="btn btn-primary" style={{width:'100%'}} onClick={() => setOrderResult(null)}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ===================================================================
   HOUSEHOLD SCREEN
   =================================================================== */
function HouseholdScreen() {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/household`)
      .then(r => { setMembers(r.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="household-screen">
        <div className="skeleton skeleton-title" style={{ marginBottom: 28 }} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 20 }}>
          {[0,1,2,3].map(i => (
            <div key={i} className="skeleton" style={{ height: 200, borderRadius: 14 }} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="household-screen">
      <div className="screen-header">
        <div className="screen-title">Household</div>
        <div className="screen-subtitle">{members.length} members</div>
      </div>

      {members.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon"><Icon name="Users" size={22} /></div>
          <div className="empty-title">No household members</div>
          <div className="empty-sub">Add household members to personalize meal planning.</div>
        </div>
      )}

      <div className="household-grid">
        {members.map(member => (
          <div key={member.id} className="member-card">
            <div className="member-card-header">
              <div className="member-avatar">{getInitials(member.name)}</div>
              <div>
                <div className="member-name">{member.name}</div>
              </div>
            </div>

            {(member.dietary_restrictions || []).length > 0 && (
              <div className="member-section">
                <div className="member-section-label">Dietary</div>
                <div className="member-tags">
                  {(member.dietary_restrictions || []).map((r, i) => (
                    <span key={i} className="member-tag">{r}</span>
                  ))}
                </div>
              </div>
            )}

            <div className="member-section">
              <div className="member-section-label">Allergies</div>
              <div className="member-tags">
                {(member.allergies || []).length > 0 ? (
                  (member.allergies || []).map((a, i) => (
                    <span key={i} className="member-tag allergy">{a}</span>
                  ))
                ) : (
                  <span className="member-tag empty">None reported</span>
                )}
              </div>
            </div>

            {(member.preferences || []).length > 0 && (
              <div className="member-section">
                <div className="member-section-label">Preferences</div>
                <div className="member-tags">
                  {(member.preferences || []).map((p, i) => (
                    <span key={i} className="member-tag">{p}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ===================================================================
   ROOT APP
   =================================================================== */
/* ===================================================================
   ANALYTICS SCREEN
   Operational metrics: automation rate, friction points, outcomes
   =================================================================== */
function AnalyticsScreen() {
  const [data, setData] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [analyticsRes, sessionsRes] = await Promise.all([
        axios.get(`${API}/analytics`),
        axios.get(`${API}/cook-sessions`).catch(() => ({ data: [] })),
      ]);
      setData(analyticsRes.data);
      setSessions(Array.isArray(sessionsRes.data) ? sessionsRes.data : []);
    } catch {
      setData(null);
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const endSession = async (sessionId, mealName) => {
    const note = window.prompt(`What was actually cooked? (default: ${mealName})`) ?? mealName;
    if (note === null) return;
    const outcome = note.trim() || mealName;
    const followed = outcome.toLowerCase() === mealName.toLowerCase();
    try {
      await axios.post(`${API}/cook-sessions/${sessionId}/complete`, {
        outcome_meal: outcome,
        outcome_notes: followed ? "Followed the plan." : `Deviated: cooked "${outcome}" instead of "${mealName}".`,
        followed_plan: followed,
      });
      await load();
    } catch {
      alert('Failed to record outcome.');
    }
  };

  const metricCard = (label, value, sub) => (
    <div className="metric-card">
      <div className="metric-value">{value ?? '--'}</div>
      <div className="metric-label">{label}</div>
      {sub && <div className="metric-sub">{sub}</div>}
    </div>
  );

  return (
    <div className="screen-container">
      <div className="screen-header">
        <div className="screen-title">Operational Analytics</div>
        <div className="screen-subtitle">What actually happened in the kitchen vs. what was planned</div>
      </div>

      {loading ? (
        <div className="empty-state"><div className="spinner" /><div className="empty-title">Loading...</div></div>
      ) : !data ? (
        <div className="empty-state"><div className="empty-title">Could not load analytics</div></div>
      ) : data.completed_sessions === 0 ? (
        <div className="empty-state">
          <div className="empty-icon"><Icon name="BarChart2" size={22} /></div>
          <div className="empty-title">No data yet</div>
          <div className="empty-sub">Complete a cook session to start tracking operational metrics.</div>
        </div>
      ) : (
        <>
          <div className="metrics-grid">
            {metricCard("Automation Rate", `${data.automation_rate_pct}%`, "sessions with zero human intervention")}
            {metricCard("Sessions Completed", data.completed_sessions)}
            {metricCard("Avg Interventions / Session", data.avg_human_interventions, "approval requests raised")}
            {metricCard("Plan Deviations", data.sessions_deviated_from_plan, "meals cooked differently from plan")}
          </div>

          {data.insight && (
            <div className="insight-banner">
              <Icon name="Lightbulb" size={15} />
              <span>{data.insight}</span>
            </div>
          )}

          {data.common_missing_ingredients?.length > 0 && (
            <div className="section-block">
              <div className="section-label">Most Common Missing Ingredients</div>
              <div className="tag-row">
                {data.common_missing_ingredients.map((item, i) => (
                  <span key={i} className="allergy-tag">{item.ingredient} ({item.count}x)</span>
                ))}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8 }}>
                These happen often enough to consider keeping them stocked or updating the default grocery order.
              </div>
            </div>
          )}
        </>
      )}

      {sessions.filter(s => s.status === 'active').length > 0 && (
        <div className="section-block" style={{ marginTop: 24 }}>
          <div className="section-label">Active Sessions: Record Outcome</div>
          {sessions.filter(s => s.status === 'active').map(s => (
            <div key={s.id} className="session-outcome-row">
              <div>
                <strong>{s.meal_name}</strong>
                <span style={{ color: 'var(--text-secondary)', marginLeft: 8 }}>{s.day}</span>
              </div>
              <button className="btn btn-primary btn-sm" onClick={() => endSession(s.id, s.meal_name)}>
                <Icon name="CheckCircle" size={13} /> End Session
              </button>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 16 }}>
        <button className="btn btn-ghost btn-sm" onClick={load}>
          <Icon name="RefreshCw" size={13} /> Refresh
        </button>
      </div>
    </div>
  );
}

/* ===================================================================
   COLD START SPLASH
   =================================================================== */
function ColdStartBanner() {
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  const [state, setState] = useState('checking'); // checking | slow | ready | error
  const [progress, setProgress] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (isLocal) { setState('ready'); setDone(true); return; }

    const slowTimer = setTimeout(() => setState('slow'), 2500);

    axios.get(`${API}/household`, { timeout: 90000 })
      .then(() => {
        clearTimeout(slowTimer);
        setProgress(100);
        setTimeout(() => { setState('ready'); setDone(true); }, 600);
      })
      .catch(() => {
        clearTimeout(slowTimer);
        setState('error');
      });

    return () => clearTimeout(slowTimer);
  }, []);

  // Animate progress bar over ~55s (typical Render cold start)
  useEffect(() => {
    if (state !== 'slow') return;
    const interval = setInterval(() => {
      setElapsed(e => {
        const next = e + 1;
        // Ease toward 90%, never reach 100 until ready
        setProgress(Math.min(90, Math.round(90 * (1 - Math.exp(-next / 35)))));
        return next;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [state]);

  if (done || state === 'ready') return null;

  const MESSAGES = [
    'Warming up the kitchen...',
    'Fetching household profiles...',
    'Loading meal plans...',
    'Almost there...',
    'Just a few more seconds...',
  ];
  const msgIdx = Math.min(Math.floor(elapsed / 11), MESSAGES.length - 1);

  if (state === 'error') {
    return (
      <div className="cold-splash">
        <div className="cold-splash-box">
          <div className="cold-splash-icon">⚠️</div>
          <div className="cold-splash-title">Could not reach the server</div>
          <div className="cold-splash-sub">Wait 60 seconds then refresh the page.</div>
          <button className="btn btn-primary" style={{ marginTop: 20 }} onClick={() => window.location.reload()}>
            Refresh
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="cold-splash">
      <div className="cold-splash-box">
        <div className="cold-splash-logo">🍳</div>
        <div className="cold-splash-title">Kitchen Agent</div>
        <div className="cold-splash-sub">
          {state === 'checking' ? 'Connecting...' : MESSAGES[msgIdx]}
        </div>
        <div className="cold-splash-bar-track">
          <div className="cold-splash-bar-fill" style={{ width: `${progress}%` }} />
        </div>
        <div className="cold-splash-note">
          {state === 'slow'
            ? `Server is waking up from sleep (${elapsed}s) — Render free tier`
            : 'Starting up...'}
        </div>
      </div>
    </div>
  );
}

/* ===================================================================
   SETTINGS SCREEN
   =================================================================== */
function SettingsScreen() {
  const household = [
    { name: 'Sarah', role: 'Adult', restrictions: 'Vegetarian', allergies: 'None' },
    { name: 'Mike',  role: 'Adult', restrictions: 'None',       allergies: 'None' },
    { name: 'Emma',  role: 'Child', restrictions: 'Kid-friendly', allergies: 'Peanuts (STRICT)' },
    { name: 'George',role: 'Senior',restrictions: 'Soft foods, low sugar', allergies: 'None' },
  ];
  return (
    <div className="screen-content">
      <div className="screen-header">
        <div>
          <div className="screen-title">Settings</div>
          <div className="screen-subtitle">Household preferences and configuration</div>
        </div>
      </div>

      <div style={{display:'grid',gap:24,maxWidth:700}}>
        {/* Household members */}
        <div className="section-block">
          <div style={{fontWeight:700,fontSize:'.95rem',marginBottom:14,color:'var(--text-primary)'}}>Household Members</div>
          {household.map(m => (
            <div key={m.name} style={{display:'flex',alignItems:'center',gap:14,padding:'12px 0',borderBottom:'1px solid var(--border)'}}>
              <div style={{width:38,height:38,borderRadius:'50%',background:'var(--primary-light)',display:'flex',alignItems:'center',justifyContent:'center',fontWeight:700,color:'var(--primary)',fontSize:'.9rem',flexShrink:0}}>
                {m.name[0]}
              </div>
              <div style={{flex:1}}>
                <div style={{fontWeight:600,fontSize:'.88rem'}}>{m.name} <span style={{fontWeight:400,color:'var(--text-muted)',fontSize:'.8rem'}}>({m.role})</span></div>
                <div style={{fontSize:'.78rem',color:'var(--text-muted)',marginTop:2}}>
                  {m.restrictions !== 'None' && <span style={{marginRight:10}}>Diet: {m.restrictions}</span>}
                  {m.allergies !== 'None' && <span style={{color:'#dc2626',fontWeight:600}}>Allergy: {m.allergies}</span>}
                  {m.restrictions === 'None' && m.allergies === 'None' && <span>No restrictions</span>}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* App info */}
        <div className="section-block">
          <div style={{fontWeight:700,fontSize:'.95rem',marginBottom:14,color:'var(--text-primary)'}}>About</div>
          {[
            ['Version', '1.0.0'],
            ['Backend', 'FastAPI + SQLite on Render'],
            ['AI Model', 'Gemini 3.8 Flash'],
            ['Voice', 'Orpheus (edge-tts fallback)'],
          ].map(([k,v]) => (
            <div key={k} style={{display:'flex',justifyContent:'space-between',padding:'8px 0',borderBottom:'1px solid var(--border)',fontSize:'.85rem'}}>
              <span style={{color:'var(--text-muted)'}}>{k}</span>
              <span style={{fontWeight:500}}>{v}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function App() {
  const [activeScreen, setActiveScreen] = useState('overview');

  const navigate = (screen) => setActiveScreen(screen);

  const renderScreen = () => {
    switch (activeScreen) {
      case 'overview':  return <OverviewScreen onNavigate={navigate} />;
      case 'planner':   return <PlannerScreen />;
      case 'cook':      return <CookScreen />;
      case 'mealplan':  return <MealPlanScreen />;
      case 'grocery':   return <GroceryScreen />;
      case 'household':  return <HouseholdScreen />;
      case 'analytics':  return <AnalyticsScreen />;
      case 'settings':   return <SettingsScreen />;
      default:           return <OverviewScreen onNavigate={navigate} />;
    }
  };

  return (
    <ToastProvider>
      <ColdStartBanner />
      <div className="app-shell">
        <Sidebar activeScreen={activeScreen} onNavigate={navigate} />
        <main className="main-content">
          {renderScreen()}
        </main>
        <MobileNav activeScreen={activeScreen} onNavigate={navigate} />
      </div>
    </ToastProvider>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

