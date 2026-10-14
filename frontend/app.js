/* =============================================================
   Kitchen Agent — Frontend Application
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

  const startRecording = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Your browser does not support voice input. Try Chrome.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      setVoiceState('processing');
      onResult(transcript);
      setTimeout(() => setVoiceState('idle'), 400);
    };

    recognition.onerror = () => setVoiceState('idle');
    recognition.onend = () => setVoiceState(s => s === 'listening' ? 'idle' : s);

    recognitionRef.current = recognition;
    recognition.start();
    setVoiceState('listening');
  }, [onResult]);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) recognitionRef.current.stop();
    setVoiceState('idle');
  }, []);

  const toggle = useCallback(() => {
    if (voiceState === 'listening') stopRecording();
    else startRecording();
  }, [voiceState, startRecording, stopRecording]);

  return { voiceState, toggle };
}

function speak(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  utterance.pitch = 1.05;
  window.speechSynthesis.speak(utterance);
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
function ChatMessage({ message }) {
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
    onSend(chip);
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
          {chips.map(chip => (
            <button key={chip} className="chip" onClick={() => handleChip(chip)}>
              {chip}
            </button>
          ))}
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
  { id: 'overview',  label: 'Overview',         icon: 'LayoutDashboard' },
  { id: 'planner',   label: 'AI Meal Planner',   icon: 'MessageSquare'  },
  { id: 'cook',      label: 'Cook Assistant',    icon: 'ChefHat'        },
  { id: 'mealplan',  label: 'Weekly Meal Plan',  icon: 'CalendarDays'   },
  { id: 'grocery',   label: 'Grocery List',      icon: 'ShoppingCart'   },
  { id: 'household', label: 'Household',         icon: 'Users'          },
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
        <button className="nav-item" style={{ width: '100%' }}>
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

  if (loading) {
    return (
      <div className="screen">
        <div className="skeleton skeleton-title" style={{ marginBottom: 24, height: 32, width: '40%' }} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 32 }}>
          {[0,1,2].map(i => <div key={i} className="skeleton skeleton-card" />)}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
          {[0,1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 72 }} />)}
        </div>
      </div>
    );
  }

  return (
    <div className="screen">
      {/* Greeting */}
      <div className="overview-greeting">
        <div className="greeting-time">{getGreeting()}</div>
        <div className="greeting-sub">Here is what is happening in your kitchen today.</div>
        <div className="greeting-date">{getDateString()}</div>
      </div>

      {/* Today in the Kitchen */}
      <div className="section-label">Today in the Kitchen</div>
      <div className="today-meals">
        {['breakfast', 'lunch', 'dinner'].map(mealType => {
          const name = todayMeals[mealType];
          return (
            <div className="meal-today-card" key={mealType}>
              <div className="meal-today-type">{mealType}</div>
              <div className={`meal-today-name ${!name ? 'empty' : ''}`}>
                {name || 'Not planned'}
              </div>
              {name && (
                <div>
                  <div className="dietary-tags">
                    {members.flatMap(m => m.dietary_restrictions || []).slice(0, 2).map((tag, i) => (
                      <span key={i} className="dietary-tag">{tag}</span>
                    ))}
                  </div>
                  <span className="meal-status-badge planned">
                    <Icon name="Check" size={11} />
                    Planned
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Stats */}
      <div className="section-label">Status</div>
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-label">Meals Planned</div>
          <div className="stat-value">{totalMeals}</div>
          <div className="stat-sub">This week</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Week Status</div>
          <div className="stat-value" style={{ fontSize: 15, marginTop: 4, textTransform: 'capitalize' }}>
            {activePlan?.status || 'No plan'}
          </div>
          <div className="stat-sub">{activePlan?.week_start || 'No plan active'}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Grocery Status</div>
          <div className="stat-value" style={{ fontSize: 15, marginTop: 4, textTransform: 'capitalize' }}>
            {groceryStatus || 'Pending'}
          </div>
          <div className="stat-sub">
            {groceryStatus === 'ordered' ? 'Order placed' : 'Tap to generate'}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Members</div>
          <div className="stat-value">{members.length}</div>
          <div className="stat-sub">Household members</div>
        </div>
      </div>

      {/* Needs Attention */}
      {activePlan && activePlan.status !== 'approved' && (
        <div>
          <div className="section-label">Needs Attention</div>
          <div className="attention-card">
            <div className="attention-icon">
              <Icon name="AlertTriangle" size={18} />
            </div>
            <div className="attention-text">
              <div className="attention-title">Review and approve this week's meal plan</div>
              <div className="attention-desc">
                The plan for the week of {activePlan.week_start} is ready and waiting for your approval.
              </div>
            </div>
            <button className="btn btn-primary btn-sm" onClick={handleApprove}>
              <Icon name="Check" size={13} />
              Approve Plan
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ===================================================================
   PLANNER SCREEN
   =================================================================== */
const PLANNER_CHIPS = [
  'Plan next week',
  'Make dinners lighter',
  'Check restrictions',
  'Replace a meal',
];

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
      const errMsg = err.response?.data?.detail || 'Connection error. Is the backend running?';
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${errMsg}`, time: new Date().toISOString() }]);
      addToast('Failed to send message', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-screen">
      <div className="chat-screen-header" style={{ padding: '24px 40px 18px' }}>
        <div className="chat-screen-title">Kitchen Planner</div>
        <div className="chat-screen-subtitle">Ready to plan your week</div>
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
          <ChatMessage key={i} message={m} />
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
      const errMsg = err.response?.data?.detail || 'Connection error';
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${errMsg}`, time: new Date().toISOString() }]);
      addToast('Failed to send message', 'error');
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
              <ChatMessage key={i} message={m} />
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
          <div className="modal-box" onClick={e => e.stopPropagation()}>
            <div className="modal-icon">
              <Icon name="CheckCircle" size={24} />
            </div>
            <div className="modal-title">Order Confirmed</div>
            <div className="modal-body">{orderResult.message}</div>
            {orderResult.order_id && (
              <div className="modal-order-id">{orderResult.order_id}</div>
            )}
            <button className="btn btn-primary" onClick={() => setOrderResult(null)}>
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
      case 'household': return <HouseholdScreen />;
      default:          return <OverviewScreen onNavigate={navigate} />;
    }
  };

  return (
    <ToastProvider>
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

