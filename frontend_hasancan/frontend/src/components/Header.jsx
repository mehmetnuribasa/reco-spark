import React from 'react';
import './Header.css';

const STATUS_CONFIG = {
  ok:       { label: 'API Çevrimiçi',     cls: 'status--ok' },
  degraded: { label: 'Model Yükleniyor',  cls: 'status--degraded' },
  error:    { label: 'API Çevrimdışı',    cls: 'status--error' },
  checking: { label: 'Bağlanıyor...',     cls: 'status--checking' },
};

const Header = ({ healthStatus }) => {
  const cfg = STATUS_CONFIG[healthStatus] ?? STATUS_CONFIG.checking;

  return (
    <header className="header">
      <div className="header__inner">
        <div className="header__brand">
          <div className="header__logo">RS</div>
          <div className="header__text">
            <h1 className="header__title">Reco-Spark</h1>
            <p className="header__subtitle">Kişiselleştirilmiş Film Öneri Motoru</p>
          </div>
        </div>

        <nav className="header__nav">
          <span className="header__tech-badge">Apache Spark</span>
          <span className="header__tech-badge">ALS</span>
          <span className="header__tech-badge">FastAPI</span>
        </nav>

        <div className={`header__status ${cfg.cls}`}>
          <span className="header__dot" />
          <span>{cfg.label}</span>
        </div>
      </div>
    </header>
  );
};

export default Header;
