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

- **Select a Cloud Provider**  
  ◦ Choose from **AWS**, **Azure**, or **GCP**.  
  ◦ Once the provider is selected, a list of available regions for that provider is displayed.

![awsregion](https://github.com/shiva-kumar-biru/Multi-Cloud-Analysis-Dashboard/blob/main/images/aws_regions.png)

- **Select the Region**  
  ◦ Choose the region you wish to analyze.

- **Enter Hardware Requirements**  
  ◦ Input your desired **RAM (in GB)** and **CPU (vCPUs)**.

- **Get Matching VM Types**  
  ◦ Based on your input, the dashboard fetches a list of available VM types that match the specifications in the selected region.

- **Select a VM Type**  
  ◦ Choose the preferred VM type from the dropdown.

- **Choose a Pricing Model**  
  ◦ You’ll be presented with the available pricing models based on your provider and VM selection.  
  ◦ Options include:
    - On-Demand  
    - Reserved  
    - Spot  

- **View Pricing Details**  
  ◦ Clicking on a pricing model will show:
    - Hourly Rate  
    - Monthly Estimate  
    - Upfront Costs (if applicable)

- **Multi-Select Pricing Models**  
  ◦ You can select multiple pricing models to compare them simultaneously.


![awspricing](https://github.com/shiva-kumar-biru/Multi-Cloud-Analysis-Dashboard/blob/main/images/aws_pricing.png)

- **Compare in Bar Chart**  

  ◦ select the options from the pricing models (multiselect)
  
  ◦ Click the "Compare" button to view a bar chart comparison of selected pricing models.

![awsbarchart](https://github.com/shiva-kumar-biru/Multi-Cloud-Analysis-Dashboard/blob/main/images/aws_barchart.png)


## 🔁 Cross-Cloud Pricing Model Comparison

The dashboard also supports comparing the **same pricing model across multiple cloud providers** — for example, comparing **On-Demand pricing** between AWS, Azure, and GCP.

This feature is useful for identifying the most **cost-effective option** for your infrastructure needs across providers.

---

### 📌 How to Compare Pricing Models Across Cloud Providers

1. **Choose Your First Cloud Provider**  
   - Select **AWS**, **Azure**, or **GCP** from the cloud provider dropdown.

2. **Select a Region**  
   - Choose a region where the provider offers virtual machines.

3. **Enter Your Hardware Requirements**  
   - Provide values for **RAM (GB)** and **CPU (vCPUs)**.  
   - This filters VM types based on your configuration.

4. **Select a VM Type**  
   - Pick one of the matching VM types suggested by the dashboard.

5. **Select All Pricing Models and Click Compare Button**  
   - This saves all available pricing models prices for the selected VM **in the background** for this provider.

6. **Repeat for Other Cloud Providers**  
   - Switch to another provider (e.g., from AWS to Azure) and repeat steps 2 to 5:  
     ◦ Select region → RAM/CPU → VM type → Select all pricing models → Click Compare.

---

### 📊 View Cross-Cloud Comparison

Once pricing data for the same model (e.g., On-Demand) is gathered across providers:

1. **Select the pricing model** from the radio buttons or comparison selector.
2. The dashboard will display a **bar chart** comparing the selected model's cost across all three providers.

---

### 💡 Example

To compare **On-Demand pricing** across AWS, Azure, and GCP:

- **AWS** → region → RAM/CPU → VM type → Select all pricing models → Click Compare  
- **Azure** → same steps  
- **GCP** → same steps  
- Then choose **"On-Demand"** from the radio buttons to view a bar chart comparison.

![Multi-Cloud Comparison](https://github.com/shiva-kumar-biru/Multi-Cloud-Analysis-Dashboard/blob/main/images/multi%20cloud.png)

---

## 🗃️ File Structure

```

Multi-Cloud-Analysis-Dashboard/
├── images/ # Contains UI and chart images
├── src/ # Python source files for each cloud provider
│ ├── aws_pricing.py
│ ├── azure_pricing.py
│ ├── gcp_pricing.py
│ └── multi-cloud-analysis-dashboard.py
├── requirements.txt # Python dependencies
├── README.md # Project documentation
└── .gitignore # Files to be ignored by Git

```



