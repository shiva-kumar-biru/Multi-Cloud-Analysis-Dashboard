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

## 🖥️ Usage Instructions
When you run the command above, the dashboard will open automatically in your default browser at http://localhost:5006/.

### Start Page
Upon loading, you will  see the start page, which provides an entry point into the analysis.

![startpage](https://github.com/shiva-kumar-biru/Multi-Cloud-Analysis-Dashboard/blob/main/images/start_page.png)

### Step-by-Step Workflow

1. Select a Cloud Provider:

-- Choose from AWS, Azure, or GCP.

-- Once the provider is selected, a list of available regions for that provider is displayed.

![awsregion](https://github.com/shiva-kumar-biru/Multi-Cloud-Analysis-Dashboard/blob/main/images/aws_regions.png)

2. Select the region you wish to analyze.

3. Enter Hardware Requirements:

-- Input your desired RAM (in GB) and CPU (vCPUs).

4. Get Matching VM Types:

-- Based on your input, the dashboard fetches a list of available VM types that match the specifications in the selected region.

5. Select a VM Type:

-- Choose the preferred VM type from the dropdown.

6. Choose a Pricing Model:

-- You’ll be presented with the available pricing models based on your provider and VM selection.

-- Options include On-Demand, Reserved, Spot, etc.

7. View Pricing Details:

-- Clicking on a pricing model will show:

a. Hourly Rate

b. Estimate

c. Upfront Costs (if applicable)

8. Multi-Select Pricing Models:

-- You can select multiple pricing models to compare them simultaneously.

![awspricing](https://github.com/shiva-kumar-biru/Multi-Cloud-Analysis-Dashboard/blob/main/images/aws_pricing.png)

9. Compare in Bar Chart:

-- select the options from the pricing models (multiselect)
-- Click the "Compare" button to view a bar chart comparison of selected pricing models.

![awsbarchart](https://github.com/shiva-kumar-biru/Multi-Cloud-Analysis-Dashboard/blob/main/images/aws_barchart.png)








