# Reco-Spark

A movie recommendation system that uses Apache Spark for offline model training, FastAPI for backend serving, and React for the frontend interface.

## Project Overview

This project builds a recommender pipeline based on the MovieLens dataset. It includes:

- `ml_pipeline/`: PySpark code to preprocess data and train an ALS recommendation model.
- `backend/`: FastAPI application that loads the trained model and exposes recommendation APIs.
- `frontend/`: React-based web client to search movies, browse genres, and view personalized recommendations.

## Features

- Offline model training with Spark ALS
- REST API service for recommendations
- React frontend for movie discovery
- Uses MovieLens-style ratings and metadata

## Prerequisites

- Python 3.8+ for backend and training
- Node.js 14+ / npm for frontend
- Apache Spark installed or accessible in the Python environment

## Getting Started

### 1. Prepare the data

Place MovieLens dataset files under `data/` if they are not already present.

### 2. Train the model

Open a terminal in the project root and run:

```bash
cd ml_pipeline
python train.py
```

This will process the data and save the trained ALS model under `ml_pipeline/saved_model/als_model/`.

### 3. Run the backend

Open a terminal in `backend/` and install dependencies, then start the API server:

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The FastAPI server should start and expose recommendation endpoints.

### 4. Run the frontend

Open a terminal in `frontend/` and install Node dependencies, then start the React app:

```bash
cd frontend
npm install
npm start
```

Visit the local development URL shown in the terminal (usually `http://localhost:3000`).

## Notes

- Ensure the backend is running before using the frontend.
- If the backend requires a specific model path, verify the configuration in `backend/main.py`.
- The data files in `data/` should match the expected MovieLens format.
