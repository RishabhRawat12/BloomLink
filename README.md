# 🌸 BloomLink | Enterprise URL Management

BloomLink is a high-performance URL shortener built with **FastAPI**, **Redis**, and **MySQL**. It is designed to handle viral traffic spikes using advanced caching strategies.



## 🚀 Key Features
* **High-Speed Redirects**: Utilizing an in-memory **LRU Cache** and **Redis** for sub-millisecond response times.
* **Hot-Key Protection**: Automatically detects "viral" links and replicates them across multiple Redis nodes to prevent database bottlenecks.
* **Bloom Filter**: Optimized lookups that check if a link exists before querying the database, reducing unnecessary load.
* **Analytics Dashboard**: Real-time tracking of clicks, IP hashes (anonymized), and system resilience diagnostics.

## 🛠️ Tech Stack
* **Backend**: Python (FastAPI)
* **Database**: MySQL (SQLAlchemy ORM)
* **Cache**: Redis (Memurai)
* **Frontend**: HTML5, Jinja2 Templates, Tailwind-inspired CSS

## 🚦 Getting Started

### Prerequisites
1.  **MySQL**: Running via XAMPP or standalone (Port 3306).
2.  **Redis**: Memurai or Redis server (Port 6379).
3.  **Python 3.10+**

### Installation
1.  Clone the repository:
    ```bash
    git clone [https://github.com/your-username/URL-SHORTNER.git](https://github.com/your-username/URL-SHORTNER.git)
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the application:
    ```bash
    .\run.bat
    ```

## 📊 System Resilience
The system monitors traffic patterns. If a link crosses the **Hot-Key Threshold**, the analytics page will display active replication nodes, demonstrating the system's ability to scale under pressure.