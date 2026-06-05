import React from 'react';
import './GenreFilter.css';

const GenreFilter = ({ recommendations, activeGenre, onGenreChange }) => {
  const genreCounts = {};
  recommendations.forEach((movie) => {
    if (movie.genres && movie.genres !== '(no genres listed)') {
      movie.genres.split('|').forEach((g) => {
        genreCounts[g] = (genreCounts[g] || 0) + 1;
      });
    }
  });

  const genres = Object.entries(genreCounts).sort((a, b) => b[1] - a[1]);
  if (genres.length < 2) return null;

  return (
    <div className="genre-filter" role="group" aria-label="Türe göre filtrele">
      <span className="genre-filter__label">Tür:</span>
      <div className="genre-filter__chips">
        <button
          type="button"
          className={`genre-filter__chip ${!activeGenre ? 'genre-filter__chip--active' : ''}`}
          onClick={() => onGenreChange(null)}
        >
          Tümü
          <span className="genre-filter__count">{recommendations.length}</span>
        </button>

        {genres.map(([genre, count]) => (
          <button
            key={genre}
            type="button"
            className={`genre-filter__chip ${activeGenre === genre ? 'genre-filter__chip--active' : ''}`}
            onClick={() => onGenreChange(activeGenre === genre ? null : genre)}
          >
            {genre}
            <span className="genre-filter__count">{count}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default GenreFilter;
