import React from 'react';
import './StatsBar.css';

const GridIcon = () => (
  <span className="view-icon" aria-hidden="true">
    <span /><span /><span /><span />
  </span>
);

const ListIcon = () => (
  <span className="view-icon view-icon--list" aria-hidden="true">
    <span /><span /><span />
  </span>
);

const StatsBar = ({ count, userId, avgRating, viewMode, onViewModeChange, onClear }) => (
  <div className="stats" role="status">
    <div className="stats__info">
      <span className="stats__badge">{count}</span>
      <span className="stats__text">
        film önerisi &nbsp;·&nbsp; Kullanıcı <strong>#{userId}</strong>
        {avgRating != null && (
          <span className="stats__avg">
            &nbsp;·&nbsp; Ort.&nbsp;
            <strong className="stats__avg-val">★ {avgRating}</strong>
          </span>
        )}
      </span>
    </div>

    <div className="stats__actions">
      <div className="stats__view-toggle" role="group" aria-label="Görünüm modu">
        <button
          type="button"
          className={`stats__view-btn ${viewMode === 'grid' ? 'stats__view-btn--active' : ''}`}
          onClick={() => onViewModeChange('grid')}
          title="Kart görünümü"
          aria-pressed={viewMode === 'grid'}
        >
          <GridIcon />
        </button>
        <button
          type="button"
          className={`stats__view-btn ${viewMode === 'list' ? 'stats__view-btn--active' : ''}`}
          onClick={() => onViewModeChange('list')}
          title="Liste görünümü"
          aria-pressed={viewMode === 'list'}
        >
          <ListIcon />
        </button>
      </div>

      <button className="stats__clear" onClick={onClear} title="Sonuçları temizle">
        Temizle
      </button>
    </div>
  </div>
);

export default StatsBar;
