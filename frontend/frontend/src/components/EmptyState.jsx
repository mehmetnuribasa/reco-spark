import React from 'react';
import './EmptyState.css';

const STATS = [
  { value: '25M+', label: 'Değerlendirme' },
  { value: '162K+', label: 'Kullanıcı' },
  { value: '62K+', label: 'Film' },
];

const EmptyState = ({ message }) => {
  if (message) {
    return (
      <div className="empty" role="alert">
        <div className="empty__not-found">
          <span className="empty__not-found-text">404</span>
        </div>
        <h3 className="empty__title">Öneri Bulunamadı</h3>
        <p className="empty__desc">{message}</p>
      </div>
    );
  }

  return (
    <div className="empty">
      <div className="empty__badge">
        <span className="empty__badge-text">ALS</span>
        <span className="empty__badge-sub">MovieLens 25M</span>
      </div>

      <h3 className="empty__title">Film Önerileri Bekleniyor</h3>
      <p className="empty__desc">
        Bir kullanıcı ID girerek Apache Spark ALS modeli ile
        kişiselleştirilmiş film önerileri alın.
      </p>

      <div className="empty__stats">
        {STATS.map((s) => (
          <div key={s.label} className="empty__stat">
            <span className="empty__stat-value">{s.value}</span>
            <span className="empty__stat-label">{s.label}</span>
          </div>
        ))}
      </div>

      <div className="empty__tech">
        <span className="empty__tech-item">PySpark MLlib</span>
        <span className="empty__tech-sep">·</span>
        <span className="empty__tech-item">ALS Collaborative Filtering</span>
        <span className="empty__tech-sep">·</span>
        <span className="empty__tech-item">FastAPI</span>
      </div>
    </div>
  );
};

export default EmptyState;
