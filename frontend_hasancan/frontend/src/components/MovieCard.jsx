import React, { useState } from 'react';
import './MovieCard.css';

const GENRE_GRADIENTS = {
  Action:      'linear-gradient(145deg, #ef4444, #b91c1c)',
  Adventure:   'linear-gradient(145deg, #f97316, #c2410c)',
  Animation:   'linear-gradient(145deg, #eab308, #d97706)',
  Comedy:      'linear-gradient(145deg, #22c55e, #15803d)',
  Crime:       'linear-gradient(145deg, #a855f7, #7e22ce)',
  Documentary: 'linear-gradient(145deg, #06b6d4, #0e7490)',
  Drama:       'linear-gradient(145deg, #3b82f6, #1d4ed8)',
  Fantasy:     'linear-gradient(145deg, #8b5cf6, #6d28d9)',
  'Film-Noir': 'linear-gradient(145deg, #475569, #1e293b)',
  Horror:      'linear-gradient(145deg, #dc2626, #450a0a)',
  Musical:     'linear-gradient(145deg, #ec4899, #be185d)',
  Mystery:     'linear-gradient(145deg, #6366f1, #3730a3)',
  Romance:     'linear-gradient(145deg, #f43f5e, #be123c)',
  'Sci-Fi':    'linear-gradient(145deg, #14b8a6, #0f766e)',
  Thriller:    'linear-gradient(145deg, #d97706, #78350f)',
  War:         'linear-gradient(145deg, #64748b, #334155)',
  Western:     'linear-gradient(145deg, #92400e, #451a03)',
  IMAX:        'linear-gradient(145deg, #2563eb, #1e3a8a)',
};

const DEFAULT_GRADIENT = 'linear-gradient(145deg, #334155, #1e293b)';

const extractYear = (title) => title.match(/\((\d{4})\)$/)?.[1] ?? null;
const cleanTitle  = (title) => title.replace(/\s*\(\d{4}\)\s*$/, '').trim();
const clamp       = (v, min, max) => Math.min(max, Math.max(min, v));

const StarRating = ({ rating }) => {
  const r = clamp(rating, 0, 5);
  const stars = Array.from({ length: 5 }, (_, i) => {
    const v = i + 1;
    if (r >= v)        return 'full';
    if (r >= v - 0.5)  return 'half';
    return 'empty';
  });
  return (
    <div className="stars" aria-label={`${rating} / 5 puan`}>
      {stars.map((type, i) => (
        <span key={i} className={`star star--${type}`} aria-hidden="true">
          {type === 'empty' ? '☆' : '★'}
        </span>
      ))}
    </div>
  );
};

const MovieCard = ({ movie, rank, viewMode = 'grid' }) => {
  const [flipped, setFlipped] = useState(false);

  const genres       = movie.genres && movie.genres !== '(no genres listed)' && movie.genres !== 'Unknown'
    ? movie.genres.split('|')
    : [];
  const primaryGenre = genres[0] ?? 'Drama';
  const gradient     = GENRE_GRADIENTS[primaryGenre] ?? DEFAULT_GRADIENT;
  const year         = extractYear(movie.title);
  const title        = cleanTitle(movie.title);
  const rating       = clamp(movie.predictedRating, 0, 5);

  const toggle = () => setFlipped((f) => !f);
  const onKey  = (e) => (e.key === 'Enter' || e.key === ' ') && toggle();

  /* ── Liste görünümü ──────────────────────────── */
  if (viewMode === 'list') {
    return (
      <article
        className="movie-row"
        style={{ '--genre-gradient': gradient }}
        aria-label={`${title}${year ? ` (${year})` : ''} — Tahmin: ${rating}/5`}
      >
        <div className="movie-row__color-bar" style={{ background: gradient }} />

        <span className="movie-row__rank">#{rank}</span>

        <div className="movie-row__info">
          <h3 className="movie-row__title" title={movie.title}>{title}</h3>
          <div className="movie-row__meta">
            {year && <span className="movie-row__year">{year}</span>}
            <span className="movie-row__id">ID: {movie.movieId}</span>
          </div>
        </div>

        <div className="movie-row__genres">
          {genres.slice(0, 3).map((g) => (
            <span key={g} className="movie-card__tag">{g}</span>
          ))}
        </div>

        <div className="movie-row__rating">
          <StarRating rating={rating} />
          <span className="movie-row__score">
            <strong>{rating.toFixed(2)}</strong>
            <span className="movie-row__score-max">/5</span>
          </span>
        </div>
      </article>
    );
  }

  /* ── Kart görünümü (flip) ────────────────────── */
  return (
    <article
      className={`movie-card ${flipped ? 'movie-card--flipped' : ''}`}
      onClick={toggle}
      onKeyDown={onKey}
      role="button"
      tabIndex={0}
      aria-label={`${title}${year ? ` (${year})` : ''} — Tahmin: ${rating}/5`}
    >
      <div className="movie-card__inner">

        {/* ─── FRONT ─── */}
        <div className="movie-card__front">
          <div className="movie-card__poster" style={{ background: gradient }}>
            <span className="movie-card__rank">#{rank}</span>
            <span className="movie-card__genre-watermark" aria-hidden="true">
              {primaryGenre}
            </span>
            <div className="movie-card__score-badge">
              <span className="movie-card__score-num">{rating.toFixed(1)}</span>
              <span className="movie-card__score-denom">/5</span>
            </div>
          </div>

          <div className="movie-card__body">
            <h3 className="movie-card__title" title={movie.title}>{title}</h3>
            {year && <span className="movie-card__year">{year}</span>}

            <div className="movie-card__genres">
              {genres.slice(0, 2).map((g) => (
                <span key={g} className="movie-card__tag">{g}</span>
              ))}
              {genres.length > 2 && (
                <span className="movie-card__tag movie-card__tag--more">+{genres.length - 2}</span>
              )}
            </div>

            <StarRating rating={rating} />

            <p className="movie-card__flip-hint">Detaylar için tıkla →</p>
          </div>
        </div>

        {/* ─── BACK ─── */}
        <div className="movie-card__back">
          <div className="movie-card__back-poster" style={{ background: gradient }}>
            <p className="movie-card__back-title">{title}</p>
          </div>

          <div className="movie-card__back-body">
            <div className="movie-card__row">
              <span className="movie-card__label">Film ID</span>
              <span className="movie-card__value">#{movie.movieId}</span>
            </div>
            {year && (
              <div className="movie-card__row">
                <span className="movie-card__label">Yıl</span>
                <span className="movie-card__value">{year}</span>
              </div>
            )}
            <div className="movie-card__row">
              <span className="movie-card__label">Tahmin Puanı</span>
              <span className="movie-card__value movie-card__value--gold">
                ★ {rating.toFixed(2)} / 5.00
              </span>
            </div>

            <div className="movie-card__row movie-card__row--col">
              <span className="movie-card__label">Türler</span>
              <div className="movie-card__genres movie-card__genres--wrap">
                {genres.length > 0
                  ? genres.map((g) => <span key={g} className="movie-card__tag">{g}</span>)
                  : <span className="movie-card__value">Belirtilmemiş</span>}
              </div>
            </div>

            <p className="movie-card__back-hint">← Geri dön</p>
          </div>
        </div>

      </div>
    </article>
  );
};

export default MovieCard;
