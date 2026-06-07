import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = () => (
  <div className="spinner-wrap" role="status" aria-live="polite" aria-label="Yükleniyor">
    <div className="spinner">
      <div className="spinner__ring spinner__ring--outer" />
      <div className="spinner__ring spinner__ring--inner" />
      <span className="spinner__icon" aria-hidden="true">ALS</span>
    </div>
    <p className="spinner__label">Öneriler hesaplanıyor...</p>
    <p className="spinner__sub">ALS modeli çalışıyor · Lütfen bekleyin</p>

    <div className="spinner__steps">
      <span className="spinner__step spinner__step--done">Kullanıcı vektörü hazır</span>
      <span className="spinner__step spinner__step--active">Matris çarpımı yapılıyor</span>
      <span className="spinner__step">Top-N seçiliyor</span>
    </div>
  </div>
);

export default LoadingSpinner;
