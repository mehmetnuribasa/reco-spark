import React, { useState } from 'react';
import MovieCard from './components/MovieCard';
import { getRecommendations } from './services/api';

const GlobalStyles = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: #13131f;
      color: #e2e8f0;
      font-family: 'DM Sans', sans-serif;
      min-height: 100vh;
    }

    /* Noise texture overlay */
    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
      pointer-events: none;
      z-index: 0;
    }

    .app-wrapper {
      position: relative;
      z-index: 1;
      max-width: 1100px;
      margin: 0 auto;
      padding: 60px 24px 80px;
    }

    .header {
      text-align: center;
      margin-bottom: 56px;
    }

    .header h1 {
      font-family: 'Syne', sans-serif;
      font-size: clamp(2.4rem, 5vw, 3.8rem);
      font-weight: 800;
      letter-spacing: -0.03em;
      background: linear-gradient(135deg, #e2e8f0 0%, #a5b4fc 50%, #ec4899 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      line-height: 1.1;
      margin-bottom: 12px;
    }

    .header p {
      font-size: 15px;
      color: #64748b;
      font-weight: 300;
      letter-spacing: 0.02em;
    }

    .search-row {
      display: flex;
      justify-content: center;
      gap: 12px;
      margin-bottom: 48px;
      flex-wrap: wrap;
    }

    .input-wrap {
      position: relative;
    }

    .input-wrap input {
      background: #1e1e2e;
      border: 1px solid rgba(99,102,241,0.3);
      border-radius: 12px;
      color: #e2e8f0;
      font-family: 'DM Sans', sans-serif;
      font-size: 15px;
      padding: 14px 20px;
      width: 260px;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
    }

    .input-wrap input:focus {
      border-color: #6366f1;
      box-shadow: 0 0 0 3px rgba(99,102,241,0.15);
    }

    .input-wrap input::placeholder { color: #475569; }

    .btn {
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      border: none;
      border-radius: 12px;
      color: #fff;
      cursor: pointer;
      font-family: 'DM Sans', sans-serif;
      font-size: 15px;
      font-weight: 500;
      padding: 14px 28px;
      transition: opacity 0.2s, transform 0.15s, box-shadow 0.2s;
      letter-spacing: 0.01em;
      box-shadow: 0 4px 16px rgba(99,102,241,0.3);
    }

    .btn:hover:not(:disabled) {
      opacity: 0.92;
      transform: translateY(-1px);
      box-shadow: 0 8px 24px rgba(99,102,241,0.4);
    }

    .btn:active:not(:disabled) { transform: translateY(0); }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }

    .error-msg {
      text-align: center;
      color: #f87171;
      font-size: 14px;
      margin-bottom: 24px;
      padding: 12px 20px;
      background: rgba(248,113,113,0.08);
      border: 1px solid rgba(248,113,113,0.2);
      border-radius: 10px;
      max-width: 400px;
      margin-left: auto;
      margin-right: auto;
    }

    .section-label {
      font-family: 'Syne', sans-serif;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #475569;
      text-align: center;
      margin-bottom: 28px;
    }

    .cards-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 20px;
      justify-content: center;
    }

    .spinner {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 8px;
      padding: 48px 0;
      color: #475569;
      font-size: 14px;
    }

    .spinner::before {
      content: '';
      width: 20px;
      height: 20px;
      border: 2px solid rgba(99,102,241,0.2);
      border-top-color: #6366f1;
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    .card-enter {
      animation: cardIn 0.35s ease both;
    }

    @keyframes cardIn {
      from { opacity: 0; transform: translateY(16px); }
      to   { opacity: 1; transform: translateY(0); }
    }
  `}</style>
);

export default function App() {
  const [userId, setUserId]       = useState('');
  const [topN]                    = useState(10);
  const [movies, setMovies]       = useState([]);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState('');
  const [searched, setSearched]   = useState(false);

  const handleSubmit = async () => {
    const id = parseInt(userId);
    if (!userId || isNaN(id) || id <= 0) {
      setError('Lütfen geçerli bir kullanıcı ID girin.');
      return;
    }

    setLoading(true);
    setError('');
    setMovies([]);
    setSearched(true);

    try {
      const recs = await getRecommendations(id, topN);
      setMovies(recs);
    } catch (err) {
      if (err.response?.status === 404) {
        setError('Kullanıcı bulunamadı veya bu kullanıcı için öneri mevcut değil.');
      } else {
        setError('API hatası. Backend çalışıyor mu?');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSubmit();
  };

  return (
    <>
      <GlobalStyles />
      <div className="app-wrapper">
        {/* Header */}
        <div className="header">
          <h1>Reco·Spark</h1>
          <p>Kişiselleştirilmiş film önerileri · MovieLens 25M · ALS</p>
        </div>

        {/* Search */}
        <div className="search-row">
          <div className="input-wrap">
            <input
              type="number"
              min="1"
              placeholder="Kullanıcı ID (örn: 1)"
              value={userId}
              onChange={e => setUserId(e.target.value)}
              onKeyDown={handleKeyDown}
            />
          </div>
          <button
            className="btn"
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? 'Yükleniyor...' : 'Öneri Al'}
          </button>
        </div>

        {/* Error */}
        {error && <div className="error-msg">{error}</div>}

        {/* Loading */}
        {loading && <div className="spinner">Öneriler hesaplanıyor</div>}

        {/* Results */}
        {!loading && movies.length > 0 && (
          <>
            <div className="section-label">
              Kullanıcı #{userId} için {movies.length} öneri
            </div>
            <div className="cards-grid">
              {movies.map((movie, i) => (
                <div
                  key={movie.movieId}
                  className="card-enter"
                  style={{ animationDelay: `${i * 40}ms` }}
                >
                  <MovieCard movie={movie} />
                </div>
              ))}
            </div>
          </>
        )}

        {/* Empty state */}
        {!loading && searched && movies.length === 0 && !error && (
          <div style={{ textAlign: 'center', color: '#475569', padding: '48px 0', fontSize: '14px' }}>
            Sonuç bulunamadı.
          </div>
        )}
      </div>
    </>
  );
}