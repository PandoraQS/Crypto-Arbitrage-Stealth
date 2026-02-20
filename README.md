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
        News[RSS Crypto Feeds]
    end

    subgraph Persistence_Layer[Shared Message Broker]
        R[(Redis Shared DB)]
    end

    subgraph App_1_Arbitrage[Arbitrage Engine Stack]
        PROC[ETL Logic]
        ST_A[Arbitrage Dashboard]
    end

    subgraph App_2_Sentiment[Sentiment Alpha Stack]
        SENT[Sentiment ETL - FinBERT]
        ST_S[Intelligence Hub]
    end

    B & K --> PROC
    News --> SENT
    PROC & SENT -->|Write Tickers & News| R
    R <--> ST_A
    R <--> ST_S
    ST_S -->|LLM Context| Llama3[Ollama Engine]
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

## Networking & Multi-App Integration

This engine is designed to operate as a modular component within a larger trading ecosystem. It uses a shared external Docker network to communicate with the [Sentiment Alpha](https://github.com/PandoraQS/News-Sentiment-Alpha) project.

**Shared Network Configuration**
Both projects connect via a bridge network named crypto-bridge. This allows the Sentiment project to read real-time ticker data directly from this engine's Redis instance to calculate news-driven arbitrage impact.

**Key Docker Compose update:**

```bash
networks:
  crypto-bridge:
    external: true
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

1. Create the shared network:
Before launching the containers, you must create the external bridge network:

```bash
docker network create crypto-bridge
```

2. Clone and Launch:

```bash
git clone https://github.com/YOUR_USERNAME/Crypto-Arbitrage-Stealth.git
cd Crypto-Arbitrage-Stealth
docker-compose up --build
```

3. Access the dashboard:
Open <http://localhost:8501> in your browser.

4. Interoperability:
Once this engine is running, you can launch the Sentiment Alpha Dashboard on port `8502`: <http://localhost:8501>. It will automatically detect the Redis instance from this project and begin correlating news with your live spreads.
