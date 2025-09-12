# eBanguka Data Ingestion with Apache Airflow

This setup provides an Apache Airflow pipeline to automatically sync data from the eBanguka API to your PostgreSQL database every minute.

## Project Structure
```
eBanguka/
├── dags/
│   └── ebanguka_data_ingestion_dag.py    # Main Airflow DAG
├── scripts/
│   └── airflow-entrypoint.sh             # Docker entrypoint script
├── logs/                                 # Airflow logs directory
├── plugins/                              # Airflow plugins directory
├── docker-compose.yml                    # Docker compose configuration
├── Dockerfile                            # Custom Airflow image
├── requirements.txt                      # Python dependencies
├── data-ingestion.py                     # Original pipeline script
└── README_AIRFLOW.md                     # This file
```

## Features
- **Automated scheduling**: Runs every minute
- **Error handling**: Built-in retries and logging
- **Data validation**: Converts complex JSON objects to strings
- **Schema management**: Automatically creates emergency schema
- **Monitoring**: Web UI at http://localhost:8080
- **Scalable**: Uses Celery executor with Redis broker

## Prerequisites
1. Docker and Docker Compose installed
2. PostgreSQL running on localhost:5432 with:
   - Database: `greenriver`
   - Username: `postgres` 
   - Password: `rv!@07842`

## Quick Start

1. **Start the Airflow services**:
   ```bash
   cd /Users/nhiclap001/Desktop/NHIC/eBanguka
   docker-compose up -d
   ```

2. **Access the Airflow UI**:
   - URL: http://localhost:8080
   - Username: `admin`
   - Password: `admin`

3. **Enable the DAG**:
   - In the Airflow UI, find the `ebanguka_data_ingestion` DAG
   - Toggle the switch to enable it
   - The pipeline will start running every minute

## Services Overview

| Service | Port | Description |
|---------|------|-------------|
| Airflow Webserver | 8080 | Main UI for managing DAGs |
| Airflow Database | 5433 | PostgreSQL for Airflow metadata |
| Flower (Worker Monitor) | 5555 | Monitor Celery workers |

## DAG Details

**DAG Name**: `ebanguka_data_ingestion`
**Schedule**: Every minute (`timedelta(minutes=1)`)
**Tasks**:
1. `fetch_data` - Retrieves data from eBanguka API
2. `process_and_store_data` - Processes and stores data in PostgreSQL
3. `log_completion` - Logs successful completion

## Configuration

### Database Connection
The DAG is configured to connect to your existing PostgreSQL setup:
- Host: localhost
- Port: 5432
- Database: greenriver
- Schema: emergency
- Table: ebanguka

### API Endpoint
- URL: `https://ebanguka.moh.gov.rw/api/exposed/transfers`
- SSL verification: Disabled (as per original script)
- Timeout: 30 seconds

## Monitoring and Logs

1. **Airflow UI**: View DAG runs, task statuses, and logs at http://localhost:8080
2. **Flower UI**: Monitor Celery workers at http://localhost:5555
3. **Log Files**: Available in the `./logs` directory

## Troubleshooting

### Common Issues

1. **Port conflicts**:
   ```bash
   # Check if ports are in use
   lsof -i :8080
   lsof -i :5433
   ```

2. **Database connection issues**:
   - Ensure your PostgreSQL is running on localhost:5432
   - Verify credentials in the DAG file

3. **Docker issues**:
   ```bash
   # Restart services
   docker-compose down
   docker-compose up -d
   
   # Check logs
   docker-compose logs airflow-webserver
   docker-compose logs airflow-scheduler
   ```

4. **DAG not appearing**:
   - Check the `dags/` folder is mounted correctly
   - Look for Python syntax errors in the DAG file
   - Check Airflow scheduler logs

### Updating the Pipeline

To modify the pipeline:
1. Edit `dags/ebanguka_data_ingestion_dag.py`
2. The changes will be automatically picked up (may take 1-2 minutes)
3. Check the Airflow UI for any parsing errors

## Stopping the Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (careful - this removes data)
docker-compose down -v
```

## Performance Considerations

- **Frequency**: Currently set to run every minute. Adjust `schedule_interval` in the DAG if needed
- **Overlap prevention**: `max_active_runs=1` prevents overlapping executions
- **Resource usage**: Monitor system resources, especially with minute-level scheduling

## Security Notes

- Default Airflow credentials are `admin/admin` - change these in production
- Database credentials are hardcoded in the DAG - consider using Airflow Variables or Connections for production
- SSL verification is disabled for the eBanguka API - ensure this is acceptable for your use case