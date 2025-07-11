# Multi-Cloud-Analysis-Dashboard

## Overview

The **Cloud Cost Analysis Dashboard** is a dynamic, web-based GUI developed in Python using the open-source [Panel](https://panel.holoviz.org/) library. It enables users to perform interactive multi-cloud pricing comparisons,across AWS, Azure, and GCP. This tool simplifies complex cloud pricing analysis by providing real-time access to instance configurations, pricing models, and region-specific cost summaries—all within a unified interface.


## 🔧 Features

- 🌐 **Multi-Cloud Support**: AWS, Azure, and GCP

- 💰 **Pricing Models**:
  - **AWS**: On-Demand, Reserved (RI), Spot
  - **Azure**: Pay-As-You-Go, Reserved(RI),Spot
  - **GCP**: On-Demand, Preemptible (Spot), Committed Use Discounts (CUD)
- 📊 **Interactive Visualization**:
  - Cost comparison using Bokeh bar charts
  - Detailed pricing breakdowns (hourly, monthly, upfront)
- 🔄 **Real-Time API Integration**:
  - Uses official cloud provider SDKs and APIs


## 📦 Tech Stack

| Component        | Technology        |
|------------------|------------------|
| Frontend         | Panel (HoloViz)  |
| Backend/API Calls| Boto3, Azure SDK, Google API Client |
| Visualization    | Bokeh            |
| Language         | Python           |


## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/shiva-kumar-biru/Multi-Cloud-Analysis-Dashboard.git
```
```bash
cd Multi-Cloud-Analysis-Dashboard
```

### 2.Create and Activate a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # For Linux/macOS
venv\Scripts\activate     # For Windows
```

### 3.Install Dependencies

```bash
pip install -r requirements.txt
```

### 4.Run the Dashboard

```bash
panel serve multi-cloud-analysis-dashboard.py --show --autoreload
```
