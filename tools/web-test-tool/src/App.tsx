import { useState, useEffect, useCallback } from 'react'
import { api, ApiError, setApiBaseUrl } from './api'
import './App.css'

// Local type definitions
type BackendType = 'fastembed' | 'st';
type E5Mode = 'auto' | 'query' | 'passage';

interface ModelSpec {
  backend: BackendType;
  name: string;
  normalize: boolean;
  e5_mode: E5Mode;
}

interface PresetModel {
  preset_id: string;
  backend: BackendType;
  name: string;
  normalize: boolean;
  e5_mode: E5Mode;
}

interface QdrantConfig {
  url: string;
  collection: string;
  query_filter?: Record<string, unknown>;
}

interface SearchRequest {
  text: string;
  preset_id?: string;
  model?: ModelSpec;
  top_k?: number;
  threshold?: number;
  with_payload?: boolean;
  qdrant: QdrantConfig;
}

interface Hit {
  id: string | number;
  score: number;
  payload?: Record<string, unknown>;
}

interface SearchResponse {
  took_ms: number;
  model: ModelSpec;
  collection: string;
  total_candidates: number;
  hits: Hit[];
}

// UI State Types
interface SearchState {
  loading: boolean;
  error: string | null;
  result: SearchResponse | null;
}

interface UISettings {
  darkMode: boolean;
  compactMode: boolean;
  showAdvanced: boolean;
}

function App() {
  // Models state
  const [models, setModels] = useState<PresetModel[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('')

  // Search form state
  const [text, setText] = useState<string>('')
  const [apiServerUrl, setApiServerUrl] = useState<string>(() => {
    return localStorage.getItem('lastApiServerUrl') || 'http://localhost:5200'
  })
  const [qdrantUrl, setQdrantUrl] = useState<string>(() => {
    return localStorage.getItem('lastQdrantUrl') || 'http://localhost:6333'
  })
  const [collection, setCollection] = useState<string>(() => {
    return localStorage.getItem('lastCollection') || ''
  })
  const [topK, setTopK] = useState<number>(() => {
    const saved = localStorage.getItem('lastTopK')
    return saved ? parseInt(saved) : 5
  })
  const [threshold, setThreshold] = useState<number>(() => {
    const saved = localStorage.getItem('lastThreshold')
    return saved ? parseFloat(saved) : 0.0
  })
  const [withPayload, setWithPayload] = useState<boolean>(() => {
    const saved = localStorage.getItem('lastWithPayload')
    return saved ? saved === 'true' : true
  })
  const [filterJson, setFilterJson] = useState<string>(() => {
    return localStorage.getItem('lastFilterJson') || ''
  })
  const [filterError, setFilterError] = useState<string>('')

  // Search state
  const [searchState, setSearchState] = useState<SearchState>({
    loading: false,
    error: null,
    result: null
  })

  // UI Settings
  const [uiSettings, setUISettings] = useState<UISettings>({
    darkMode: true,
    compactMode: false,
    showAdvanced: false
  })

  // Connection status
  const [isConnected, setIsConnected] = useState<boolean | null>(null)

  // Panel resizing
  const [leftPanelWidth, setLeftPanelWidth] = useState<number>(() => {
    const saved = localStorage.getItem('leftPanelWidth')
    return saved ? parseInt(saved) : 500
  })
  const [isResizing, setIsResizing] = useState<boolean>(false)

  // Copy functionality
  const [copiedTexts, setCopiedTexts] = useState<Set<string>>(new Set())

  const checkConnection = useCallback(async () => {
    try {
      await api.getHealth()
      setIsConnected(true)
    } catch {
      setIsConnected(false)
    }
  }, [])

  const loadModels = useCallback(async () => {
    try {
      const response = await api.getModels()
      setModels(response.models)

      // 저장된 모델 ID가 있으면 사용, 없으면 첫 번째 모델 사용
      const lastModelId = localStorage.getItem('lastSelectedModel')
      if (lastModelId && response.models.find(m => m.preset_id === lastModelId)) {
        setSelectedModel(lastModelId)
      } else if (response.models.length > 0) {
        setSelectedModel(response.models[0].preset_id)
      }
      setIsConnected(true)
    } catch (error) {
      console.warn('API 연결 실패, 기본 모델 사용:', error)
      const defaultModels: PresetModel[] = [
        { preset_id: 'bge-m3', backend: 'fastembed', name: 'BAAI/bge-m3', normalize: true, e5_mode: 'auto' },
        { preset_id: 'ko-sbert', backend: 'st', name: './models/ko-sbert', normalize: true, e5_mode: 'auto' },
        { preset_id: 'mE5-base', backend: 'st', name: 'intfloat/multilingual-e5-base', normalize: true, e5_mode: 'auto' },
        { preset_id: 'mE5-large', backend: 'st', name: 'intfloat/multilingual-e5-large', normalize: true, e5_mode: 'auto' }
      ]
      setModels(defaultModels)

      const lastModelId = localStorage.getItem('lastSelectedModel')
      if (lastModelId && defaultModels.find(m => m.preset_id === lastModelId)) {
        setSelectedModel(lastModelId)
      } else {
        setSelectedModel('bge-m3')
      }
      setIsConnected(false)
    }
  }, [])

  const handleConnectToServer = useCallback(async () => {
    setSearchState(prev => ({
      ...prev,
      loading: true,
      error: null
    }))

    // Update API base URL
    setApiBaseUrl(apiServerUrl)

    try {
      // Check health first
      await checkConnection()

      // Load models
      await loadModels()

      // Save API server URL on successful connection
      localStorage.setItem('lastApiServerUrl', apiServerUrl)

    } catch (err) {
      setSearchState(prev => ({
        ...prev,
        error: `서버 연결 실패: ${err instanceof Error ? err.message : String(err)}`
      }))
    } finally {
      setSearchState(prev => ({
        ...prev,
        loading: false
      }))
    }
  }, [apiServerUrl, checkConnection, loadModels])

  // Set API base URL when component mounts or URL changes
  useEffect(() => {
    setApiBaseUrl(apiServerUrl)
  }, [apiServerUrl])

  // Apply initial dark mode and set page title (removed auto loadModels)
  useEffect(() => {
    // Apply initial dark mode
    document.body.classList.add('dark-body')
    // Set page title
    document.title = 'Vector Search Tester'
  }, [loadModels, checkConnection])

  // JSON 필터 유효성 검증
  const validateFilter = useCallback((jsonString: string): { valid: boolean; parsed?: any; error?: string } => {
    if (!jsonString.trim()) {
      return { valid: true, parsed: null }
    }
    try {
      const parsed = JSON.parse(jsonString)
      return { valid: true, parsed }
    } catch (err) {
      return { valid: false, error: err instanceof Error ? err.message : 'Invalid JSON' }
    }
  }, [])

  // 성공한 설정 정보를 로컬 스토리지에 저장
  const saveSuccessfulSettings = useCallback(() => {
    localStorage.setItem('lastApiServerUrl', apiServerUrl)
    localStorage.setItem('lastQdrantUrl', qdrantUrl)
    localStorage.setItem('lastCollection', collection.trim())
    localStorage.setItem('lastSelectedModel', selectedModel)
    localStorage.setItem('lastTopK', topK.toString())
    localStorage.setItem('lastThreshold', threshold.toString())
    localStorage.setItem('lastWithPayload', withPayload.toString())
    localStorage.setItem('lastFilterJson', filterJson.trim())
  }, [apiServerUrl, qdrantUrl, collection, selectedModel, topK, threshold, withPayload, filterJson])

  const handleSearch = useCallback(async () => {
    if (!text.trim() || !collection.trim()) {
      setSearchState(prev => ({
        ...prev,
        error: '검색 텍스트와 컬렉션 이름을 입력해주세요.'
      }))
      return
    }

    if (!isConnected || models.length === 0) {
      setSearchState(prev => ({
        ...prev,
        error: 'API 서버에 먼저 연결해주세요.'
      }))
      return
    }

    // 필터 유효성 검증
    const filterValidation = validateFilter(filterJson)
    if (!filterValidation.valid) {
      setFilterError(filterValidation.error || 'Invalid JSON')
      setSearchState(prev => ({
        ...prev,
        error: `필터 JSON 오류: ${filterValidation.error}`
      }))
      return
    }
    setFilterError('')

    setSearchState(prev => ({
      ...prev,
      loading: true,
      error: null,
      result: null
    }))

    // Update title during search
    document.title = 'Vector Search Tester - Searching...'

    try {
      const request: SearchRequest = {
        text: text.trim(),
        preset_id: selectedModel,
        top_k: topK,
        threshold: threshold,
        with_payload: withPayload,
        qdrant: {
          url: qdrantUrl,
          collection: collection.trim(),
          query_filter: filterValidation.parsed || undefined
        }
      }

      const result = await api.search(request)

      // 검색 성공 시 설정 정보 저장
      saveSuccessfulSettings()

      setSearchState(prev => ({
        ...prev,
        loading: false,
        result,
        error: null
      }))

      // Update title with result count
      document.title = `Vector Search Tester - ${result.hits.length} results`
    } catch (error) {
      const errorMessage = error instanceof ApiError
        ? error.message
        : '알 수 없는 오류가 발생했습니다.'

      setSearchState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage
      }))

      // Update title on error
      document.title = 'Vector Search Tester - Error'
    }
  }, [text, collection, selectedModel, topK, threshold, withPayload, qdrantUrl, apiServerUrl, filterJson, validateFilter, saveSuccessfulSettings])

  const toggleDarkMode = useCallback(() => {
    setUISettings(prev => {
      const newDarkMode = !prev.darkMode
      // Apply dark mode to body element
      if (newDarkMode) {
        document.body.classList.add('dark-body')
      } else {
        document.body.classList.remove('dark-body')
      }
      return { ...prev, darkMode: newDarkMode }
    })
  }, [])

  // Apply initial dark mode to body
  useEffect(() => {
    if (uiSettings.darkMode) {
      document.body.classList.add('dark-body')
    } else {
      document.body.classList.remove('dark-body')
    }
  }, [uiSettings.darkMode])

  const toggleAdvanced = useCallback(() => {
    setUISettings(prev => ({ ...prev, showAdvanced: !prev.showAdvanced }))
  }, [])

  // Filter presets
  const filterPresets = {
    category: {
      name: '카테고리 필터',
      json: JSON.stringify({
        "must": [
          { "key": "category", "match": { "value": "기술" } }
        ]
      }, null, 2)
    },
    dateRange: {
      name: '날짜 범위',
      json: JSON.stringify({
        "must": [
          { "key": "created_at", "range": { "gte": "2024-01-01T00:00:00Z" } }
        ]
      }, null, 2)
    },
    multiCondition: {
      name: '복합 조건',
      json: JSON.stringify({
        "must": [
          { "key": "category", "match": { "value": "AI" } },
          { "key": "year", "range": { "gte": 2024 } }
        ],
        "must_not": [
          { "key": "status", "match": { "value": "draft" } }
        ]
      }, null, 2)
    },
    tags: {
      name: '태그 필터',
      json: JSON.stringify({
        "must": [
          { "key": "tags", "match": { "any": ["AI", "머신러닝", "딥러닝"] } }
        ]
      }, null, 2)
    }
  }

  const applyFilterPreset = useCallback((presetJson: string) => {
    setFilterJson(presetJson)
    setFilterError('')
  }, [])

  // Copy text to clipboard
  const copyToClipboard = useCallback(async (text: string, hitId: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedTexts(prev => new Set(prev).add(hitId))

      // Reset copied state after 2 seconds
      setTimeout(() => {
        setCopiedTexts(prev => {
          const newSet = new Set(prev)
          newSet.delete(hitId)
          return newSet
        })
      }, 2000)
    } catch (err) {
      console.error('복사 실패:', err)
    }
  }, [])

  // Panel resizing handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
  }, [])

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing) return

    const newWidth = e.clientX - 32 // Account for main padding
    const minWidth = 350
    const maxWidth = 800

    if (newWidth >= minWidth && newWidth <= maxWidth) {
      setLeftPanelWidth(newWidth)
    }
  }, [isResizing])

  const handleMouseUp = useCallback(() => {
    if (isResizing) {
      setIsResizing(false)
      localStorage.setItem('leftPanelWidth', leftPanelWidth.toString())
    }
  }, [isResizing, leftPanelWidth])

  // Add global mouse event listeners for resizing
  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'

      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
      }
    }
  }, [isResizing, handleMouseMove, handleMouseUp])

  return (
    <div className={`app ${uiSettings.darkMode ? 'dark' : ''}`}>
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="header-left">
            <h1 className="title">
              <span className="icon">🔍</span>
              Vector Search Tester
            </h1>
            <div className="connection-status">
              <div className={`status-indicator ${isConnected === null ? 'pending' : isConnected ? 'connected' : 'disconnected'}`} />
              <span className="status-text">
                {isConnected === null ? 'Connecting...' : isConnected ? 'API Connected' : 'API Offline'}
              </span>
              {localStorage.getItem('lastCollection') && (
                <span className="last-settings">
                  | Last: {localStorage.getItem('lastCollection')}
                </span>
              )}
            </div>
          </div>
          <div className="header-actions">
            <button
              className="icon-button"
              onClick={toggleAdvanced}
              title="Toggle Advanced Settings"
            >
              ⚙️
            </button>
            <button
              className="icon-button"
              onClick={toggleDarkMode}
              title="Toggle Dark Mode"
            >
              {uiSettings.darkMode ? '☀️' : '🌙'}
            </button>
            <button
              className="icon-button"
              onClick={checkConnection}
              title="Refresh Connection"
            >
              🔄
            </button>
          </div>
        </div>
      </header>

      <main className="main">
        {/* Left Panel - Search Form */}
        <div className="search-panel" style={{ width: `${leftPanelWidth}px` }}>
          <div className="search-form-card">
              <div className="card-header">
                <h2>⚙️ Search Configuration</h2>
              </div>
              <div className="card-content">
              {/* API Server URL - 맨 위로 이동 */}
              <div className="form-group">
                <label htmlFor="api-server-url" className="label">
                  🌐 API Server URL
                </label>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input
                    id="api-server-url"
                    type="text"
                    className="input"
                    value={apiServerUrl}
                    onChange={(e) => setApiServerUrl(e.target.value)}
                    placeholder="http://localhost:5200"
                    style={{ flex: 1 }}
                  />
                  <button
                    type="button"
                    className="button button-secondary"
                    onClick={handleConnectToServer}
                    disabled={searchState.loading}
                    title="Connect and Load Models"
                  >
                    {searchState.loading ? '⏳' : '🔗'}
                  </button>
                </div>
                {(!isConnected || models.length === 0) && (
                  <small style={{ color: 'var(--color-warning)', fontSize: '12px' }}>
                    Connect to server to load available models
                  </small>
                )}
                {isConnected && models.length > 0 && (
                  <small style={{ color: 'var(--color-success)', fontSize: '12px' }}>
                    ✓ Connected - {models.length} models available
                  </small>
                )}
              </div>

              {/* Model Selection - API 연결 후에만 활성화 */}
              <div className="form-group">
                <label htmlFor="model" className="label">
                  🤖 Embedding Model
                </label>
                <select
                  id="model"
                  className="input select"
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  disabled={!isConnected || models.length === 0 || searchState.loading}
                >
                  {models.length === 0 ? (
                    <option value="">No models available - Connect to server first</option>
                  ) : (
                    models.map(model => (
                      <option key={model.preset_id} value={model.preset_id}>
                        {model.preset_id} ({model.backend}) - {model.name}
                      </option>
                    ))
                  )}
                </select>
              </div>

              {/* Query Text */}
              <div className="form-group">
                <label htmlFor="text" className="label">
                  Search Query
                </label>
                <textarea
                  id="text"
                  className="input textarea"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Enter your search query here..."
                  rows={3}
                />
              </div>


              {/* Qdrant Settings */}
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="qdrant-url" className="label">
                    Qdrant URL
                  </label>
                  <input
                    id="qdrant-url"
                    type="text"
                    className="input"
                    value={qdrantUrl}
                    onChange={(e) => setQdrantUrl(e.target.value)}
                    placeholder="http://localhost:6333"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="collection" className="label">
                    Collection Name
                  </label>
                  <input
                    id="collection"
                    type="text"
                    className="input"
                    value={collection}
                    onChange={(e) => setCollection(e.target.value)}
                    placeholder="documents"
                  />
                </div>
              </div>

              {/* Advanced Settings */}
              {uiSettings.showAdvanced && (
                <div className="advanced-settings">
                  <h3 className="section-title">Advanced Settings</h3>
                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="top-k" className="label">
                        Top K Results
                      </label>
                      <input
                        id="top-k"
                        type="number"
                        className="input"
                        value={topK}
                        onChange={(e) => setTopK(Number(e.target.value))}
                        min="1"
                        max="100"
                      />
                    </div>
                    <div className="form-group">
                      <label htmlFor="threshold" className="label">
                        최소 유사도
                      </label>
                      <input
                        id="threshold"
                        type="number"
                        className="input"
                        value={threshold}
                        onChange={(e) => setThreshold(Number(e.target.value))}
                        min="0"
                        max="1"
                        step="0.01"
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        className="checkbox"
                        checked={withPayload}
                        onChange={(e) => setWithPayload(e.target.checked)}
                      />
                      <span className="checkbox-text">Include metadata in results</span>
                    </label>
                  </div>

                  {/* Qdrant Filter */}
                  <div className="form-group">
                    <label htmlFor="filter-json" className="label">
                      🔍 Qdrant Filter (JSON)
                    </label>

                    {/* Filter Presets */}
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', flexWrap: 'wrap' }}>
                      <button
                        type="button"
                        className="button button-secondary"
                        style={{ fontSize: '12px', padding: '4px 8px' }}
                        onClick={() => applyFilterPreset(filterPresets.category.json)}
                        title="카테고리 필터 예시 적용"
                      >
                        📁 {filterPresets.category.name}
                      </button>
                      <button
                        type="button"
                        className="button button-secondary"
                        style={{ fontSize: '12px', padding: '4px 8px' }}
                        onClick={() => applyFilterPreset(filterPresets.dateRange.json)}
                        title="날짜 범위 필터 예시 적용"
                      >
                        📅 {filterPresets.dateRange.name}
                      </button>
                      <button
                        type="button"
                        className="button button-secondary"
                        style={{ fontSize: '12px', padding: '4px 8px' }}
                        onClick={() => applyFilterPreset(filterPresets.multiCondition.json)}
                        title="복합 조건 필터 예시 적용"
                      >
                        🎯 {filterPresets.multiCondition.name}
                      </button>
                      <button
                        type="button"
                        className="button button-secondary"
                        style={{ fontSize: '12px', padding: '4px 8px' }}
                        onClick={() => applyFilterPreset(filterPresets.tags.json)}
                        title="태그 필터 예시 적용"
                      >
                        🏷️ {filterPresets.tags.name}
                      </button>
                      <button
                        type="button"
                        className="button button-secondary"
                        style={{ fontSize: '12px', padding: '4px 8px' }}
                        onClick={() => {
                          setFilterJson('')
                          setFilterError('')
                        }}
                        title="필터 초기화"
                      >
                        🗑️ 초기화
                      </button>
                    </div>

                    <textarea
                      id="filter-json"
                      className={`input textarea ${filterError ? 'error' : ''}`}
                      value={filterJson}
                      onChange={(e) => {
                        setFilterJson(e.target.value)
                        setFilterError('')
                      }}
                      placeholder='예시: {"must": [{"key": "category", "match": {"value": "기술"}}]}'
                      rows={6}
                      style={{
                        fontFamily: 'monospace',
                        fontSize: '13px',
                        borderColor: filterError ? 'var(--color-error)' : undefined
                      }}
                    />
                    {filterError && (
                      <small style={{ color: 'var(--color-error)', fontSize: '12px', marginTop: '4px', display: 'block' }}>
                        ❌ {filterError}
                      </small>
                    )}
                    {!filterError && filterJson.trim() && (
                      <small style={{ color: 'var(--color-success)', fontSize: '12px', marginTop: '4px', display: 'block' }}>
                        ✓ Valid JSON
                      </small>
                    )}
                    <small style={{ color: 'var(--color-text-secondary)', fontSize: '12px', marginTop: '4px', display: 'block' }}>
                      비워두면 필터 없이 검색합니다. <a href="https://github.com/yourusername/vector/blob/main/docs/QDRANT_FILTERING_GUIDE.md" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-primary)' }}>필터 가이드 보기</a>
                    </small>
                  </div>
                </div>
              )}

              {/* Search Button */}
              <div className="search-actions">
                <button
                  onClick={handleSearch}
                  disabled={searchState.loading || !text.trim() || !collection.trim()}
                  className={`search-button ${searchState.loading ? 'loading' : ''}`}
                >
                  {searchState.loading ? (
                    <>
                      <span className="spinner" />
                      Searching...
                    </>
                  ) : (
                    <>
                      <span>🔍</span>
                      Search
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Resizer Handle */}
          <div
            className={`panel-resizer ${isResizing ? 'resizing' : ''}`}
            onMouseDown={handleMouseDown}
          />
        </div>

        {/* Right Panel - Results */}
        <div className="results-panel">
          {(!searchState.result && !searchState.error) ? (
            <div className="results-header">
              <h2>🔍 Search Results</h2>
              <p style={{ margin: 0, color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                Enter your search query and click "Search" to see results here
              </p>
            </div>
          ) : (
            <>
              {searchState.result && (
                <div className="results-header">
                  <h2>✅ Search Results</h2>
                  <div className="result-summary">
                    <span className="result-count">{searchState.result.hits.length} results</span>
                    <span className="result-time">{searchState.result.took_ms}ms</span>
                  </div>
                </div>
              )}

              {searchState.error && (
                <div className="results-header">
                  <h2 className="error-title">❌ Error</h2>
                </div>
              )}
            </>
          )}

          <div className="results-content">
            <div className="results-container">
          {/* Error Display */}
          {searchState.error && (
            <div style={{ padding: 'var(--spacing-lg)', color: 'var(--color-error)' }}>
              <p className="error-message">{searchState.error}</p>
            </div>
          )}

          {/* Results Display */}
          {searchState.result && (
            <>
              <div style={{ padding: 'var(--spacing-lg)' }}>
                <div className="card-content">
                    {/* Result Metadata */}
                    <div className="result-metadata">
                      <div className="metadata-grid">
                        <div className="metadata-item">
                          <span className="metadata-label">Model:</span>
                          <span className="metadata-value">
                            {searchState.result.model.name} ({searchState.result.model.backend})
                          </span>
                        </div>
                        <div className="metadata-item">
                          <span className="metadata-label">Collection:</span>
                          <span className="metadata-value">{searchState.result.collection}</span>
                        </div>
                        <div className="metadata-item">
                          <span className="metadata-label">Total Candidates:</span>
                          <span className="metadata-value">{searchState.result.total_candidates.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>

                    {/* Search Hits */}
                    <div className="hits-container">
                      {searchState.result.hits.map((hit, index) => (
                        <div key={`${hit.id}-${index}`} className="hit-card">
                          <div className="hit-header">
                            <div className="hit-info">
                              <span className="hit-rank">#{index + 1}</span>
                              <span className="hit-id">ID: {hit.id}</span>
                            </div>
                          </div>

                          <div className="hit-content">
                            {/* Similarity Score */}
                            <div className="hit-similarity">
                              <span className="similarity-label">유사도:</span>
                              <span className="similarity-value">{(hit.score * 100).toFixed(1)}%</span>
                            </div>

                            {/* Text Content */}
                            {hit.payload && typeof hit.payload.text === 'string' && (
                              <div className="hit-text">
                                <button
                                  className="text-copy-button"
                                  onClick={() => copyToClipboard(hit.payload?.text as string, `${hit.id}-${index}`)}
                                  title="텍스트 복사"
                                >
                                  {copiedTexts.has(`${hit.id}-${index}`) ? (
                                    <>
                                      <span>✓</span>
                                      <span>복사됨</span>
                                    </>
                                  ) : (
                                    <>
                                      <span>📋</span>
                                      <span>복사</span>
                                    </>
                                  )}
                                </button>
                                {hit.payload.text}
                              </div>
                            )}

                            {/* Other fields in payload */}
                            {hit.payload && withPayload && Object.keys(hit.payload).filter(key => key !== 'text').length > 0 && (
                              <div className="hit-payload">
                                <details className="payload-details">
                                  <summary className="payload-summary">
                                    📄 추가 메타데이터 ({Object.keys(hit.payload).filter(key => key !== 'text').length} fields)
                                  </summary>
                                  <pre className="payload-content">
                                    {JSON.stringify(
                                      Object.fromEntries(
                                        Object.entries(hit.payload).filter(([key]) => key !== 'text')
                                      ),
                                      null,
                                      2
                                    )}
                                  </pre>
                                </details>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </>
          )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
