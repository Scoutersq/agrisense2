import { useEffect, useState } from 'react'
import {
  Activity,
  Bell,
  ChevronDown,
  CloudSun,
  LayoutDashboard,
  Leaf,
  Menu,
  Microscope,
  Sprout,
  Tractor,
  TrendingUp,
  Upload,
  Image as ImageIcon,
  Check,
  AlertTriangle,
  UserRound,
  Wheat,
  X,
} from 'lucide-react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const navItems = [
  { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
  { id: 'disease', label: 'Disease Detection', icon: Microscope },
  { id: 'recommend', label: 'Crop Advisory', icon: Sprout },
  { id: 'yield', label: 'Yield Forecast', icon: TrendingUp },
  { id: 'irrigation', label: 'Smart Farming', icon: Tractor },
]

const trendData = [
  { month: 'Jan', yield: 18 },
  { month: 'Feb', yield: 22 },
  { month: 'Mar', yield: 20 },
  { month: 'Apr', yield: 27 },
  { month: 'May', yield: 25 },
  { month: 'Jun', yield: 32 },
  { month: 'Jul', yield: 29 },
  { month: 'Aug', yield: 36 },
]

function Brand({ compact = false }) {
  return (
    <div className="brand">
      <div className="brand-mark"><Leaf size={compact ? 20 : 22} strokeWidth={2.4} /></div>
      {!compact && (
        <div>
          <strong>AgriSense</strong>
          <span>AI</span>
        </div>
      )}
    </div>
  )
}

function Sidebar({ active, setActive, open, setOpen }) {
  return (
    <>
      {open && <button className="sidebar-backdrop" aria-label="Close menu" onClick={() => setOpen(false)} />}
      <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
        <div className="sidebar-top">
          <Brand />
          <button className="icon-button sidebar-close" onClick={() => setOpen(false)} aria-label="Close menu">
            <X size={20} />
          </button>
        </div>
        <nav className="nav-list" aria-label="Primary navigation">
          <span className="nav-label">Workspace</span>
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <button
                key={item.id}
                className={`nav-item ${active === item.id ? 'active' : ''}`}
                onClick={() => {
                  setActive(item.id)
                  setOpen(false)
                }}
              >
                <Icon size={19} strokeWidth={2} />
                <span>{item.label}</span>
              </button>
            )
          })}
        </nav>
        <div className="sidebar-footer">
          <div className="weather-mini">
            <div className="weather-icon"><CloudSun size={21} /></div>
            <div>
              <strong>28°C</strong>
              <span>Partly cloudy</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}

function Header({ setOpen, user, onLogout }) {
  return (
    <header className="header">
      <button className="icon-button menu-button" onClick={() => setOpen(true)} aria-label="Open menu">
        <Menu size={21} />
      </button>
      <div className="header-actions">
        <button className="icon-button notification-button" aria-label="Notifications">
          <Bell size={20} />
          <span className="notification-dot" />
        </button>
        <button className="profile-button" aria-label="Open profile menu" onClick={onLogout} title="Sign out">
          <div className="avatar">{user?.name?.split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase() || 'FA'}</div>
          <div className="profile-copy">
            <strong>{user?.name || 'Farmer account'}</strong>
            <span>Farmer</span>
          </div>
          <ChevronDown size={16} />
        </button>
      </div>
    </header>
  )
}

function StatCard({ icon: Icon, tone, label, value, detail }) {
  return (
    <article className="stat-card">
      <div className={`stat-icon ${tone}`}><Icon size={21} /></div>
      <div className="stat-copy">
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </article>
  )
}

function Dashboard({ user, refreshKey }) {
  const [overview, setOverview] = useState({
    disease_analyses: 0,
    crop_recommendations: 0,
    yield_forecasts: 0,
    recent_disease_analyses: [],
  })

  function loadOverview() {
    const token = localStorage.getItem('agrisense_token')
    if (!token) return
    fetch('http://127.0.0.1:8000/api/analytics/overview', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        if (!response.ok) return null
        return response.json()
      })
      .then((data) => {
        if (data) setOverview(data)
      })
      .catch(() => {})
  }

  useEffect(() => {
    loadOverview()
    window.addEventListener('agrisense-history-updated', loadOverview)
    return () => window.removeEventListener('agrisense-history-updated', loadOverview)
  }, [refreshKey])

  return (
    <main className="content">
      <section className="welcome-row">
        <div>
          <p className="eyebrow">Tuesday, 24 November</p>
          <h1>Good morning, {user?.name?.split(' ')[0] || 'Farmer'}</h1>
          <p className="welcome-copy">Here is a summary of your farm activity.</p>
        </div>
        <button className="primary-button"><Leaf size={17} /> New analysis</button>
      </section>

      <section className="stats-grid" aria-label="Farm summary">
        <StatCard icon={Microscope} tone="green" label="Disease analyses" value={overview.disease_analyses} detail={overview.disease_analyses ? "Saved predictions" : "No analyses yet"} />
        <StatCard icon={Sprout} tone="amber" label="Crop plans" value={overview.crop_recommendations} detail={overview.crop_recommendations ? "Saved recommendations" : "No recommendations yet"} />
        <StatCard icon={TrendingUp} tone="blue" label="Yield forecasts" value={overview.yield_forecasts} detail="No forecasts yet" />
        <StatCard icon={Activity} tone="purple" label="Farm health" value={overview.disease_analyses ? "Monitored" : "Not set"} detail={overview.disease_analyses ? "Based on saved analyses" : "Add field details"} />
      </section>

      <section className="dashboard-grid">
        <article className="panel chart-panel">
          <div className="panel-heading">
            <div>
              <span className="panel-kicker">Overview</span>
              <h2>Farm productivity</h2>
            </div>
            <button className="select-button">This year <ChevronDown size={14} /></button>
          </div>
          <div className="dashboard-empty">
            <TrendingUp size={26} />
            <strong>No productivity data</strong>
            <span>Forecasts and historical trends will appear after farm data is available.</span>
          </div>
        </article>

        <article className="panel field-panel">
          <div className="panel-heading">
            <div>
              <span className="panel-kicker">This season</span>
              <h2>Field status</h2>
            </div>
            <button className="text-button">View all</button>
          </div>
          {overview.recent_disease_analyses.length ? (
            <div className="recent-list">
              {overview.recent_disease_analyses.map((item, index) => (
                <div className="field-row" key={`${item.created_at}-${index}`}>
                  {item.thumbnail_base64 ? (
                    <img
                      className="history-thumbnail"
                      src={`data:image/jpeg;base64,${item.thumbnail_base64}`}
                      alt={item.disease_name || item.predicted_class}
                      onError={(event) => {
                        event.currentTarget.style.display = 'none'
                      }}
                    />
                  ) : (
                    <div className="crop-icon green"><Microscope size={19} /></div>
                  )}
                  <div className="field-copy">
                    <strong>{item.disease_name || item.predicted_class}</strong>
                    <span>{item.image_name || "Crop image"} · {item.confidence ? `${(item.confidence * 100).toFixed(1)}%` : "Analysis"}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="dashboard-empty compact">
              <Sprout size={24} />
              <strong>No recent analyses</strong>
              <span>Upload a crop image to begin its history.</span>
            </div>
          )}
        </article>
      </section>

      <section className="quick-grid">
        {[
          { icon: Microscope, title: 'Check crop disease', text: 'Upload a leaf photo for assisted identification', tone: 'green' },
          { icon: Sprout, title: 'Find a suitable crop', text: 'Use soil and climate inputs for an ML recommendation', tone: 'amber' },
          { icon: TrendingUp, title: 'Estimate crop yield', text: 'Get a data-based forecast and uncertainty context', tone: 'blue' },
        ].map((item) => (
          <button className="quick-card" key={item.title}>
            <div className={`quick-icon ${item.tone}`}><item.icon size={21} /></div>
            <div>
              <strong>{item.title}</strong>
              <span>{item.text}</span>
            </div>
          </button>
        ))}
      </section>
    </main>
  )
}

function DiseasePage() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  function selectFile(event) {
    const selected = event.target.files?.[0]
    setResult(null)
    setError('')
    if (!selected) return
    if (!['image/jpeg', 'image/png'].includes(selected.type)) {
      setError('Please choose a JPG or PNG image.')
      return
    }
    if (selected.size > 10 * 1024 * 1024) {
      setError('The image must be 10 MB or smaller.')
      return
    }
    setFile(selected)
    setPreview(URL.createObjectURL(selected))
  }

  async function analyze() {
    if (!file) return
    setLoading(true)
    setError('')
    setResult(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const response = await fetch('http://127.0.0.1:8000/api/disease/predict', {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('agrisense_token')}` },
        body: form,
      })
      const data = await response.json()
      if (response.status === 401) {
        localStorage.removeItem('agrisense_token')
        localStorage.removeItem('agrisense_user')
        throw new Error('Your session has expired or is invalid. Please sign in again.')
      }
      if (!response.ok) throw new Error(data.detail || 'Unable to analyze the image')
      setResult(data)
      window.dispatchEvent(new Event('agrisense-history-updated'))
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="content">
      <section className="page-heading">
        <div className="page-heading-icon"><Microscope size={22} /></div>
        <div>
          <h1>Crop disease detection</h1>
          <p>Upload a clear leaf image for AI-assisted screening</p>
        </div>
      </section>
      <section className="disease-grid">
        <div className="panel upload-panel">
          <div className="upload-preview">
            {preview ? (
              <img src={preview} alt="Selected crop leaf preview" />
            ) : (
              <div className="upload-placeholder">
                <ImageIcon size={34} />
                <strong>Upload a crop image</strong>
                <span>JPG or PNG, up to 10 MB</span>
              </div>
            )}
          </div>
          <label className="upload-button">
            <Upload size={17} />
            <span>{file ? 'Choose another image' : 'Select image'}</span>
            <input type="file" accept="image/jpeg,image/png" onChange={selectFile} />
          </label>
          <button className="analyze-button" onClick={analyze} disabled={!file || loading}>
            {loading ? 'Analyzing…' : 'Analyze crop image'}
          </button>
          {error && <div className="module-alert error"><AlertTriangle size={16} />{error}</div>}
          {result && (
            <div className="module-alert success">
              <Check size={16} />
              Analysis completed
            </div>
          )}
        </div>
        <div className="panel result-panel">
          <span className="panel-kicker">Analysis result</span>
          <h2>{result ? result.disease_name : 'Awaiting image'}</h2>
          {result ? (
            <>
              <div className="disease-confidence">
                <strong>{result.confidence_percent}% confidence</strong>
                <span>AI-assisted prediction</span>
              </div>
              <div className="alternative-list disease-predictions">
                {result.top_predictions.map((item) => (
                  <div key={item.class_name}>
                    <span>{item.disease_name || item.class_name}</span>
                    <strong>{item.confidence_percent}%</strong>
                  </div>
                ))}
              </div>
              <div className="disease-guidance">
                <strong>General guidance</strong>
                <span>{result.guidance}</span>
              </div>
            </>
          ) : (
            <div className="result-placeholder">
              <Microscope size={30} />
              <p>Upload a clear image of a single affected leaf. Avoid blurry, dark, or heavily edited photos.</p>
            </div>
          )}
          <div className="model-disclaimer">
            <strong>Medical and agricultural caution</strong>
            <span>Image classification can assist screening but cannot confirm a disease without field inspection or laboratory testing.</span>
          </div>
        </div>
      </section>
    </main>
  )
}

function CropRecommendationPage() {
  const [form, setForm] = useState({ nitrogen: '', phosphorus: '', potassium: '', temperature: '', humidity: '', ph: '', rainfall: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  function update(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  async function submit(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    const body = {
      nitrogen: Number(form.nitrogen),
      phosphorus: Number(form.phosphorus),
      potassium: Number(form.potassium),
      temperature: Number(form.temperature),
      humidity: Number(form.humidity),
      ph: Number(form.ph),
      rainfall: Number(form.rainfall),
    }
    try {
      const response = await fetch('http://127.0.0.1:8000/api/crops/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('agrisense_token')}`,
        },
        body: JSON.stringify(body),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Unable to generate recommendation')
      setResult(data)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="content">
      <section className="page-heading">
        <div className="page-heading-icon"><Sprout size={22} /></div>
        <div>
          <h1>Crop advisory</h1>
          <p>Random Forest model trained on a public crop dataset</p>
        </div>
      </section>
      <section className="crop-grid">
        <form className="panel crop-form" onSubmit={submit}>
          <h2>Soil and climate inputs</h2>
          {[
            ['nitrogen', 'Nitrogen (N)', '0–300'],
            ['phosphorus', 'Phosphorus (P)', '0–300'],
            ['potassium', 'Potassium (K)', '0–300'],
            ['temperature', 'Temperature (°C)', '-20–60'],
            ['humidity', 'Humidity (%)', '0–100'],
            ['ph', 'Soil pH', '0–14'],
            ['rainfall', 'Rainfall (mm)', '0–1000'],
          ].map(([name, label, hint]) => (
            <label key={name}>
              <span>{label}</span>
              <input name={name} value={form[name]} onChange={update} type="number" step="any" placeholder={hint} required />
            </label>
          ))}
          {error && <div className="module-alert error"><AlertTriangle size={16} />{error}</div>}
          <button className="analyze-button" type="submit" disabled={loading}>{loading ? 'Evaluating…' : 'Recommend crop'}</button>
        </form>
        <div className="panel result-panel crop-result">
          <span className="panel-kicker">Model result</span>
          {result ? (
            <>
              <h2>{result.recommended_crop}</h2>
              <div className="alternative-list">
                {result.alternatives.map((item) => (
                  <div key={item.crop}><span>{item.crop}</span><strong>{(item.probability * 100).toFixed(1)}%</strong></div>
                ))}
              </div>
            </>
          ) : (
            <>
              <h2>No recommendation yet</h2>
              <div className="result-placeholder">
                <Sprout size={30} />
                <p>Enter soil and climate measurements to receive model-generated alternatives.</p>
              </div>
            </>
          )}
          <div className="model-disclaimer">
            <strong>Data limitation</strong>
            <span>This result is a statistical recommendation, not a guarantee of crop success or local suitability.</span>
          </div>
        </div>
      </section>
    </main>
  )
}

function ModulePage({ title, subtitle, icon: Icon }) {
  return (
    <main className="content">
      <section className="page-heading">
        <div className="page-heading-icon"><Icon size={22} /></div>
        <div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
      </section>
      <section className="panel empty-state">
        <Icon size={32} />
        <h2>Workspace ready</h2>
        <p>This module will be connected to the trained model and tested API in the next implementation phase.</p>
      </section>
    </main>
  )
}

function AuthPage({ onAuthenticated }) {
  const [mode, setMode] = useState('login')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({ name: '', email: '', password: '', state: '' })

  function updateField(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  async function submit(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/register'
    const body = mode === 'login'
      ? { email: form.email, password: form.password }
      : form
    try {
      const response = await fetch(`http://127.0.0.1:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Unable to continue')
      localStorage.setItem('agrisense_token', data.access_token)
      localStorage.setItem('agrisense_user', JSON.stringify(data.user))
      onAuthenticated(data.user)
    } catch (requestError) {
      setError(requestError.message === 'Failed to fetch'
        ? 'The backend is not reachable. Start the FastAPI server and try again.'
        : requestError.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-brand-panel">
        <div className="auth-brand"><Brand /></div>
        <div className="auth-brand-copy">
          <span>Intelligent crop decisions</span>
          <h2>Better field decisions begin with reliable information.</h2>
          <p>One workspace for crop analysis, yield forecasting, soil planning, and farm records.</p>
        </div>
      </section>
      <section className="auth-form-panel">
        <div className="auth-form-wrap">
          <div className="auth-tabs" role="tablist">
            <button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Sign in</button>
            <button className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>Create account</button>
          </div>
          <div className="auth-heading">
            <p className="eyebrow">Secure farmer account</p>
            <h1>{mode === 'login' ? 'Welcome back' : 'Create your workspace'}</h1>
            <span>{mode === 'login' ? 'Sign in to view your farm overview.' : 'Set up a profile for your agricultural operations.'}</span>
          </div>
          <form onSubmit={submit} className="auth-form">
            {mode === 'register' && (
              <label>
                <span>Full name</span>
                <input name="name" value={form.name} onChange={updateField} placeholder="Enter your name" minLength={2} required />
              </label>
            )}
            <label>
              <span>Email address</span>
              <input name="email" type="email" value={form.email} onChange={updateField} placeholder="you@example.com" required />
            </label>
            {mode === 'register' && (
              <label>
                <span>State</span>
                <input name="state" value={form.state} onChange={updateField} placeholder="For example, Maharashtra" />
              </label>
            )}
            <label>
              <span>Password</span>
              <input name="password" type="password" value={form.password} onChange={updateField} placeholder={mode === 'login' ? 'Enter your password' : 'At least 8 characters'} minLength={mode === 'register' ? 8 : 1} required />
            </label>
            {error && <div className="auth-error" role="alert">{error}</div>}
            <button className="auth-submit" type="submit" disabled={loading}>
              {loading ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>
        </div>
      </section>
    </main>
  )
}

export default function App() {
  const [active, setActive] = useState('dashboard')
  const [menuOpen, setMenuOpen] = useState(false)
  const [token, setToken] = useState(() => localStorage.getItem('agrisense_token'))
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('agrisense_user')) } catch { return null }
  })

  useEffect(() => {
    const storedToken = localStorage.getItem('agrisense_token')
    if (!storedToken) return

    fetch('http://127.0.0.1:8000/api/auth/me', {
      headers: { Authorization: `Bearer ${storedToken}` },
    })
      .then(async (response) => {
        if (!response.ok) throw new Error('invalid session')
        const verifiedUser = await response.json()
        setUser(verifiedUser)
        localStorage.setItem('agrisense_user', JSON.stringify(verifiedUser))
      })
      .catch(() => {
        localStorage.removeItem('agrisense_token')
        localStorage.removeItem('agrisense_user')
        setToken(null)
        setUser(null)
      })
  }, [])

  function logout() {
    localStorage.removeItem('agrisense_token')
    localStorage.removeItem('agrisense_user')
    setToken(null)
    setUser(null)
  }

  if (!token) {
    return <AuthPage onAuthenticated={(authenticatedUser) => {
      setToken(localStorage.getItem('agrisense_token'))
      setUser(authenticatedUser)
    }} />
  }

  const pages = {
    dashboard: <Dashboard user={user} refreshKey={active === 'dashboard' ? 'active' : 'inactive'} />,
    recommend: <CropRecommendationPage />,
    yield: <ModulePage title="Yield forecast" subtitle="Regional crop yield estimates from historical data" icon={TrendingUp} />,
    irrigation: <ModulePage title="Smart farming" subtitle="Transparent irrigation and field-management decisions" icon={Tractor} />,
  }

  return (
    <div className="app-shell">
      <Sidebar active={active} setActive={setActive} open={menuOpen} setOpen={setMenuOpen} />
      <div className="main-shell">
        <Header setOpen={setMenuOpen} user={user} onLogout={logout} />
        <div className={active === 'disease' ? '' : 'hidden-module'}><DiseasePage /></div>
        {active !== 'disease' && pages[active]}
      </div>
    </div>
  )
}
