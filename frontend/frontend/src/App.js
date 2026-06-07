import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import Header        from './components/Header';
import SearchBar     from './components/SearchBar';
import MovieCard     from './components/MovieCard';
import LoadingSpinner from './components/LoadingSpinner';
import EmptyState    from './components/EmptyState';
import StatsBar      from './components/StatsBar';
import GenreFilter   from './components/GenreFilter';
import ScrollToTop   from './components/ScrollToTop';
import { getRecommendations, checkHealth } from './services/api';

const calcAvg = (recs) => {
  if (!recs.length) return null;
  const sum = recs.reduce((a, r) => a + r.predictedRating, 0);
  return (sum / recs.length).toFixed(2);
};

function App() {
  const [userId, setUserId]           = useState('');
  const [topN, setTopN]               = useState(10);
  const [loading, setLoading]         = useState(false);
  const [data, setData]               = useState(null);   // { userId, recommendations }
  const [error, setError]             = useState(null);
  const [healthStatus, setHealthStatus] = useState('checking');
  const [hasSearched, setHasSearched] = useState(false);
  const [viewMode, setViewMode]       = useState('grid');
  const [activeGenre, setActiveGenre] = useState(null);

  const resultsRef = useRef(null);

  /* ── Health poll ──────────────────────────────────── */
  const pollHealth = useCallback(async () => {
    try {
      const res = await checkHealth();
      setHealthStatus(res.model_ready ? 'ok' : 'degraded');
    } catch {
      setHealthStatus('error');
    }
  }, []);

  useEffect(() => {
    pollHealth();
    const id = setInterval(pollHealth, 30_000);
    return () => clearInterval(id);
  }, [pollHealth]);

  /* ── Search ───────────────────────────────────────── */
  const runSearch = async (uid) => {
    setLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const res = await getRecommendations(uid, topN);
      setData(res);
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 120);
    } catch (err) {
      setData(null);
      if (err.response?.status === 404) {
        setError(`Kullanıcı #${uid} için öneri bulunamadı. Farklı bir ID deneyin.`);
      } else if (err.response?.status === 503) {
        setError('Model henüz yüklenmedi. Birkaç saniye bekleyip tekrar deneyin.');
      } else {
        setError(
          err.response?.data?.detail ??
          'Öneriler alınırken bir hata oluştu. Backend\'in çalıştığından emin olun.'
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    const uid = parseInt(userId);
    if (!userId || isNaN(uid) || uid < 1) {
      setError('Lütfen geçerli bir kullanıcı ID girin (1 – 162.541).');
      return;
    }
    runSearch(uid);
  };

  const handleExampleSelect = (id) => {
    setUserId(String(id));
    runSearch(id);
  };

  const handleKeyDown = (e) => e.key === 'Enter' && !loading && handleSearch();

  const handleClear = () => {
    setData(null);
    setError(null);
    setHasSearched(false);
    setUserId('');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const recommendations = data?.recommendations ?? [];
  const avgRating = data ? calcAvg(recommendations) : null;

  useEffect(() => { setActiveGenre(null); }, [data]);

  const filteredRecs = activeGenre
    ? recommendations.filter((m) => m.genres && m.genres.split('|').includes(activeGenre))
    : recommendations;

  return (
    <div className="app">
      {/* Ambient glow blobs */}
      <div className="app__glow app__glow--purple" aria-hidden="true" />
      <div className="app__glow app__glow--cyan"   aria-hidden="true" />

      <Header healthStatus={healthStatus} />

      <main className="app__main">
        <div className="app__container">

          <SearchBar
            userId={userId}
            topN={topN}
            loading={loading}
            onUserIdChange={setUserId}
            onTopNChange={setTopN}
            onSearch={handleSearch}
            onKeyDown={handleKeyDown}
            onExampleSelect={handleExampleSelect}
          />

          {/* Error banner */}
          {error && !loading && (
            <div className="app__error" role="alert">
              <p>{error}</p>
              <button className="app__error-close" onClick={() => setError(null)} aria-label="Kapat">Kapat</button>
            </div>
          )}

          {/* Results area */}
          <div ref={resultsRef}>
            {loading && <LoadingSpinner />}

            {!loading && data && recommendations.length > 0 && (
              <>
                <StatsBar
                  count={filteredRecs.length}
                  userId={data.userId}
                  avgRating={avgRating}
                  viewMode={viewMode}
                  onViewModeChange={setViewMode}
                  onClear={handleClear}
                />
                <GenreFilter
                  recommendations={recommendations}
                  activeGenre={activeGenre}
                  onGenreChange={setActiveGenre}
                />
                {filteredRecs.length > 0 ? (
                  <div className={`app__grid ${viewMode === 'list' ? 'app__grid--list' : ''}`}>
                    {filteredRecs.map((movie, idx) => (
                      <MovieCard key={movie.movieId} movie={movie} rank={idx + 1} viewMode={viewMode} />
                    ))}
                  </div>
                ) : (
                  <p className="app__filter-empty">
                    Bu türde öneri bulunamadı. Farklı bir tür seçin.
                  </p>
                )}
              </>
            )}

            {!loading && data && recommendations.length === 0 && (
              <EmptyState message="Bu kullanıcı için öneri bulunamadı." />
            )}

            {!loading && !data && !error && hasSearched && (
              <EmptyState message="Sonuç yüklenemedi. Backend bağlantısını kontrol edin." />
            )}

            {!loading && !data && !hasSearched && <EmptyState />}
          </div>
        </div>
      </main>

      <ScrollToTop />

      <footer className="app__footer">
        <p className="app__footer-brand">Reco-Spark</p>
        <p className="app__footer-sub">
          CSE458 – Big Data Analytics &nbsp;·&nbsp; Gebze Teknik Üniversitesi
        </p>
        <p className="app__footer-stack">
          Apache Spark &nbsp;·&nbsp; PySpark MLlib ALS &nbsp;·&nbsp; FastAPI &nbsp;·&nbsp; React
        </p>
      </footer>
    </div>
  );
}

export default App;
