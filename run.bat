@echo off
set DATABASE_URL=mysql+pymysql://root:Rishabh19@localhost:3306/bloomlink
set REDIS_HOST=localhost
uvicorn app.main:app --reload --port 8080