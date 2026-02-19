# Crypto Arbitrage Stealth Engine

A high-frequency Real-Time ETL pipeline designed to monitor and visualize arbitrage opportunities across multiple cryptocurrency exchanges using **WebSockets**, **Redis**, and **Docker**.

![Dashboard Preview](assets/dashboard.png)

## System Architecture

The project follows a microservices architecture to ensure low latency and scalability:

```mermaid
graph TD
    subgraph External_Data_Sources
        B[Binance WebSocket]
        K[Kraken WebSocket]
    end

    subgraph Backend_Service[ETL Engine - Python 3.10]
        CCXT[CCXT Pro]
        PROC[Processing Logic]
    end

    subgraph Persistence_Layer[Message Broker]
        R[(Redis DB)]
    end

    subgraph Frontend_Service[Analytics Dashboard]
        ST[Streamlit App]
        ALT[Altair Engine]
    end

    B -->|WSS Stream| CCXT
    K -->|WSS Stream| CCXT
    CCXT --> PROC
    PROC -->|JSON Payload| R
    R <-->|Get/Set State| ST
    ST -->|Reactive Bind| ALT
```

1. **ETL Engine (Python/CCXT Pro)**: Connects to Binance and Kraken via WebSockets. It performs real-time data ingestion, calculates order book depth/imbalance, and pushes normalized data to Redis.
2. **Message Broker (Redis)**: Acts as an ultra-fast in-memory data store, serving as the "Single Source of Truth" for the frontend.
3. **Analytics Dashboard (Streamlit/Altair)**: A reactive web interface that performs complex analytics, including correlation matrices and market intelligence insights.

```mermaid
sequenceDiagram
    autonumber
    participant EX as Exchanges (Binance/Kraken)
    participant BE as Backend ETL
    participant DB as Redis Cache
    participant FE as Frontend Dashboard

    Note over EX,FE: Real-time Data Synchronization Loop
    EX->>BE: Order Book Update (WebSocket)
    BE->>BE: Compute Depth, Spread & Imbalance
    BE->>DB: SET ticker:exchange:symbol
    loop Every 1000ms
        FE->>DB: GET active symbols
        DB-->>FE: JSON Data
        FE->>FE: Update Master History DataFrame
        FE->>FE: Calculate Correlation & Trends
        FE->>FE: Re-render Altair Components
    end
```

## Tech Stack

- **Backend**: Python 3.10 (Asyncio)
- **Exchange Integration**: CCXT Pro (WebSockets)
- **Infrastructure**: Docker & Docker Compose
- **Database**: Redis (In-memory caching)
- **Visualization**: Streamlit & Altair (Declarative Statistical Visualization)

## Data Schema

```mermaid
classDiagram
    class TickerData {
        +String exchange
        +String symbol
        +Float bid
        +Float ask
        +Float bid_depth
        +Float ask_depth
        +Float latency
        +Int timestamp
    }

    class MasterHistory {
        +DateTime time
        +String symbol
        +Float spread
        +Float liquidity
        +Float latency
        +Float imbalance
        +Float net_profit
    }

    TickerData --|> MasterHistory : Transformation
```

## Advanced Features

```mermaid
graph LR
    User((Trader))
    
    subgraph Dashboard_Capabilities
        UC1(Monitor Real-time Spreads)
        UC2(Analyze Liquidity Flow)
        UC3(Assess Order Book Imbalance)
        UC4(Audit Network Latency)
        UC5(Calculate Net ROI)
        UC6(View Alert Logs)
    end

    User --- UC1
    User --- UC2
    User --- UC3
    User --- UC4
    User --- UC5
    User --- UC6
```

- **Market Intelligence Insights**: Real-time automated analysis of execution risk, network latency, and buying pressure.
- **Correlation Heatmap**: Dynamic matrix showing the price spread relationships between different assets.
- **Order Book Imbalance**: Visualizes Bid vs. Ask pressure to predict short-term price movements.
- **Analytics**:
  - **Live Spreads & Trends**: Real-time delta tracking with directional trend indicators (▲/▼).
  - **Liquidity Flow**: Multi-line tracking of market depth across all monitored symbols.
  - **Net Profit Calculator**: Instant calculation of ROI after exchange fees and investment size.
- **Alert Log**: Persistent session logging of every profitable arbitrage window detected.

## Getting Started

### Prerequisites

- Docker & Docker Compose installed.

### Installation

1. Clone the repository:

```bash
git clone [https://github.com/YOUR_USERNAME/Crypto-Arbitrage-Stealth.git](https://github.com/YOUR_USERNAME/Crypto-Arbitrage-Stealth.git)
cd Crypto-Arbitrage-Stealth
```

2. Launch the entire stack:

```bash
docker-compose up --build
```

3. Access the dashboard:
Open <http://localhost:8501> in your browser.
