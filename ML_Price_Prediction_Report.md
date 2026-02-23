# Project Report: Mobile Phone Price Prediction in Sri Lanka

## Contents
1. [Problem Definition & Dataset Collection](#1-problem-definition--dataset-collection)
   1.1 [Problem Definition](#11-problem-definition)
   1.2 [Dataset Collection](#12-dataset-collection)
   1.3 [Features and Target Variable](#13-features-and-target-variable)
   1.4 [Data Preprocessing](#14-data-preprocessing)
2. [Selection of a Machine Learning Algorithm](#2-selection-of-a-machine-learning-algorithm)
   2.1 [Algorithm Selected: HistGradientBoostingRegressor](#21-algorithm-selected-histgradientboostingregressor)
   2.2 [Comparison to Standard Models](#22-comparison-to-standard-models)
3. [Model Training and Evaluation](#3-model-training-and-evaluation)
   3.1 [Train/Validation/Test Split](#31-trainvalidationtest-split)
   3.2 [Hyperparameter Configuration](#32-hyperparameter-configuration)
   3.3 [Performance Metrics & Results](#33-performance-metrics--results)
4. [Explainability & Interpretation](#4-explainability--interpretation)
   4.1 [Explainability Method: Permutation Importance](#41-explainability-method-permutation-importance)
   4.2 [Alignment with Domain Knowledge](#42-alignment-with-domain-knowledge)
5. [Critical Discussion](#5-critical-discussion)
   5.1 [Limitations & Data Quality Issues](#51-limitations--data-quality-issues)
   5.2 [Real-World Impact, Bias, and Ethics](#52-real-world-impact-bias-and-ethics)
6. [Front-End Integration](#6-front-end-integration)

---

## 1. Problem Definition & Dataset Collection

### 1.1 Problem Definition
The secondary market for mobile phones in Sri Lanka is highly fragmented and volatile. Consumers and small-scale resellers often struggle to determine a "fair" market price for used or brand-new devices due to rapid currency fluctuations, brand prestige, and varying technical specifications. This project addresses the need for a data-driven price estimation tool that provides transparency and benchmarks for the local mobile phone market.

### 1.2 Dataset Collection
*   **Data Sources**: The primary dataset was scraped from two major Sri Lankan sources:
    *   **Ikman.lk**: The largest marketplace in Sri Lanka for used and new electronics.
    *   **Francium.lk**: A specialized tech retailer providing high-fidelity pricing for premium Apple products.
*   **Collection Method**: A custom Python web scraper was developed using the `requests` and `BeautifulSoup` libraries. The scraper implemented robust features such as:
    *   **Incremental Saving**: To prevent data loss during long runs.
    *   **Error Handling**: Automatic retries for network instability.
    *   **Rate Limiting**: A 1.5-second delay to comply with ethical scraping practices and `robots.txt` policies.
*   **Dataset Size**: After merging and cleaning, the final dataset contains **6,530 unique listing records**.
*   **Ethical Data Use**: Only publicly available listing data (Title, Specs, Price) was collected. Personal seller information was explicitly excluded to ensure full privacy and ethical compliance.

### 1.3 Features and Target Variable
The dataset consists of **7 features** and **1 target variable**:
*   **Target Variable**: `Total price (LKR)` (The market price of the device).
*   **Categorical Features**:
    *   `Brand`: (e.g., Apple, Samsung, Xiaomi)
    *   `Operating system`: (iOS, Android, Other)
    *   `Warranty`: (Yes, Unknown)
    *   `Condition`: (Used, Brand New) - *Extracted from title*
    *   **`Connectivity`**: (4G, 5G) - *Extracted from title*
*   **Numerical Features**:
    *   `RAM_GB`: (Numeric capacity in GB)
    *   `Storage_GB`: (Numeric capacity in GB)

### 1.4 Data Preprocessing
1.  **Standardization**: Converted all storage units (TB/GB) to a uniform GB scale.
2.  **Cleaning**: Cleaned price strings by removing "Rs.", commas, and whitespace, converting them to floating-point numbers.
3.  **Extraction**: Utilized Regular Expressions (Regex) to extract technical specs (Condition, Connectivity, RAM) directly from unstructured product titles where available.
4.  **Deduplication**: Removed exact duplicate listings based on the unique Product URL as well as Title+Price combinations to ensure data integrity.
5.  **Imputation**: Applied 'unknown' labels to missing categorical fields to retain maximum data volume for the model.

---

## 2. Selection of a Machine Learning Algorithm

### 2.1 Algorithm Selected: HistGradientBoostingRegressor
We selected the `HistGradientBoostingRegressor` from the Scikit-Learn library.

**Justification for Selection:**
*   **Efficiency on Large Data**: It is significantly faster than standard Gradient Boosting when dealing with thousands of samples because it bins continuous values into discrete integer-based histograms.
*   **Handling Categorical Data**: It provides native, high-performance support for categorical features without requiring memory-intensive One-Hot Encoding.
*   **Robustness to Missing Values**: It can handle `NaN` values during training and inference without requiring complex imputation.
*   **Memory Efficiency**: Because of the environment's limited disk space, this model was chosen as a state-of-the-art GBDT (Gradient Boosting Decision Tree) that is part of the standard Scikit-Learn installation.

### 2.2 Comparison to Standard Models
*   **vs. Linear Regression**: Linear regression fails to capture the non-linear price drops (e.g., the massive price difference between an "iPhone" vs "Other" brands regardless of RAM).
*   **vs. Random Forest**: Random Forest builds trees independently (bagging). `HistGradientBoosting` builds them sequentially (boosting), focusing on correcting the errors of the previous trees, which typically leads to lower error rates on price prediction.
*   **vs. k-NN**: k-NN is extremely sensitive to feature scaling and becomes very slow as the dataset grows to 6,000+ records.
*   **vs. Decision Trees**: A single tree is prone to overfitting. Our boosting model combines 1,000 trees to achieve a much more stable and accurate prediction.

---

## 3. Model Training and Evaluation

### 3.1 Train/Validation/Test Split
*   **Split Ratio**: 80% Training (5,222 records) / 10% Validation (653 records) / 10% Testing (653 records).
*   **Randomization**: `random_state=42` was used to ensure the results are reproducible across runs.

### 3.2 Hyperparameter Configuration
*   `max_iter=1000`: Set a high limit for the number of boosting rounds.
*   `learning_rate=0.05`: Used a small step size to prevent the model from overfitting to noisy outlier listings.
*   `max_depth=6`: Balanced depth to capture complex spec interactions (like 5G + Apple + 256GB).
*   `early_stopping=True`: Automatically stopped training when the validation score stopped improving to ensure the best generalization.

### 3.3 Performance Metrics & Results
*   **R² Score**: **0.5623**
*   **RMSE**: LKR 57,415.53
*   **MAE**: LKR 38,464.03

**Interpretation**: The model successfully explains **56.23%** of the variance in mobile prices. Given that "Used" phone prices are highly subjective (influenced by physical scratches or battery health which we cannot see), an R² over 0.50 is considered strong for this type of secondary market data. The MAE of ~38k LKR means that on average, the model's estimate is within a reasonable range for high-end smartphones in the Sri Lankan context.

---

## 4. Explainability & Interpretation

### 4.1 Explainability Method: Permutation Importance
We used Permutation Importance on the test set to evaluate which features most impact the price.

**What the Model Has Learned:**
1.  **Brand Prestige**: The `Brand` feature holds the highest importance, confirming that Apple and Samsung flagships command a price premium regardless of other specs.
2.  **Condition Factor**: The model learned a massive distinction between 'Used' and 'Brand New' status, often several ten-thousand LKR in difference.
3.  **Storage Tiers**: `Storage_GB` was more influential than `RAM_GB`, reflecting the Sri Lankan market where 256GB vs 128GB iPhone models have very distinct price brackets.

### 4.2 Alignment with Domain Knowledge
The model behavior perfectly aligns with local market reality. Brand identity (Apple/Samsung) is the primary driver of value in Sri Lanka, followed closely by the phone's physical condition (New vs Used) and its connectivity (5G models are increasingly priced higher as the national network upgrades).

---

## 5. Critical Discussion

### 5.1 Limitations & Data Quality Issues
*   **Visual Condition**: The model cannot "see" the phone. Scratches, screen cracks, or battery health percentage (especially for iPhones) are critical factors that the scraper cannot extract from text.
*   **Seller Reliability**: "Ikman" prices can vary based on how quickly the seller wants to sell their item, introducing noise into the dataset.
*   **Model Accuracy**: An R² of 0.56 means there is still 44% of price variance that depends on factors not present in the technical specifications.

### 5.2 Real-World Impact, Bias, and Ethics
*   **Positive Impact**: Provides a "Market Standard" price for buyers and sellers, preventing them from being overcharged or under-selling their devices.
*   **Bias**: The dataset is biased toward "Colombo" listings as they represent the majority of online postings. Rural prices might differ due to lower availability.
*   **Ethics**: The tool is designed to be a "Price Advisor," not a "Price Dictator." It ensures transparency while acknowledging the limitations of machine learning in subjective markets.

---

## 6. Front-End Integration

To make this model useful for everyday users, we developed a fully functional Web Application.

*   **Technology Stack**: Python, **Flask** (Backend), HTML5/CSS3/JS (Frontend), `joblib` (Model persistence).
*   **Interactive Features**:
    *   **Input Validation**: Integrated dropdown menus to prevent invalid specs (negative values) and ensure compatibility with trained categories.
    *   **Market Insights**: The app does not just show a price; it calculates if the predicted price is "Above" or "Below" the typical market average for that brand.
    *   **Confidence levels**: Displays a "Moderate" confidence warning to ensure users understand the 56% R² context.
*   **User Interface**: A clean, mobile-responsive, single-page application that provides predictions instantly via an AJAX-powered Flask endpoint.
