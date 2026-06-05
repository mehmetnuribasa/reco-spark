import React from 'react';

const STAR_COUNT = 5;

function StarRating({ rating }) {
  const filled = Math.round((rating / 5) * STAR_COUNT);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '8px' }}>
      {Array.from({ length: STAR_COUNT }).map((_, i) => (
        <span
          key={i}
          style={{
            fontSize: '14px',
            color: i < filled ? '#f5c518' : '#444',
            textShadow: i < filled ? '0 0 6px #f5c51880' : 'none',
            transition: 'color 0.2s',
          }}
        >
          ★
        </span>
      ))}
      <span style={{ fontSize: '12px', color: '#aaa', marginLeft: '4px' }}>
        {rating.toFixed(2)} / 5.0
      </span>
    </div>
  );
}

function GenrePill({ genre }) {
  return (
    <span
      style={{
        fontSize: '10px',
        fontWeight: 600,
        letterSpacing: '0.05em',
        textTransform: 'uppercase',
        padding: '2px 8px',
        borderRadius: '999px',
        background: 'rgba(99,102,241,0.18)',
        color: '#a5b4fc',
        border: '1px solid rgba(99,102,241,0.3)',
        whiteSpace: 'nowrap',
      }}
    >
      {genre}
    </span>
  );
}

export default function MovieCard({ movie }) {
  const { title, genres, predictedRating } = movie;
  const genreList = genres === '(no genres listed)'
    ? ['Uncategorized']
    : genres.split('|');

  // Extract year from title if present
  const yearMatch = title.match(/\((\d{4})\)$/);
  const year = yearMatch ? yearMatch[1] : null;
  const cleanTitle = title.replace(/\s*\(\d{4}\)$/, '');

  return (
    <div
      style={{
        width: '200px',
        minHeight: '220px',
        background: 'linear-gradient(145deg, #1e1e2e 0%, #181825 100%)',
        border: '1px solid rgba(99,102,241,0.2)',
        borderRadius: '16px',
        padding: '18px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        boxShadow: '0 4px 24px rgba(0,0,0,0.4)',
        transition: 'transform 0.2s, box-shadow 0.2s, border-color 0.2s',
        cursor: 'default',
        position: 'relative',
        overflow: 'hidden',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.transform = 'translateY(-4px)';
        e.currentTarget.style.boxShadow = '0 12px 32px rgba(99,102,241,0.25)';
        e.currentTarget.style.borderColor = 'rgba(99,102,241,0.5)';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = '0 4px 24px rgba(0,0,0,0.4)';
        e.currentTarget.style.borderColor = 'rgba(99,102,241,0.2)';
      }}
    >
      {/* Decorative top gradient bar */}
      <div style={{
        position: 'absolute',
        top: 0, left: 0, right: 0,
        height: '3px',
        background: 'linear-gradient(90deg, #6366f1, #a855f7, #ec4899)',
        borderRadius: '16px 16px 0 0',
      }} />

      {/* Year badge */}
      {year && (
        <span style={{
          position: 'absolute',
          top: '14px',
          right: '14px',
          fontSize: '10px',
          color: '#6366f1',
          fontWeight: 700,
          letterSpacing: '0.08em',
        }}>
          {year}
        </span>
      )}

      {/* Title */}
      <div style={{
        fontFamily: "'Georgia', serif",
        fontSize: '15px',
        fontWeight: 700,
        color: '#e2e8f0',
        lineHeight: 1.35,
        paddingRight: year ? '32px' : '0',
        flex: 1,
      }}>
        {cleanTitle}
      </div>

      {/* Genres */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '4px',
      }}>
        {genreList.slice(0, 3).map(g => (
          <GenrePill key={g} genre={g} />
        ))}
        {genreList.length > 3 && (
          <span style={{ fontSize: '10px', color: '#555', alignSelf: 'center' }}>
            +{genreList.length - 3}
          </span>
        )}
      </div>

      {/* Rating */}
      <StarRating rating={predictedRating} />
    </div>
  );
}