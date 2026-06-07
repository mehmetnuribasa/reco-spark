import React from 'react';
import './SearchBar.css';

const TOP_N_OPTIONS = [5, 10, 15, 20];

const EXAMPLE_USERS = [
  { id: 1,      label: '#1' },
  { id: 414,    label: '#414' },
  { id: 3000,   label: '#3000' },
  { id: 18000,  label: '#18000' },
  { id: 99000,  label: '#99000' },
  { id: 162541, label: '#162541' },
];

const SearchBar = ({
  userId, topN, loading,
  onUserIdChange, onTopNChange, onSearch, onKeyDown, onExampleSelect,
}) => (
  <section className="search">
    <div className="search__card">
      <div className="search__header">
        <h2 className="search__title">Film Önerileri Al</h2>
        <p className="search__desc">
          MovieLens 25M üzerinde eğitilmiş ALS modeli ile kişiselleştirilmiş öneriler
        </p>
      </div>

      <div className="search__body">
        <div className="search__field">
          <label className="search__label" htmlFor="user-id">Kullanıcı ID</label>
          <div className="search__input-wrap">
            <span className="search__input-icon">#</span>
            <input
              id="user-id"
              type="number"
              className="search__input"
              placeholder="Kullanıcı ID girin (ör: 1)"
              value={userId}
              onChange={(e) => onUserIdChange(e.target.value)}
              onKeyDown={onKeyDown}
              min="1"
              max="162541"
              disabled={loading}
              autoFocus
            />
          </div>
        </div>

        <div className="search__field search__field--narrow">
          <label className="search__label" htmlFor="top-n">Öneri Sayısı</label>
          <select
            id="top-n"
            className="search__select"
            value={topN}
            onChange={(e) => onTopNChange(Number(e.target.value))}
            disabled={loading}
          >
            {TOP_N_OPTIONS.map((n) => (
              <option key={n} value={n}>{n} Film</option>
            ))}
          </select>
        </div>

        <button
          className="search__btn"
          onClick={onSearch}
          disabled={loading || !userId}
        >
          {loading ? (
            <><span className="search__spinner" /> Yükleniyor...</>
          ) : (
            'Öneri Al'
          )}
        </button>
      </div>

      <div className="search__footer">
        <p className="search__hint">
          MovieLens 25M: 162.541 kullanıcı · 62.423 film · 25.000.095 değerlendirme
        </p>

        <div className="search__examples">
          <span className="search__examples-label">Hızlı dene:</span>
          <div className="search__example-chips">
            {EXAMPLE_USERS.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                className={`search__example-chip ${String(userId) === String(id) ? 'search__example-chip--active' : ''}`}
                onClick={() => onExampleSelect(id)}
                disabled={loading}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  </section>
);

export default SearchBar;
